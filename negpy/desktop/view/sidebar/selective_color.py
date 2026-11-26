from negpy.kernel.system.i18n import tr

from negpy.desktop.view.sidebar.base import BaseSidebar, SliderPage
from negpy.desktop.view.styles.theme import THEME
from negpy.desktop.view.widgets.segmented_choice import SegmentedChoice
from negpy.desktop.view.widgets.sliders import CompactSlider
from negpy.features.adjust.models import BAND_KEYS, BANDS, band_field

# Red takes the red channel's text tone: the one bright red the theme allows beside errors.
_BAND_COLORS = (THEME.channel_red_text, *(getattr(THEME, f"band_{b}") for b in BANDS[1:]))


def band_names() -> tuple[str, ...]:
    return (tr("Red"), tr("Orange"), tr("Yellow"), tr("Green"), tr("Cyan"), tr("Blue"), tr("Purple"), tr("Magenta"))


def _percent_slider(label: str, tooltip: str) -> CompactSlider:
    slider = CompactSlider(label, -100.0, 100.0, 0.0, step=1.0, unit="%", has_neutral=True)
    slider.setToolTip(tooltip)
    return slider


class SelectiveColorSidebar(BaseSidebar):
    """One color range at a time: its Hue, Saturation and Luminance. The header toggle turns every
    range off without losing the values."""

    def _init_ui(self) -> None:
        self.band_btn = SegmentedChoice(
            tuple(("fa5s.square", name, color) for name, color in zip(band_names(), _BAND_COLORS)),
            tr("Pick the color range that the sliders below change."),
            icon_only=tuple(range(len(BANDS))),
        )
        self.layout.addWidget(self.band_btn)
        self.hue_slider = _percent_slider(tr("Hue"), tr("Hue: turns this color toward its neighbor colors."))
        self.sat_slider = _percent_slider(tr("Saturation"), tr("Saturation: makes this color stronger or weaker, down to gray."))
        self.lum_slider = _percent_slider(tr("Luminance"), tr("Luminance: makes this color lighter or darker."))
        self._sliders = (self.hue_slider, self.sat_slider, self.lum_slider)
        for slider in self._sliders:
            self.layout.addWidget(slider)
        self.layout.addStretch()

    def _band(self) -> str:
        return BANDS[self.band_btn.currentIndex()]

    def _on_value(self, key: str, pct: float, persist: bool = False) -> None:
        changes = {band_field(self._band(), key): pct / 100.0}
        if pct != 0.0 and not self.state.config.adjust.selective_enabled:
            changes["selective_enabled"] = True
        self.update_config_section("adjust", render=True, persist=persist, readback_metrics=persist, **changes)

    def set_enabled(self, on: bool) -> None:
        self.update_config_section("adjust", render=True, persist=True, selective_enabled=on)

    def _connect_signals(self) -> None:
        self.band_btn.currentChanged.connect(lambda _i: self.sync_ui())
        for slider, key in zip(self._sliders, BAND_KEYS):
            slider.valueChanged.connect(lambda v, k=key: self._on_value(k, v))
            slider.valueCommitted.connect(lambda v, k=key: self._on_value(k, v, persist=True))

    def slider_pages(self) -> tuple[SliderPage, ...]:
        conf = self.state.config.adjust
        return tuple(
            SliderPage(self.band_btn, i, slider.label.text(), slider, getattr(conf, band_field(band, key)) * 100.0)
            for i, band in enumerate(BANDS)
            for slider, key in zip(self._sliders, BAND_KEYS)
        )

    def sync_ui(self) -> None:
        conf = self.state.config.adjust
        self.block_signals(True)
        try:
            for slider, key in zip(self._sliders, BAND_KEYS):
                slider.setValue(round(getattr(conf, band_field(self._band(), key)) * 100.0))
            for i, band in enumerate(BANDS):
                self.band_btn.set_edited(i, any(getattr(conf, band_field(band, k)) != 0.0 for k in BAND_KEYS))
        finally:
            self.block_signals(False)

    def block_signals(self, blocked: bool) -> None:
        for w in (self.band_btn, *self._sliders):
            w.blockSignals(blocked)
