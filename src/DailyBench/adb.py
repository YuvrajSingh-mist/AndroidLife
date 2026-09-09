"""Deprecated alias  -  use `androidlife.adb`."""
from androidlife import adb as _impl
import sys

sys.modules[__name__] = _impl
