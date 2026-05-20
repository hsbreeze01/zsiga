"""Phase Write-Ahead Log for crash recovery.

Persists the current pipeline phase state to a ``.phase_state`` file
inside the change directory at every phase boundary. The WAL is deleted
on successful DELIVER or on REVERT.
"""

import json
from datetime import datetime

from ..transport import Transport, LocalTransport
from .utils import read_file as _read_file


PHASE_STATE_FILENAME = ".phase_state"


class PhaseWAL:
    """Write-ahead log for pipeline phase state.

    Operates via transport so it works identically for local and SSH targets.
    """

    def __init__(self, change_dir: str, transport: Transport = None):
        self.change_dir = change_dir
        self.transport = transport or LocalTransport()
        self._path = f"{change_dir}/{PHASE_STATE_FILENAME}"

    # -- write -------------------------------------------------------------

    def write(self, phase: str, pre_sha: str = None,
              target_path: str = None, project: str = None) -> None:
        """Write (or overwrite) the ``.phase_state`` file."""
        data = {
            "current_phase": phase,
            "started_at": datetime.now().isoformat(),
        }
        if pre_sha is not None:
            data["pre_sha"] = pre_sha
        if target_path is not None:
            data["target_path"] = target_path
        if project is not None:
            data["project"] = project

        payload = json.dumps(data, ensure_ascii=False)
        escaped = payload.replace("'", "'\\''")
        self.transport.run_shell(
            f"echo '{escaped}' > '{self._path}'",
            timeout=10,
        )

    # -- read --------------------------------------------------------------

    def read(self) -> dict | None:
        """Read the ``.phase_state`` file.

        Returns a dict with keys ``current_phase``, ``started_at``,
        ``pre_sha``, ``target_path``, ``project`` — or ``None`` if the
        file does not exist.
        """
        content = _read_file(self._path, self.transport)
        if content is None:
            return None
        try:
            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return None

    # -- existence ---------------------------------------------------------

    def exists(self) -> bool:
        """Return ``True`` if the ``.phase_state`` file exists."""
        from .utils import file_exists
        return file_exists(self._path, self.transport)

    # -- delete ------------------------------------------------------------

    def delete(self) -> None:
        """Delete the ``.phase_state`` file (idempotent)."""
        self.transport.run_shell(
            f"rm -f '{self._path}'",
            timeout=5,
        )
