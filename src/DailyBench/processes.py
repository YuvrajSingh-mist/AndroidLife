"""Deprecated alias  -  use `androidlife.processes`."""
from androidlife import processes as _impl
import sys

sys.modules[__name__] = _impl
