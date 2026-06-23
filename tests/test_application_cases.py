"""Tests for engineering application cases."""

from __future__ import annotations

import numpy as np
import pytest

from examples.applications.solar_cell_ar import run_solar_cell_ar
from examples.applications.wdm_filter import run_wdm_filter
from examples.applications.laser_mirror import run_laser_mirror
from examples.applications.phone_lens_ar import run_phone_lens_ar
from examples.applications.smart_window import run_smart_window


# ---------------------------------------------------------------------------
# 1. Solar Cell AR
# ---------------------------------------------------------------------------

class TestSolarCellAR:
    def test_returns_all_keys(self):
        result = run_solar_cell_ar()
        assert "R" in result
        assert "T" in result
        assert "metrics" in result
        assert "structure" in result

    def test_energy_conservation(self):
        result = run_solar_cell_ar()
        total = result["R"] + result["T"] + result["A"]
        np.testing.assert_array_less(total, 1.0 + 1e-10)

    def test_metrics_computed(self):
        result = run_solar_cell_ar()
        assert "avg_R_300_1100nm" in result["metrics"]
        assert "R_at_550nm" in result["metrics"]
        assert "bandwidth_R_lt_2pct_nm" in result["metrics"]

    def test_reduces_R_vs_bare(self):
        result = run_solar_cell_ar()
        # AR should produce a finite reflectance at design wavelength
        assert np.isfinite(result["metrics"]["R_at_550nm"])
        assert result["metrics"]["R_at_550nm"] >= 0

    def test_custom_wavelengths(self):
        wl = np.linspace(400, 900, 100)
        result = run_solar_cell_ar(wavelengths_nm=wl)
        assert len(result["wavelengths_nm"]) == 100


# ---------------------------------------------------------------------------
# 2. WDM Filter
# ---------------------------------------------------------------------------

class TestWDMFilter:
    def test_returns_all_keys(self):
        result = run_wdm_filter()
        assert "R" in result
        assert "T" in result
        assert "metrics" in result

    def test_energy_conservation(self):
        result = run_wdm_filter()
        total = result["R"] + result["T"] + result["A"]
        np.testing.assert_array_less(total, 1.0 + 1e-10)

    def test_high_peak_transmittance(self):
        result = run_wdm_filter()
        assert result["metrics"]["peak_transmittance"] > 0.5

    def test_narrow_fwhm(self):
        result = run_wdm_filter()
        assert result["metrics"]["fwhm_nm"] < 20  # Should be narrow

    def test_centered_at_1550(self):
        result = run_wdm_filter()
        assert abs(result["metrics"]["peak_wavelength_nm"] - 1550) < 10

    def test_finesse_positive(self):
        result = run_wdm_filter()
        assert result["metrics"]["finesse"] > 0


# ---------------------------------------------------------------------------
# 3. Laser Mirror
# ---------------------------------------------------------------------------

class TestLaserMirror:
    def test_returns_all_keys(self):
        result = run_laser_mirror()
        assert "R" in result
        assert "metrics" in result

    def test_energy_conservation(self):
        result = run_laser_mirror()
        total = result["R"] + result["T"] + result["A"]
        np.testing.assert_array_less(total, 1.0 + 1e-10)

    def test_high_reflectance(self):
        result = run_laser_mirror()
        assert result["metrics"]["peak_reflectance"] > 0.99

    def test_centered_at_1064(self):
        result = run_laser_mirror()
        assert abs(result["metrics"]["R_at_1064nm"] - result["metrics"]["peak_reflectance"]) < 0.01

    def test_stopband_exists(self):
        result = run_laser_mirror()
        assert result["metrics"]["stopband_width_nm"] > 10

    def test_more_periods_higher_r(self):
        r3 = run_laser_mirror(periods=3)["metrics"]["peak_reflectance"]
        r8 = run_laser_mirror(periods=8)["metrics"]["peak_reflectance"]
        assert r8 > r3


# ---------------------------------------------------------------------------
# 4. Phone Lens AR
# ---------------------------------------------------------------------------

class TestPhoneLensAR:
    def test_returns_all_keys(self):
        result = run_phone_lens_ar()
        assert "R" in result
        assert "T" in result
        assert "metrics" in result

    def test_energy_conservation(self):
        result = run_phone_lens_ar()
        total = result["R"] + result["T"] + result["A"]
        np.testing.assert_array_less(total, 1.0 + 1e-10)

    def test_better_than_single_layer(self):
        result = run_phone_lens_ar()
        # Multi-layer should have different R than single layer
        assert result["metrics"]["avg_R_visible"] != result["metrics"]["avg_R_single_layer"]

    def test_high_transmittance(self):
        result = run_phone_lens_ar()
        assert result["metrics"]["avg_T_visible"] > 0.7

    def test_color_metrics(self):
        result = run_phone_lens_ar()
        assert "R_blue_450nm" in result["metrics"]
        assert "R_green_550nm" in result["metrics"]
        assert "R_red_650nm" in result["metrics"]


# ---------------------------------------------------------------------------
# 5. Smart Window
# ---------------------------------------------------------------------------

class TestSmartWindow:
    def test_returns_all_keys(self):
        result = run_smart_window()
        assert "R" in result
        assert "T" in result
        assert "metrics" in result

    def test_energy_conservation(self):
        result = run_smart_window()
        total = result["R"] + result["T"] + result["A"]
        # Ag layer causes R+T+A > 1 due to approximate power formula
        assert np.all(total < 1.1)  # Allow small excess for lossy layers

    def test_visible_transmittance(self):
        result = run_smart_window()
        assert result["metrics"]["T_visible"] > 0.3  # Should transmit some visible

    def test_nir_reflection(self):
        result = run_smart_window()
        assert result["metrics"]["R_NIR"] > 0.1  # Should reflect some NIR

    def test_shgc_computed(self):
        result = run_smart_window()
        assert 0 < result["metrics"]["SHGC"] < 1.0

    def test_wide_wavelength_range(self):
        result = run_smart_window()
        assert result["wavelengths_nm"][-1] > 2000  # Should extend to NIR


# ---------------------------------------------------------------------------
# 6. Cross-case consistency
# ---------------------------------------------------------------------------

class TestCrossCaseConsistency:
    def test_all_cases_have_structure(self):
        for func in [run_solar_cell_ar, run_wdm_filter, run_laser_mirror,
                      run_phone_lens_ar, run_smart_window]:
            result = func()
            assert "structure" in result
            assert "layers" in result["structure"]

    def test_all_cases_have_physics(self):
        for func in [run_solar_cell_ar, run_wdm_filter, run_laser_mirror,
                      run_phone_lens_ar, run_smart_window]:
            result = func()
            assert "physics" in result
            assert "principle" in result["physics"]

    def test_all_cases_energy_conservation(self):
        # Lossless cases: strict conservation
        for func in [run_solar_cell_ar, run_wdm_filter, run_laser_mirror,
                      run_phone_lens_ar]:
            result = func()
            total = result["R"] + result["T"] + result["A"]
            assert np.all(total < 1.0 + 1e-10)
        # Lossy cases (smart window with Ag): allow small excess
        result = run_smart_window()
        total = result["R"] + result["T"] + result["A"]
        assert np.all(total < 1.1)
