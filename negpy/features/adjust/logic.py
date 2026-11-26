import negpy_core
import numpy as np

from negpy.domain.types import ImageBuffer
from negpy.features.adjust.models import AdjustConfig, band_values

# Brightness at 1.0 raises Oklab L to 2^-BRIGHTNESS_STOPS. Mirrors negpy_core/src/color.rs.
BRIGHTNESS_STOPS = 0.7


def brightness_gamma(brightness: float) -> float:
    """The power on Oklab L for a Brightness value; 1.0 at 0."""
    return 2.0 ** (-BRIGHTNESS_STOPS * max(-1.0, min(1.0, float(brightness))))


def hsl_active(config: AdjustConfig) -> bool:
    return config.selective_enabled and any(v != 0.0 for k in ("hue", "sat", "lum") for v in band_values(config, k))


def adjust_active(config: AdjustConfig) -> bool:
    return hsl_active(config) or config.brightness != 0.0


def apply_adjust(img: ImageBuffer, config: AdjustConfig) -> ImageBuffer:
    """Selective Color, then Brightness, on linear RGB. The identity when both are off."""
    if not adjust_active(config):
        return img
    gamma = brightness_gamma(config.brightness)
    return negpy_core.adjust(
        np.ascontiguousarray(img, dtype=np.float32),
        band_values(config, "hue"),
        band_values(config, "sat"),
        band_values(config, "lum"),
        hsl_active(config),
        gamma,
    )
