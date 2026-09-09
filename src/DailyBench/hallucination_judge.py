"""Deprecated alias  -  use `androidlife.hallucination_judge`."""
from androidlife import hallucination_judge as _impl
import sys

sys.modules[__name__] = _impl
