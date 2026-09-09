"""Deprecated alias  -  use `androidlife.task_batch`."""
from androidlife import task_batch as _impl
import sys

sys.modules[__name__] = _impl
