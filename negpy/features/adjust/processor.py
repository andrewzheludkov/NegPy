from negpy.domain.interfaces import PipelineContext
from negpy.domain.types import ImageBuffer
from negpy.features.adjust.logic import apply_adjust
from negpy.features.adjust.models import AdjustConfig


class AdjustProcessor:
    def __init__(self, config: AdjustConfig):
        self.config = config

    def process(self, image: ImageBuffer, context: PipelineContext) -> ImageBuffer:
        return apply_adjust(image, self.config)
