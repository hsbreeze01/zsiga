import asyncio
import sys
from .config import load_config
from .pipeline.orchestrator import ZsigaOrchestrator
from .metrics.dashboard import generate_dashboard


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "dashboard":
        path = generate_dashboard()
        print(f"Dashboard generated: {path}")
        return

    config = load_config()
    orchestrator = ZsigaOrchestrator(config)
    asyncio.run(orchestrator.run_cycle())


if __name__ == "__main__":
    main()
