"""Deprecated alias  -  use `androidlife.pricing`."""
from androidlife import pricing as _impl
import sys

sys.modules[__name__] = _impl
