from fastapi import FastAPI
from pydantic import BaseModel
import boto3
import base64
from io import BytesIO
from PIL import Image
import time
from prometheus_client import Counter, Histogram, generate_latest

app = FastAPI(title="Image Analysis Service")


IMAGE_REQUEST_COUNT = Counter('image_requests_total', 'Total image analysis requests')
IMAGE_PROCESSING_TIME = Histogram('image_processing_seconds', 'Image processing time')

class ImageRequest(BaseModel):
    image_data: str  

class ImageResponse(BaseModel):
    categories: list
    moderation_flagged: bool
    moderation_labels: list
    processing_time: float


rekognition = boto3.client('rekognition', region_name='us-east-1')

def analyze_image(image_bytes):
    """EXACT COPY FROM MY LAMBDA - Image analysis logic"""
    labels = rekognition.detect_labels(Image={'Bytes': image_bytes}, MaxLabels=10, MinConfidence=60)
    moderation = rekognition.detect_moderation_labels(Image={'Bytes': image_bytes}, MinConfidence=50)
    
    return {
        'categories': [label['Name'] for label in labels['Labels']],
        'moderation_flagged': len(moderation['ModerationLabels']) > 0,
        'moderation_labels': [label['Name'] for label in moderation['ModerationLabels']]
    }

def preprocess_image(image_data: str):
    """EXACT COPY FROM MY LAMBDA - Image preprocessing"""
    missing_padding = len(image_data) % 4
    if missing_padding:
        image_data += '=' * (4 - missing_padding)
    
    image_bytes = base64.b64decode(image_data)
    return image_bytes

@app.post("/analyze")
async def analyze_image_endpoint(request: ImageRequest):
    start_time = time.time()
    IMAGE_REQUEST_COUNT.inc()
    
    try:
        with IMAGE_PROCESSING_TIME.time():
            
            image_bytes = preprocess_image(request.image_data)
            image_result = analyze_image(image_bytes)
            
            processing_time = time.time() - start_time
            
            return ImageResponse(
                categories=image_result['categories'],
                moderation_flagged=image_result['moderation_flagged'],
                moderation_labels=image_result['moderation_labels'],
                processing_time=processing_time
            )
            
    except Exception as e:
        return {"error": f"Image processing failed: {str(e)}"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "image-analysis"}

@app.get("/metrics")
async def metrics():
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)