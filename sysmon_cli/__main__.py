"""Main entry point for running sysmon_cli as a module (`python -m sysmon_cli`)."""

import sys
from sysmon_cli.cli import main

if __name__ == "__main__":
    sys.exit(main())
