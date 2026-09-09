"""Deprecated alias  -  use `androidlife.files`."""
from androidlife import files as _impl
import sys

sys.modules[__name__] = _impl
