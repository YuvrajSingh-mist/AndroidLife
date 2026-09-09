"""Deprecated alias  -  use `androidlife.summary`."""
from androidlife import summary as _impl
import sys

sys.modules[__name__] = _impl
