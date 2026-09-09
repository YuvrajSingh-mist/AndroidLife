"""Deprecated alias  -  use `androidlife.task_dataset`."""
from androidlife import task_dataset as _impl
import sys

sys.modules[__name__] = _impl
