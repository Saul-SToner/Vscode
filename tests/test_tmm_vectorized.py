"""Tests for TMM vectorization: verify vectorized matches scalar reference.

These tests use _multilayer_rt_spectrum_scalar as the oracle and assert
that the vectorized multilayer_rt_spectrum produces identical results.
"""

from __future__ import annotations

import numpy as np
import pytest

from thinfilm.education import (
    LayerSpec,
    _multilayer_rt_spectrum_scalar,
    build_high_reflector_layers,
    build_fp_single_halfwave_layers,
    multilayer_rt_spectrum,
    quarter_wave_thickness_nm,
)

LAMBDAS_NM = np.linspace(400, 800, 600)
LAMBDAS_SINGLE = np.array([550.0])


def _single_layer() -> list[LayerSpec]:
    n = 1.38
    return [LayerSpec("L", n, quarter_wave_thickness_nm(550.0, n))]


def _bragg_3period() -> list[LayerSpec]:
    return build_high_reflector_layers(550.0, n_high=2.30, n_low=1.46, periods=3)


def _fp_filter() -> list[LayerSpec]:
    return build_fp_single_halfwave_layers(550.0, n_high=2.30, n_low=1.46, periods=3)


class TestVectorizedMatchesScalar:
    """Direct comparison: vectorized == scalar for every output field."""

    @pytest.mark.parametrize("layers_fn,name", [
        (_single_layer, "single_layer"),
        (_bragg_3period, "bragg_3p"),
        (_fp_filter, "fp_filter"),
        (lambda: [], "bare_interface"),
    ])
    @pytest.mark.parametrize("pol", ["s", "p"])
    def test_600_points(self, layers_fn, name, pol):
        layers = layers_fn()
        ref = _multilayer_rt_spectrum_scalar(
            LAMBDAS_NM, layers, n_incident=1.0, n_substrate=1.52, pol=pol,
        )
        vec = multilayer_rt_spectrum(
            LAMBDAS_NM, layers, n_incident=1.0, n_substrate=1.52, pol=pol,
        )
        np.testing.assert_allclose(vec["R"], ref["R"], rtol=1e-12, atol=1e-14,
                                    err_msg=f"R mismatch for {name}/{pol}")
        np.testing.assert_allclose(vec["T"], ref["T"], rtol=1e-12, atol=1e-14,
                                    err_msg=f"T mismatch for {name}/{pol}")
        np.testing.assert_allclose(vec["A"], ref["A"], rtol=1e-12, atol=1e-14,
                                    err_msg=f"A mismatch for {name}/{pol}")

    def test_single_wavelength(self):
        ref = _multilayer_rt_spectrum_scalar(
            LAMBDAS_SINGLE, _bragg_3period(), n_incident=1.0, n_substrate=1.52,
        )
        vec = multilayer_rt_spectrum(
            LAMBDAS_SINGLE, _bragg_3period(), n_incident=1.0, n_substrate=1.52,
        )
        np.testing.assert_allclose(vec["R"], ref["R"], rtol=1e-12)
        np.testing.assert_allclose(vec["T"], ref["T"], rtol=1e-12)

    def test_oblique_45deg(self):
        ref = _multilayer_rt_spectrum_scalar(
            LAMBDAS_NM, _single_layer(), n_incident=1.0, n_substrate=1.52,
            theta0_deg=45.0, pol="s",
        )
        vec = multilayer_rt_spectrum(
            LAMBDAS_NM, _single_layer(), n_incident=1.0, n_substrate=1.52,
            theta0_deg=45.0, pol="s",
        )
        np.testing.assert_allclose(vec["R"], ref["R"], rtol=1e-12)
        np.testing.assert_allclose(vec["T"], ref["T"], rtol=1e-12)

    def test_many_layers_21(self):
        layers = build_high_reflector_layers(550.0, n_high=4.0, n_low=1.0, periods=10)
        ref = _multilayer_rt_spectrum_scalar(
            LAMBDAS_NM, layers, n_incident=1.0, n_substrate=1.5,
        )
        vec = multilayer_rt_spectrum(
            LAMBDAS_NM, layers, n_incident=1.0, n_substrate=1.5,
        )
        np.testing.assert_allclose(vec["R"], ref["R"], rtol=1e-12, atol=1e-14)

    def test_complex_r_and_t(self):
        ref = _multilayer_rt_spectrum_scalar(
            LAMBDAS_NM, _single_layer(), n_incident=1.0, n_substrate=1.52,
        )
        vec = multilayer_rt_spectrum(
            LAMBDAS_NM, _single_layer(), n_incident=1.0, n_substrate=1.52,
        )
        np.testing.assert_allclose(vec["r_complex"], ref["r_complex"], rtol=1e-12)
        np.testing.assert_allclose(vec["t_complex"], ref["t_complex"], rtol=1e-12)


class TestVectorizedPerformance:
    """Verify vectorized is faster than scalar."""

    def test_speedup_single_layer(self):
        layers = _single_layer()
        import time

        t0 = time.perf_counter()
        for _ in range(5):
            _multilayer_rt_spectrum_scalar(LAMBDAS_NM, layers, n_incident=1.0, n_substrate=1.52)
        scalar_time = (time.perf_counter() - t0) / 5

        t0 = time.perf_counter()
        for _ in range(5):
            multilayer_rt_spectrum(LAMBDAS_NM, layers, n_incident=1.0, n_substrate=1.52)
        vec_time = (time.perf_counter() - t0) / 5

        speedup = scalar_time / vec_time
        # Vectorized should be at least 3x faster for 600 points
        assert speedup > 3.0, f"Expected >3x speedup, got {speedup:.1f}x"

    def test_speedup_bragg(self):
        layers = _bragg_3period()
        import time

        t0 = time.perf_counter()
        for _ in range(3):
            _multilayer_rt_spectrum_scalar(LAMBDAS_NM, layers, n_incident=1.0, n_substrate=1.52)
        scalar_time = (time.perf_counter() - t0) / 3

        t0 = time.perf_counter()
        for _ in range(3):
            multilayer_rt_spectrum(LAMBDAS_NM, layers, n_incident=1.0, n_substrate=1.52)
        vec_time = (time.perf_counter() - t0) / 3

        speedup = scalar_time / vec_time
        assert speedup > 3.0, f"Expected >3x speedup, got {speedup:.1f}x"
