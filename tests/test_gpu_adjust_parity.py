"""GPU/CPU parity for Brightness and Selective Color (negpy_core adjust and lab.wgsl)."""

import unittest
from dataclasses import replace

import numpy as np

from negpy.domain.models import WorkspaceConfig
from negpy.infrastructure.gpu.device import GPUDevice


def _image() -> np.ndarray:
    rng = np.random.default_rng(4)
    h, w = 48, 64
    hue = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :].repeat(h, axis=0)
    val = np.linspace(0.08, 0.9, h, dtype=np.float32)[:, None].repeat(w, axis=1)
    rgb = np.stack([np.abs(np.sin(np.pi * (hue + k / 3.0))) for k in range(3)], axis=-1) * val[..., None]
    return np.ascontiguousarray(rgb + rng.uniform(0, 0.01, rgb.shape).astype(np.float32))


@unittest.skipUnless(GPUDevice.get().is_available, "GPU not available")
class TestGpuAdjustParity(unittest.TestCase):
    def _render(self, processor, settings, img, prefer_gpu):
        result, _ = processor.run_pipeline(
            img, settings, "adjust-parity", render_size_ref=float(max(img.shape[:2])), prefer_gpu=prefer_gpu, readback_metrics=False
        )
        arr = np.asarray(result.readback() if hasattr(result, "readback") else result)[:, :, :3]
        return arr.astype(np.float64)

    def test_bands_and_brightness_match(self):
        from negpy.services.rendering.image_processor import ImageProcessor

        processor = ImageProcessor()
        if processor.engine_gpu is None:
            self.skipTest("GPU engine not initialised")
        s = WorkspaceConfig()
        adjust = replace(
            s.adjust, brightness=0.4, sc_red_hue=0.5, sc_orange_sat=-0.6, sc_blue_lum=0.7, sc_green_sat=0.5, sc_purple_hue=-1.0
        )
        settings = replace(s, adjust=adjust)
        img = _image()
        cpu = self._render(processor, settings, img, prefer_gpu=False)
        gpu = self._render(processor, settings, img, prefer_gpu=True)
        base = self._render(processor, s, img, prefer_gpu=False)
        self.assertGreater(float(np.abs(cpu - base).max()), 0.05)
        self.assertLess(float(np.abs(cpu - gpu).max()), 4e-3)
