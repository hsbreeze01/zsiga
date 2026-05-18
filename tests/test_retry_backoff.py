import asyncio
import subprocess

import pytest

from zsiga.pipeline.utils import retry_sync, retry_with_backoff


# --- async retry_with_backoff tests ---


def test_first_attempt_success():
    """Successful call on first attempt — invoked exactly once."""
    call_count = 0

    async def ok():
        nonlocal call_count
        call_count += 1
        return "done"

    result = asyncio.run(retry_with_backoff(ok, max_attempts=3))
    assert result == "done"
    assert call_count == 1


def test_retry_then_success():
    """Retry on transient exception then succeed."""
    call_count = 0

    async def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("transient")
        return "ok"

    result = asyncio.run(retry_with_backoff(
        flaky, max_attempts=3, retry_on=(ConnectionError,),
        base_delay=0.01, jitter=False,
    ))
    assert result == "ok"
    assert call_count == 3


def test_exhaust_all_attempts():
    """Exhaust all attempts and raise last exception."""
    async def always_fail():
        raise ConnectionError("boom")

    with pytest.raises(ConnectionError, match="boom"):
        asyncio.run(retry_with_backoff(
            always_fail, max_attempts=3,
            retry_on=(ConnectionError,),
            base_delay=0.01, jitter=False,
        ))


def test_non_retryable_raises_immediately():
    """Non-retryable exception raises immediately without retry."""
    call_count = 0

    async def bad():
        nonlocal call_count
        call_count += 1
        raise ValueError("bad input")

    with pytest.raises(ValueError, match="bad input"):
        asyncio.run(retry_with_backoff(
            bad, max_attempts=3,
            retry_on=(ConnectionError, TimeoutError),
            base_delay=0.01,
        ))
    assert call_count == 1


def test_default_retry_on_all_exceptions():
    """Default retry_on=(Exception,) retries on any exception."""
    call_count = 0

    async def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RuntimeError("any")
        return "ok"

    result = asyncio.run(retry_with_backoff(
        flaky, max_attempts=3, base_delay=0.01, jitter=False,
    ))
    assert result == "ok"
    assert call_count == 2


# --- backoff timing tests ---


def test_backoff_timing_no_jitter():
    """Default backoff timing without jitter: 1.0, 2.0, 4.0."""
    delays = []
    call_count = 0

    async def _run():
        nonlocal call_count

        async def mock_sleep(delay):
            delays.append(delay)

        async def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("fail")
            return "done"

        import unittest.mock
        with unittest.mock.patch("asyncio.sleep", mock_sleep):
            return await retry_with_backoff(
                fail_twice, max_attempts=4,
                base_delay=1.0, max_delay=30.0, jitter=False,
                retry_on=(ConnectionError,),
            )

    result = asyncio.run(_run())
    assert result == "done"
    assert delays == [1.0, 2.0]


def test_max_delay_cap():
    """Delay capped at max_delay."""
    delays = []
    call_count = 0

    async def _run():
        nonlocal call_count

        async def mock_sleep(delay):
            delays.append(delay)

        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("fail")

        import unittest.mock
        with unittest.mock.patch("asyncio.sleep", mock_sleep):
            with pytest.raises(ConnectionError):
                await retry_with_backoff(
                    always_fail, max_attempts=6,
                    base_delay=1.0, max_delay=10.0, jitter=False,
                    retry_on=(ConnectionError,),
                )

    asyncio.run(_run())
    assert delays == [1.0, 2.0, 4.0, 8.0, 10.0]


def test_jitter_range():
    """Jitter randomizes delay within [raw_delay*0.5, raw_delay]."""
    delays = []
    call_count = 0

    async def _run():
        nonlocal call_count

        async def mock_sleep(delay):
            delays.append(delay)

        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("fail")

        import unittest.mock
        with unittest.mock.patch("asyncio.sleep", mock_sleep):
            with pytest.raises(ConnectionError):
                await retry_with_backoff(
                    always_fail, max_attempts=4,
                    base_delay=1.0, max_delay=30.0, jitter=True,
                    retry_on=(ConnectionError,),
                )

    asyncio.run(_run())
    for i, d in enumerate(delays):
        raw = 1.0 * (2 ** i)
        assert raw * 0.5 <= d <= raw


# --- logging tests ---


def test_retry_logging(capsys):
    """Each retry logs attempt number, exception type, and delay."""
    call_count = 0

    async def fail_then_ok():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("transient")
        return "done"

    asyncio.run(retry_with_backoff(
        fail_then_ok, max_attempts=3,
        retry_on=(ConnectionError,),
        base_delay=0.01, jitter=False,
    ))
    captured = capsys.readouterr()
    assert "[retry] attempt 1/3 failed (ConnectionError)" in captured.out
    assert "[retry] attempt 2/3 failed (ConnectionError)" in captured.out


# --- sync retry tests ---


def test_sync_retry_success_first_attempt():
    """Sync retry: success on first attempt."""
    call_count = 0

    def ok():
        nonlocal call_count
        call_count += 1
        return "done"

    result = retry_sync(ok, max_attempts=3)
    assert result == "done"
    assert call_count == 1


def test_sync_retry_then_success():
    """Sync retry on subprocess.TimeoutExpired then succeed."""
    call_count = 0

    def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise subprocess.TimeoutExpired(cmd="test", timeout=5)
        return "ok"

    result = retry_sync(
        flaky, max_attempts=2,
        retry_on=(subprocess.TimeoutExpired,),
        base_delay=0.01, jitter=False,
    )
    assert result == "ok"
    assert call_count == 2


def test_sync_retry_exhaust():
    """Sync retry: exhaust all attempts."""
    def always_fail():
        raise subprocess.TimeoutExpired(cmd="test", timeout=5)

    with pytest.raises(subprocess.TimeoutExpired):
        retry_sync(
            always_fail, max_attempts=2,
            retry_on=(subprocess.TimeoutExpired,),
            base_delay=0.01, jitter=False,
        )


def test_sync_non_retryable_raises_immediately():
    """Sync: non-retryable exception raises immediately."""
    call_count = 0

    def bad():
        nonlocal call_count
        call_count += 1
        raise ValueError("bad")

    with pytest.raises(ValueError):
        retry_sync(
            bad, max_attempts=3,
            retry_on=(subprocess.TimeoutExpired,),
            base_delay=0.01,
        )
    assert call_count == 1
