from negpy.kernel.system.i18n import tr

from negpy.desktop.view.sidebar.base import BaseSidebar
from negpy.desktop.view.styles.templates import wrap_tooltip
from negpy.desktop.view.widgets.sliders import SliderGroup
from negpy.infrastructure.scanners.roll import XPAN_AUTO_STITCH_SETTING, XPAN_MODE_SETTING

_TOGGLE_TIP = tr("Let each frame in the Coolscan strip preview move up to 55 mm, for XPAN panoramas.")
_AUTO_STITCH_TIP = tr("After a strip scan, stitch each two scans in a row into one XPAN frame.")


class XpanSidebar(BaseSidebar):
    """XPAN Mode and its Auto Stitch: app-wide settings. The strip preview reads XPAN Mode when it opens."""

    def _init_ui(self) -> None:
        self.enable_btn = self._small_toggle(
            "mdi.panorama-horizontal",
            tr("XPAN Mode"),
            self._saved(XPAN_MODE_SETTING),
            wrap_tooltip(_TOGGLE_TIP),
            align_left=True,
        )
        self.layout.addWidget(self.enable_btn)
        self.auto_stitch_btn = self._small_toggle(
            "fa5s.object-group",
            tr("Auto Stitch"),
            self._saved(XPAN_AUTO_STITCH_SETTING),
            wrap_tooltip(_AUTO_STITCH_TIP),
            align_left=True,
        )
        self.layout.addWidget(SliderGroup(self.auto_stitch_btn))

    def _connect_signals(self) -> None:
        self.enable_btn.toggled.connect(lambda checked: self._save(XPAN_MODE_SETTING, checked))
        self.auto_stitch_btn.toggled.connect(lambda checked: self._save(XPAN_AUTO_STITCH_SETTING, checked))
        self.sync_ui()

    def _saved(self, key: str) -> bool:
        return bool(self.controller.session.repo.get_global_setting(key, False))

    def _save(self, key: str, checked: bool) -> None:
        self.controller.session.repo.save_global_setting(key, bool(checked))
        self.auto_stitch_btn.setEnabled(self.enable_btn.isChecked())

    def sync_ui(self) -> None:
        for btn, key in ((self.enable_btn, XPAN_MODE_SETTING), (self.auto_stitch_btn, XPAN_AUTO_STITCH_SETTING)):
            btn.blockSignals(True)
            btn.setChecked(self._saved(key))
            btn.blockSignals(False)
        self.auto_stitch_btn.setEnabled(self.enable_btn.isChecked())
