from dataclasses import dataclass

# Selective Color bands, in hue order. Each band has its sc_<band>_hue, _sat and _lum field.
BANDS = ("red", "orange", "yellow", "green", "cyan", "blue", "purple", "magenta")
BAND_KEYS = ("hue", "sat", "lum")


@dataclass(frozen=True)
class AdjustConfig:
    """
    Photo-editor controls on the finished print: Brightness and Selective Color.
    Every value is a fraction of full travel, -1..1, 0 = off.
    """

    brightness: float = 0.0
    # Off keeps the band values but skips them.
    selective_enabled: bool = True
    sc_red_hue: float = 0.0
    sc_red_sat: float = 0.0
    sc_red_lum: float = 0.0
    sc_orange_hue: float = 0.0
    sc_orange_sat: float = 0.0
    sc_orange_lum: float = 0.0
    sc_yellow_hue: float = 0.0
    sc_yellow_sat: float = 0.0
    sc_yellow_lum: float = 0.0
    sc_green_hue: float = 0.0
    sc_green_sat: float = 0.0
    sc_green_lum: float = 0.0
    sc_cyan_hue: float = 0.0
    sc_cyan_sat: float = 0.0
    sc_cyan_lum: float = 0.0
    sc_blue_hue: float = 0.0
    sc_blue_sat: float = 0.0
    sc_blue_lum: float = 0.0
    sc_purple_hue: float = 0.0
    sc_purple_sat: float = 0.0
    sc_purple_lum: float = 0.0
    sc_magenta_hue: float = 0.0
    sc_magenta_sat: float = 0.0
    sc_magenta_lum: float = 0.0


def band_field(band: str, key: str) -> str:
    return f"sc_{band}_{key}"


def band_values(config: AdjustConfig, key: str) -> tuple:
    return tuple(float(getattr(config, band_field(b, key))) for b in BANDS)


SELECTIVE_FIELDS = ("selective_enabled", *(band_field(b, k) for b in BANDS for k in BAND_KEYS))
