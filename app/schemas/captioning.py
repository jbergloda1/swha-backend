from pydantic import BaseModel, Field
from typing import Optional

class CaptioningResponse(BaseModel):
    """Response model for the image captioning endpoint."""
    caption: str = Field(..., description="The generated caption for the image.")
    conditional_text: Optional[str] = Field(None, description="The conditional text used to generate the caption, if any.")
    model_name: str = Field("Salesforce/blip-image-captioning-base", description="The name of the model used for captioning.")
    processing_time_ms: float = Field(..., description="Time taken to generate the caption in milliseconds.") 