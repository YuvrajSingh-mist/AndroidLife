"""Deprecated alias  -  use `androidlife.user_config`."""
from androidlife import user_config as _impl
import sys

sys.modules[__name__] = _impl
