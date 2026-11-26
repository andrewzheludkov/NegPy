from negpy.kernel.system.i18n import tr

from negpy.desktop.view.sidebar.base import BaseSidebar
from negpy.desktop.view.widgets.sliders import CompactSlider

# Print Density at Exposure 0 %; each 100 % is one unit of density.
_DENSITY_AT_ZERO = 1.0
BASIC_EXPOSURE_FIELDS = ("density", "highlight_density", "shadow_density")


def _percent_slider(label: str, tooltip: str) -> CompactSlider:
    slider = CompactSlider(label, -100.0, 100.0, 0.0, step=1.0, unit="%", has_neutral=True)
    slider.setToolTip(tooltip)
    return slider


class BasicExposureSidebar(BaseSidebar):
    """Photo-editor names over the print controls: Exposure is Print Density, Highlights and Shadows
    are the zone densities, all with the sign turned so that more is lighter. Brightness is its own
    midtone lift on the finished print."""

    def _init_ui(self) -> None:
        self.exposure_slider = _percent_slider(tr("Exposure"), tr("Exposure: makes the whole picture lighter or darker."))
        self.highlights_slider = _percent_slider(
            tr("Highlights"), tr("Highlights: makes only the bright parts of the picture lighter or darker.")
        )
        self.shadows_slider = _percent_slider(tr("Shadows"), tr("Shadows: makes only the dark parts of the picture lighter or darker."))
        self.brightness_slider = _percent_slider(
            tr("Brightness"), tr("Brightness: makes the middle tones lighter or darker, while black and white stay.")
        )
        for slider in (self.exposure_slider, self.highlights_slider, self.shadows_slider, self.brightness_slider):
            self.layout.addWidget(slider)
        self.layout.addStretch()

    def _exposure(self, field: str, value: float, persist: bool) -> None:
        self.update_config_section("exposure", render=True, persist=persist, readback_metrics=persist, **{field: value})

    def _on_exposure(self, pct: float, persist: bool = False) -> None:
        self._exposure("density", max(0.0, min(2.0, _DENSITY_AT_ZERO - pct / 100.0)), persist)

    def _on_brightness(self, pct: float, persist: bool = False) -> None:
        self.update_config_section("adjust", render=True, persist=persist, readback_metrics=persist, brightness=pct / 100.0)

    def _connect_signals(self) -> None:
        self.exposure_slider.valueChanged.connect(self._on_exposure)
        self.exposure_slider.valueCommitted.connect(lambda v: self._on_exposure(v, persist=True))
        for slider, field in ((self.highlights_slider, "highlight_density"), (self.shadows_slider, "shadow_density")):
            slider.valueChanged.connect(lambda v, f=field: self._exposure(f, -v / 100.0, False))
            slider.valueCommitted.connect(lambda v, f=field: self._exposure(f, -v / 100.0, True))
        self.brightness_slider.valueChanged.connect(self._on_brightness)
        self.brightness_slider.valueCommitted.connect(lambda v: self._on_brightness(v, persist=True))

    def sync_ui(self) -> None:
        conf = self.state.config.exposure
        self.block_signals(True)
        try:
            self.exposure_slider.setValue(round((_DENSITY_AT_ZERO - conf.density) * 100.0))
            self.highlights_slider.setValue(round(-conf.highlight_density * 100.0))
            self.shadows_slider.setValue(round(-conf.shadow_density * 100.0))
            self.brightness_slider.setValue(round(self.state.config.adjust.brightness * 100.0))
        finally:
            self.block_signals(False)

    def block_signals(self, blocked: bool) -> None:
        for w in (self.exposure_slider, self.highlights_slider, self.shadows_slider, self.brightness_slider):
            w.blockSignals(blocked)
