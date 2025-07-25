import logging
from typing import Optional
from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from app.core.config import settings
import io

logger = logging.getLogger(__name__)

class CaptioningService:
    """Service for image captioning using Salesforce BLIP model."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CaptioningService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'model'):
            self.device = "cuda" if torch.cuda.is_available() and not settings.FORCE_CPU else "cpu"
            self.model_name = "Salesforce/blip-image-captioning-base"
            self.processor, self.model = self._load_model()
            logger.info(f"Captioning Service initialized on device: {self.device}")

    def _load_model(self):
        """Load the BLIP model and processor."""
        logger.info(f"Loading image captioning model '{self.model_name}'...")
        try:
            processor = BlipProcessor.from_pretrained(self.model_name)
            model = BlipForConditionalGeneration.from_pretrained(self.model_name).to(self.device)
            logger.info(f"Image captioning model '{self.model_name}' loaded successfully.")
            return processor, model
        except Exception as e:
            logger.error(f"Error loading captioning model: {e}")
            raise RuntimeError(f"Could not load model '{self.model_name}'.")

    def generate_caption(self, image_bytes: bytes, conditional_text: Optional[str] = None) -> str:
        """
        Generates a caption for a given image.

        Args:
            image_bytes: The image file in bytes.
            conditional_text: Optional text to guide the caption generation.

        Returns:
            The generated caption string.
        """
        try:
            raw_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        except Exception as e:
            logger.error(f"Could not open image from bytes: {e}")
            raise ValueError("Invalid image data provided.")

        if conditional_text:
            # Conditional image captioning
            inputs = self.processor(raw_image, conditional_text, return_tensors="pt").to(self.device)
        else:
            # Unconditional image captioning
            inputs = self.processor(raw_image, return_tensors="pt").to(self.device)

        out = self.model.generate(**inputs)
        caption = self.processor.decode(out[0], skip_special_tokens=True)

        logger.info(f"Generated caption: '{caption}'")
        return caption

def get_captioning_service() -> CaptioningService:
    """Dependency injector for the CaptioningService."""
    return CaptioningService() 