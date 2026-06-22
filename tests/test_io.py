"""Tests for CSV I/O functions.

These tests verify the spectrum CSV loading and parsing pipeline.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from thinfilm.io import (
    SpectrumData,
    _extract_comment_lines,
    _guess_y_kind,
    _normalize_label,
    load_spectrum_csv,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _make_simple_csv(path: Path) -> None:
    """Two-column CSV: wavelength (nm) and reflectance."""
    content = """% wavelength_nm, R
400, 0.05
500, 0.03
600, 0.02
700, 0.04
800, 0.06
"""
    _write_csv(path, content)


def _make_comsol_csv(path: Path) -> None:
    """COMSOL-style numeric table with comment header."""
    content = """% lambda (nm), R(1)
400, 0.05
500, 0.03
600, 0.02
700, 0.04
800, 0.06
"""
    _write_csv(path, content)


def _make_three_column_csv(path: Path) -> None:
    """Three-column CSV: wavelength, R, T."""
    content = """% lambda_nm, reflectance, transmittance
400, 0.05, 0.93
500, 0.03, 0.95
600, 0.02, 0.96
700, 0.04, 0.94
800, 0.06, 0.92
"""
    _write_csv(path, content)


def _make_no_header_csv(path: Path) -> None:
    """CSV with no headers, pure numeric."""
    content = """400, 0.05
500, 0.03
600, 0.02
700, 0.04
800, 0.06
"""
    _write_csv(path, content)


# ---------------------------------------------------------------------------
# 1. Comment line extraction
# ---------------------------------------------------------------------------

class TestCommentExtraction:
    def test_extracts_percent_lines(self):
        lines = ["% header1", "data", "% header2"]
        result = _extract_comment_lines(lines)
        assert result == ["% header1", "% header2"]

    def test_empty(self):
        result = _extract_comment_lines(["data", "more data"])
        assert result == []


# ---------------------------------------------------------------------------
# 2. Label normalization
# ---------------------------------------------------------------------------

class TestLabelNormalization:
    def test_strip_quotes(self):
        assert _normalize_label('"Reflectance"') == "reflectance"

    def test_strip_whitespace(self):
        assert _normalize_label("  R  ") == "r"


# ---------------------------------------------------------------------------
# 3. Y-kind guessing
# ---------------------------------------------------------------------------

class TestYKindGuessing:
    def test_reflectance(self):
        assert _guess_y_kind("Reflectance", np.array([])) == "reflectance"

    def test_transmittance(self):
        assert _guess_y_kind("Transmittance", np.array([])) == "transmittance"

    def test_absorptance(self):
        assert _guess_y_kind("Absorptance", np.array([])) == "absorptance"

    def test_chinese_reflectance(self):
        assert _guess_y_kind("反射率", np.array([])) == "reflectance"

    def test_unknown(self):
        kind = _guess_y_kind("unknown", np.array([5.0]))
        assert kind == "unknown"


# ---------------------------------------------------------------------------
# 4. Simple CSV loading
# ---------------------------------------------------------------------------

class TestSimpleCSVLoading:
    def test_load_two_column(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        _make_simple_csv(csv_path)

        spec = load_spectrum_csv(csv_path)
        assert isinstance(spec, SpectrumData)
        assert len(spec.x_nm) == 5
        assert spec.y_kind == "reflectance"
        np.testing.assert_allclose(spec.x_nm, [400, 500, 600, 700, 800])
        np.testing.assert_allclose(spec.y, [0.05, 0.03, 0.02, 0.04, 0.06])

    def test_load_comsol_style(self, tmp_path):
        csv_path = tmp_path / "comsol.csv"
        _make_comsol_csv(csv_path)

        spec = load_spectrum_csv(csv_path)
        assert len(spec.x_nm) == 5
        assert spec.y_kind == "reflectance"

    def test_load_three_column(self, tmp_path):
        csv_path = tmp_path / "three.csv"
        _make_three_column_csv(csv_path)

        spec = load_spectrum_csv(csv_path, y_selector=2)
        assert spec.y_kind == "transmittance"


# ---------------------------------------------------------------------------
# 5. Missing / invalid files
# ---------------------------------------------------------------------------

class TestFileErrors:
    def test_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_spectrum_csv(Path("nonexistent.csv"))

    def test_empty_file(self, tmp_path):
        csv_path = tmp_path / "empty.csv"
        _write_csv(csv_path, "")
        with pytest.raises((ValueError, pd.errors.EmptyDataError)):
            load_spectrum_csv(csv_path)


# ---------------------------------------------------------------------------
# 6. Data ordering
# ---------------------------------------------------------------------------

class TestDataOrdering:
    def test_sorted_by_wavelength(self, tmp_path):
        csv_path = tmp_path / "unsorted.csv"
        content = """% wavelength_nm, R
800, 0.06
400, 0.05
600, 0.02
"""
        _write_csv(csv_path, content)

        spec = load_spectrum_csv(csv_path)
        assert np.all(np.diff(spec.x_nm) >= 0)


# ---------------------------------------------------------------------------
# 7. Output attributes
# ---------------------------------------------------------------------------

class TestOutputAttributes:
    def test_has_data_table(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        _make_simple_csv(csv_path)

        spec = load_spectrum_csv(csv_path)
        assert isinstance(spec.data_table, pd.DataFrame)
        assert len(spec.comment_lines) >= 1
        assert len(spec.all_column_labels) >= 2
