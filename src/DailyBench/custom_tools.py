"""Deprecated alias  -  use `androidlife.custom_tools`."""
from androidlife import custom_tools as _impl
import sys

sys.modules[__name__] = _impl
