"""Tests for reflection phase calculation (Tamm analysis support)."""

from __future__ import annotations

import numpy as np
import pytest

from thinfilm.education import (
    LayerSpec,
    multilayer_rt_spectrum,
    phase_difference,
    reflection_phase_degrees,
    reflection_phase_radians,
    quarter_wave_thickness_nm,
)


LAMBDAS_NM = np.linspace(400, 800, 600)


def _single_layer_result():
    n = 1.38
    layers = [LayerSpec("L", n, quarter_wave_thickness_nm(550.0, n))]
    return multilayer_rt_spectrum(LAMBDAS_NM, layers, n_incident=1.0, n_substrate=1.52)


def _bragg_result():
    from thinfilm.education import build_high_reflector_layers
    layers = build_high_reflector_layers(550.0, n_high=2.30, n_low=1.46, periods=3)
    return multilayer_rt_spectrum(LAMBDAS_NM, layers, n_incident=1.0, n_substrate=1.52)


# ---------------------------------------------------------------------------
# 1. reflection_phase_radians
# ---------------------------------------------------------------------------

class TestReflectionPhaseRadians:
    def test_shape(self):
        result = _single_layer_result()
        phase = reflection_phase_radians(result)
        assert phase.shape == (600,)

    def test_dtype(self):
        result = _single_layer_result()
        phase = reflection_phase_radians(result)
        assert phase.dtype == np.float64

    def test_range_wrapped(self):
        result = _single_layer_result()
        phase = reflection_phase_radians(result, unwrap=False)
        assert np.all(phase >= -np.pi)
        assert np.all(phase <= np.pi)

    def test_unwrapped_continuous(self):
        result = _bragg_result()
        phase = reflection_phase_radians(result, unwrap=True)
        # Unwrapped phase should be monotonically varying (no jumps)
        dphase = np.diff(phase)
        # Max jump should be less than π (no wrapping)
        assert np.max(np.abs(dphase)) < np.pi

    def test_matches_angle(self):
        result = _single_layer_result()
        phase = reflection_phase_radians(result, unwrap=False)
        expected = np.angle(result["r_complex"])
        np.testing.assert_allclose(phase, expected, atol=1e-12)


# ---------------------------------------------------------------------------
# 2. reflection_phase_degrees
# ---------------------------------------------------------------------------

class TestReflectionPhaseDegrees:
    def test_shape(self):
        result = _single_layer_result()
        phase = reflection_phase_degrees(result)
        assert phase.shape == (600,)

    def test_conversion(self):
        result = _single_layer_result()
        rad = reflection_phase_radians(result, unwrap=False)
        deg = reflection_phase_degrees(result, unwrap=False)
        np.testing.assert_allclose(deg, np.degrees(rad), atol=1e-10)


# ---------------------------------------------------------------------------
# 3. phase_difference
# ---------------------------------------------------------------------------

class TestPhaseDifference:
    def test_same_structure_zero(self):
        result = _single_layer_result()
        delta = phase_difference(result, result)
        np.testing.assert_allclose(delta, 0.0, atol=1e-12)

    def test_different_structures(self):
        n1, n2 = 1.38, 1.46
        r1 = multilayer_rt_spectrum(
            LAMBDAS_NM,
            [LayerSpec("L", n1, quarter_wave_thickness_nm(550.0, n1))],
            n_incident=1.0, n_substrate=1.52,
        )
        r2 = multilayer_rt_spectrum(
            LAMBDAS_NM,
            [LayerSpec("L", n2, quarter_wave_thickness_nm(550.0, n2))],
            n_incident=1.0, n_substrate=1.52,
        )
        delta = phase_difference(r1, r2)
        assert delta.shape == (600,)
        # Different structures should give nonzero phase difference
        assert np.max(np.abs(delta)) > 0.01

    def test_wrapped_range(self):
        r1 = _single_layer_result()
        r2 = _bragg_result()
        delta = phase_difference(r1, r2, unwrap=False)
        assert np.all(delta >= -np.pi)
        assert np.all(delta <= np.pi)

    def test_unwrapped_smaller_magnitude(self):
        r1 = _single_layer_result()
        r2 = _bragg_result()
        delta_wrapped = np.abs(phase_difference(r1, r2, unwrap=False))
        delta_unwrapped = np.abs(phase_difference(r1, r2, unwrap=True))
        # Unwrapped difference should generally have smaller magnitude
        assert np.mean(delta_unwrapped) <= np.mean(delta_wrapped) + 0.1


# ---------------------------------------------------------------------------
# 4. Edge cases
# ---------------------------------------------------------------------------

class TestPhaseEdgeCases:
    def test_bare_interface(self):
        result = multilayer_rt_spectrum(
            LAMBDAS_NM, [], n_incident=1.0, n_substrate=1.52,
        )
        phase = reflection_phase_radians(result)
        # Bare interface: phase should be ~0 or ~π (real r)
        assert phase.shape == (600,)

    def test_single_wavelength(self):
        result = multilayer_rt_spectrum(
            [550.0], [], n_incident=1.0, n_substrate=1.52,
        )
        phase = reflection_phase_radians(result)
        assert phase.shape == (1,)

    def test_oblique_incidence(self):
        n = 1.38
        layers = [LayerSpec("L", n, quarter_wave_thickness_nm(550.0, n))]
        result = multilayer_rt_spectrum(
            LAMBDAS_NM, layers, n_incident=1.0, n_substrate=1.52,
            theta0_deg=45.0, pol="s",
        )
        phase = reflection_phase_radians(result)
        assert phase.shape == (600,)
