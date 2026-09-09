"""Deprecated alias  -  use `androidlife.sampler`."""
from androidlife import sampler as _impl
import sys

sys.modules[__name__] = _impl
