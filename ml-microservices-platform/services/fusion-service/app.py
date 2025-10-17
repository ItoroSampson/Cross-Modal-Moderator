from fastapi import FastAPI
from pydantic import BaseModel
import boto3
import uuid
from datetime import datetime
import time
from prometheus_client import Counter, Histogram, generate_latest

app = FastAPI(title="Fusion & Decision Service")


FUSION_REQUEST_COUNT = Counter('fusion_requests_total', 'Total fusion requests')
FUSION_PROCESSING_TIME = Histogram('fusion_processing_seconds', 'Fusion processing time')

class FusionRequest(BaseModel):
    risk_assessment: dict
    original_input: dict

class FusionResponse(BaseModel):
    analysis_id: str
    risk_score: float
    needs_review: bool
    image_categories: list
    text_sentiment: str
    unsafe_found: list
    explanation: str
    processing_time: float
    prediction_id: str  

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('ContentModerationResults')

@app.post("/fuse")
async def fuse_decisions(request: FusionRequest):
    start_time = time.time()
    FUSION_REQUEST_COUNT.inc()
    
    try:
        with FUSION_PROCESSING_TIME.time():
            risk_assessment = request.risk_assessment
            original_input = request.original_input
            
            
            analysis_id = f"mod_{uuid.uuid4().hex[:8]}"
            
            # Store in DynamoDB (from my Lambda)
            item = {
                'analysis_id': analysis_id,
                'timestamp': datetime.utcnow().isoformat(),
                'risk_score': risk_assessment['risk_score'],
                'needs_review': risk_assessment['needs_review'],
                'image_categories': original_input.get('image_analysis', {}).get('categories', [])[:3],
                'text_sentiment': original_input.get('text_analysis', {}).get('sentiment', ''),
                'unsafe_words_found': original_input.get('text_analysis', {}).get('unsafe_found', []),
                'moderation_flagged': original_input.get('image_analysis', {}).get('moderation_flagged', False),
                'explanation': risk_assessment['explanation']
            }
            
            
            table.put_item(Item=item)
            
            processing_time = time.time() - start_time
            
            return FusionResponse(
                analysis_id=analysis_id,
                risk_score=risk_assessment['risk_score'],
                needs_review=risk_assessment['needs_review'],
                image_categories=original_input.get('image_analysis', {}).get('categories', [])[:3],
                text_sentiment=original_input.get('text_analysis', {}).get('sentiment', ''),
                unsafe_found=original_input.get('text_analysis', {}).get('unsafe_found', []),
                explanation=risk_assessment['explanation'],
                processing_time=processing_time
                prediction_id=analysis_id 
            )
            
    except Exception as e:
        return {"error": f"Fusion processing failed: {str(e)}"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "fusion-decision"}

@app.get("/metrics")
async def metrics():
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)