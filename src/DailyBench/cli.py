"""Deprecated alias  -  use `androidlife.cli`."""
from androidlife import cli as _impl
import sys

sys.modules[__name__] = _impl
