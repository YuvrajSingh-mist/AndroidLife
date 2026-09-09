"""Deprecated alias  -  use `androidlife.benchmark_metrics`."""
from androidlife import benchmark_metrics as _impl
import sys

sys.modules[__name__] = _impl
