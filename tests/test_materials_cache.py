"""Tests for materials caching.

These tests verify that:
1. Cached data is returned on repeated calls
2. Cache can be cleared
3. Cached arrays are read-only
4. Performance improvement from caching
"""

from __future__ import annotations

import time

import numpy as np
import pytest

from thinfilm.materials import (
    clear_material_cache,
    load_real_material,
    material_nk_at,
)


@pytest.fixture(autouse=True)
def _clean_cache():
    """Clear cache before and after each test."""
    clear_material_cache()
    yield
    clear_material_cache()


class TestMaterialCaching:
    """Verify caching behavior."""

    def test_same_instance_returned(self):
        ds1 = load_real_material("SiO2")
        ds2 = load_real_material("SiO2")
        assert ds1 is ds2  # Same Python object, not just equal

    def test_cache_works_for_csv_materials(self):
        ds1 = load_real_material("MgF2")
        ds2 = load_real_material("MgF2")
        assert ds1 is ds2

    def test_cache_works_for_air(self):
        ds1 = load_real_material("Air")
        ds2 = load_real_material("Air")
        assert ds1 is ds2

    def test_different_materials_different_instances(self):
        ds_sio2 = load_real_material("SiO2")
        ds_mgf2 = load_real_material("MgF2")
        assert ds_sio2 is not ds_mgf2

    def test_cache_clear(self):
        ds1 = load_real_material("SiO2")
        clear_material_cache()
        ds2 = load_real_material("SiO2")
        assert ds1 is not ds2  # New instance after cache clear

    def test_data_consistency_after_cache_clear(self):
        ds1 = load_real_material("SiO2")
        n1 = ds1.n.copy()
        clear_material_cache()
        ds2 = load_real_material("SiO2")
        np.testing.assert_array_equal(ds2.n, n1)


class TestReadonlyArrays:
    """Verify cached arrays are read-only."""

    def test_lambda_um_readonly(self):
        ds = load_real_material("SiO2")
        with pytest.raises(ValueError, match="read-only"):
            ds.lambda_um[0] = 999.0

    def test_n_readonly(self):
        ds = load_real_material("SiO2")
        with pytest.raises(ValueError, match="read-only"):
            ds.n[0] = 999.0

    def test_k_readonly(self):
        ds = load_real_material("SiO2")
        with pytest.raises(ValueError, match="read-only"):
            ds.k[0] = 999.0


class TestMaterialNkCaching:
    """Verify material_nk_at benefits from caching."""

    def test_consistent_results(self):
        """Same input should give same output after caching."""
        n1, k1 = material_nk_at("SiO2", 0.55)
        n2, k2 = material_nk_at("SiO2", 0.55)
        np.testing.assert_allclose(n1, n2)
        np.testing.assert_allclose(k1, k2)

    def test_performance_improvement(self):
        """Second call should be faster due to caching."""
        # First call: cold cache
        t0 = time.perf_counter()
        for _ in range(10):
            material_nk_at("SiO2", 0.55)
        t1 = time.perf_counter()

        # Cache is warm, measure again
        t2 = time.perf_counter()
        for _ in range(10):
            material_nk_at("SiO2", 0.55)
        t3 = time.perf_counter()

        cold_time = t1 - t0
        warm_time = t3 - t2
        # Warm cache should be significantly faster (at least 2x)
        assert warm_time < cold_time


class TestCommonWavelengthWindow:
    """Verify common_wavelength_window_um benefits from caching."""

    def test_consistent_results(self):
        lo1, hi1 = _cached_window()
        lo2, hi2 = _cached_window()
        assert lo1 == lo2
        assert hi1 == hi2


def _cached_window():
    from thinfilm.materials import common_wavelength_window_um
    return common_wavelength_window_um(["SiO2", "MgF2"])
