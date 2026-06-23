"""Engineering application cases for optical thin-film design.

All cases use TMM-only (no COMSOL dependency).
Each case includes: background, structure, design goals, metrics, and visualization.
"""

from .solar_cell_ar import run_solar_cell_ar
from .wdm_filter import run_wdm_filter
from .laser_mirror import run_laser_mirror
from .phone_lens_ar import run_phone_lens_ar
from .smart_window import run_smart_window

__all__ = [
    "run_solar_cell_ar",
    "run_wdm_filter",
    "run_laser_mirror",
    "run_phone_lens_ar",
    "run_smart_window",
]
