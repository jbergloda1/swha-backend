from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from typing import Optional
from PIL import Image, ImageDraw
import torch
from transformers import AutoImageProcessor, TableTransformerForObjectDetection
import requests
import io

router = APIRouter()

# Load model và processor chỉ 1 lần
MODEL_NAME = "microsoft/table-transformer-detection"
image_processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
model = TableTransformerForObjectDetection.from_pretrained(MODEL_NAME)
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

@router.post("/detect")
async def detect_table(
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    visualize: Optional[bool] = Form(False)
):
    """Detect bảng (table) trong ảnh, trả về bounding box các bảng hoặc ảnh đã vẽ box."""
    if not file and not image_url:
        raise HTTPException(status_code=400, detail="Either file or image_url must be provided.")
    if file and image_url:
        raise HTTPException(status_code=400, detail="Provide either file or image_url, not both.")

    # Đọc ảnh
    try:
        if file:
            image = Image.open(file.file).convert("RGB")
        else:
            response = requests.get(image_url)
            image = Image.open(io.BytesIO(response.content)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read image: {e}")

    # Tiền xử lý
    inputs = image_processor(images=image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Dự đoán
    with torch.no_grad():
        outputs = model(**inputs)

    # Lấy kết quả bbox
    target_sizes = torch.tensor([image.size[::-1]], device=device)
    results = image_processor.post_process_object_detection(outputs, threshold=0.9, target_sizes=target_sizes)[0]

    tables = []
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        if model.config.id2label[label.item()] == "table":
            tables.append({
                "score": float(score),
                "bbox": [float(x) for x in box.tolist()]
            })

    if visualize:
        # Vẽ bounding box lên ảnh
        draw = ImageDraw.Draw(image)
        for t in tables:
            bbox = t["bbox"]
            draw.rectangle(bbox, outline="red", width=3)
        # Lưu vào buffer
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)
        return Response(content=buf.getvalue(), media_type="image/png")

    return {"tables": tables, "num_tables": len(tables)} 