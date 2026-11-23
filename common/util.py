import re
import sys
from typing import NoReturn


def fail(message: str) -> NoReturn:
    """Abort workflow generation with a message (gwf shows it on any command)."""
    print(message, file=sys.stderr)
    sys.exit(1)


def safe_name(value: str) -> str:
    """Make `value` usable inside a gwf target name.

    gwf only allows [a-zA-Z0-9._] after the first character, so anything else
    (e.g. '-' in sample IDs, '*' or ':' in HLA contig names) becomes '_'.
    """
    return re.sub(r"[^A-Za-z0-9._]", "_", value)
