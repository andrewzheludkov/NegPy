"""Brightness, Selective Color, and the White Balance card's Temperature and Tint mapping."""

from dataclasses import replace

import numpy as np
import pytest

from negpy.domain.models import WorkspaceConfig
from negpy.features.adjust.logic import apply_adjust, brightness_gamma
from negpy.features.adjust.models import SELECTIVE_FIELDS, AdjustConfig
from negpy.features.exposure.logic import temp_tint_of, temp_tint_to_wb, wb_to_kelvin
from negpy.features.transparency.logic import slide_temp_to_wb, slide_wb_to_kelvin


def _img() -> np.ndarray:
    rng = np.random.default_rng(7)
    return np.ascontiguousarray(rng.uniform(0.02, 0.95, (16, 16, 3)).astype(np.float32))


def test_defaults_are_the_identity():
    img = _img()
    assert apply_adjust(img, AdjustConfig()) is img


def test_off_keeps_the_bands_and_skips_them():
    img = _img()
    cfg = AdjustConfig(sc_red_sat=-1.0, selective_enabled=False)
    assert apply_adjust(img, cfg) is img


def test_a_band_leaves_grays_alone():
    gray = np.full((4, 4, 3), 0.4, np.float32)
    out = apply_adjust(gray, AdjustConfig(**{f: 1.0 for f in SELECTIVE_FIELDS if f != "selective_enabled"}))
    np.testing.assert_allclose(out, gray, atol=1e-5)


def test_blue_saturation_leaves_red_alone():
    red = np.array([[[0.7, 0.05, 0.05]]], np.float32)
    out = apply_adjust(red, AdjustConfig(sc_blue_sat=-1.0))
    np.testing.assert_allclose(out, red, atol=1e-5)


@pytest.mark.parametrize("b", (-1.0, -0.4, 0.4, 1.0))
def test_brightness_moves_midtones_in_its_direction(b):
    mid = np.full((1, 1, 3), 0.18, np.float32)
    out = float(apply_adjust(mid, AdjustConfig(brightness=b))[0, 0, 0])
    assert (out > 0.18) == (b > 0)
    assert brightness_gamma(b) != 1.0


def test_adjust_flat_keys_round_trip():
    cfg = replace(WorkspaceConfig(), adjust=AdjustConfig(brightness=0.3, sc_cyan_hue=-0.5, selective_enabled=False))
    assert WorkspaceConfig.from_flat_dict(cfg.to_dict()).adjust == cfg.adjust


def test_print_temperature_and_tint_round_trip():
    for t, n in ((0.0, 0.0), (0.4, -0.2), (-0.7, 0.3)):
        m, y = temp_tint_to_wb(t, n)
        assert temp_tint_of(m, y) == pytest.approx((t, n))


def test_print_temperature_alone_follows_the_kelvin_direction():
    m, y = temp_tint_to_wb(0.5, 0.0)
    assert wb_to_kelvin(m, y) < 5500.0
    # Pure Planckian: the Kelvin pair is along (km, ky), so Tint stays 0.
    assert temp_tint_of(m, y)[1] == pytest.approx(0.0)


def test_slide_temperature_warms_and_keeps_a_hand_cyan_offset():
    c, y = slide_temp_to_wb(0.5, 0.1, 0.0)
    assert slide_wb_to_kelvin(c, y) < slide_wb_to_kelvin(0.1, 0.0)
    c0, y0 = slide_temp_to_wb(0.0, c, y)
    assert (c0, y0) == pytest.approx((0.1, 0.0))
