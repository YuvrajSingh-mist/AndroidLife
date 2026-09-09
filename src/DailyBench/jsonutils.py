"""Deprecated alias  -  use `androidlife.jsonutils`."""
from androidlife import jsonutils as _impl
import sys

sys.modules[__name__] = _impl
