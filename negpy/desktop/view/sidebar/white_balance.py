from negpy.kernel.system.i18n import tr
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from negpy.desktop.session import ToolMode
from negpy.desktop.view.sidebar.base import BaseSidebar
from negpy.desktop.view.styles.templates import FIELD_LABEL_WIDTH, ICON_BUTTON_WIDTH, field_label, hint_label
from negpy.desktop.view.widgets.sliders import CompactSlider
from negpy.features.exposure.logic import temp_tint_of, temp_tint_to_wb
from negpy.features.process.path import RenderPath, is_mono, render_path
from negpy.features.transparency.logic import slide_temp_to_wb

# The global filtration this card drives: the Filtration card's Global Cyan, Magenta and Yellow.
WB_FIELDS = ("wb_cyan", "wb_magenta", "wb_yellow")


def _percent_slider(label: str, name: str, tooltip: str) -> CompactSlider:
    slider = CompactSlider(label, -100.0, 100.0, 0.0, step=1.0, unit="%", has_neutral=True)
    slider.slider.setObjectName(name)
    slider.setToolTip(tooltip)
    return slider


class WhiteBalanceSidebar(BaseSidebar):
    """Gray picker, Temperature and Tint over the global filtration. Temperature is Yellow; Tint is
    Magenta past the Planckian share of Yellow on a print, plain Magenta on a slide."""

    def _init_ui(self) -> None:
        self.mono_hint = hint_label(tr("A black-and-white picture has no white balance."))
        self.layout.addWidget(self.mono_hint)

        self.body = QWidget()
        self.body.setObjectName("collapsible_content_body")
        col = QVBoxLayout(self.body)
        col.setContentsMargins(0, 0, 0, 0)

        self.gray_btn = self._tool_toggle(
            "fa5s.eye-dropper",
            "",
            tr("Gray: click something in the picture that should be gray, and the colors are corrected to make it gray."),
        )
        self.gray_btn.setFixedWidth(ICON_BUTTON_WIDTH)
        self.gray_btn.setProperty("value_column", True)
        gray_row = QHBoxLayout()
        gray_row.addWidget(field_label(tr("Gray"), FIELD_LABEL_WIDTH))
        gray_row.addStretch(1)
        gray_row.addWidget(self.gray_btn)
        col.addLayout(gray_row)

        self.temp_slider = _percent_slider(
            tr("Temperature"), "temperature_slider", tr("Temperature: makes the picture cooler (more blue) or warmer (more yellow).")
        )
        self.tint_slider = _percent_slider(tr("Tint"), "tint_slider", tr("Tint: makes the picture more green or more magenta."))
        col.addWidget(self.temp_slider)
        col.addWidget(self.tint_slider)
        self.layout.addWidget(self.body)
        self.layout.addStretch()

    def _is_slide(self) -> bool:
        return render_path(self.state.config.process) is not RenderPath.PRINT

    def temp_tint(self) -> tuple[float, float]:
        conf = self.state.config.exposure
        if self._is_slide():
            return conf.wb_yellow, conf.wb_magenta
        return temp_tint_of(conf.wb_magenta, conf.wb_yellow)

    def _connect_signals(self) -> None:
        self.temp_slider.valueChanged.connect(lambda v: self._on_temp(v / 100.0))
        self.temp_slider.valueCommitted.connect(lambda v: self._on_temp(v / 100.0, persist=True))
        self.tint_slider.valueChanged.connect(lambda v: self._on_tint(v / 100.0))
        self.tint_slider.valueCommitted.connect(lambda v: self._on_tint(v / 100.0, persist=True))
        self.gray_btn.clicked.connect(self._on_gray_clicked)

    def _apply(self, persist: bool, **fields: float) -> None:
        self.update_config_section("exposure", render=True, persist=persist, readback_metrics=persist, **fields)

    def _on_temp(self, temperature: float, persist: bool = False) -> None:
        conf = self.state.config.exposure
        if self._is_slide():
            c, y = slide_temp_to_wb(temperature, conf.wb_cyan, conf.wb_yellow)
            self._apply(persist, wb_cyan=c, wb_yellow=y)
            return
        m, y = temp_tint_to_wb(temperature, self.temp_tint()[1])
        self._apply(persist, wb_magenta=m, wb_yellow=y)

    def _on_tint(self, tint: float, persist: bool = False) -> None:
        if self._is_slide():
            self._apply(persist, wb_magenta=max(-1.0, min(1.0, tint)))
            return
        m, y = temp_tint_to_wb(self.temp_tint()[0], tint)
        self._apply(persist, wb_magenta=m, wb_yellow=y)

    def _on_gray_clicked(self, checked: bool) -> None:
        # The pick lands on the global filtration, whatever region the Filtration card shows.
        self.state.wb_pick_global = checked
        self.controller.set_active_tool(ToolMode.WB_PICK if checked else ToolMode.NONE)

    def sync_ui(self) -> None:
        self.block_signals(True)
        try:
            temperature, tint = self.temp_tint()
            self.temp_slider.setValue(round(temperature * 100.0))
            self.tint_slider.setValue(round(tint * 100.0))
            self.gray_btn.setChecked(self.state.active_tool == ToolMode.WB_PICK and self.state.wb_pick_global)
            bw = is_mono(self.state.config.process)
            self.mono_hint.setVisible(bw)
            self.body.setEnabled(not bw)
        finally:
            self.block_signals(False)

    def block_signals(self, blocked: bool) -> None:
        for w in (self.temp_slider, self.tint_slider, self.gray_btn):
            w.blockSignals(blocked)
