import asyncio
import sys
from .config import load_config
from .pipeline.orchestrator import ZsigaOrchestrator


def main():
    config = load_config()
    orchestrator = ZsigaOrchestrator(config)
    asyncio.run(orchestrator.run_cycle())


if __name__ == "__main__":
    main()
