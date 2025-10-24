from fastapi import FastAPI, HTTPException
import aiohttp
import asyncio
from pydantic import BaseModel
import time
import uuid
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY

app = FastAPI(title="Cross-Modal Orchestrator")


REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
PREDICTION_LATENCY = Histogram('prediction_latency_seconds', 'Prediction latency')
MODEL_INFERENCE_TIME = Histogram('model_inference_seconds', 'Model inference time', ['model_type'])

class AnalysisRequest(BaseModel):
    image_data: str
    text_content: str
    context: dict = {}

class AnalysisResponse(BaseModel):
    prediction_id: str
    risk_score: float
    confidence: float
    flags: list
    components_used: list
    processing_time: float
    model_version: str = "1.0.0"
    feedback_endpoint: str = "/v1/feedback"


SERVICES = {
    "image": "http://image-service:8001",
    "text": "http://text-service:8002",
    "context": "http://context-service:8003",
    "risk": "http://risk-service:8004",
    "fusion": "http://fusion-service:8005",
    "feedback": "http://feedback-service:8006"
}

@app.middleware("http")
async def monitor_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    response.headers["X-Processing-Time"] = str(duration)
    return response

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_content(request: AnalysisRequest):
    start_time = time.time()
    prediction_id = str(uuid.uuid4())
    
    try:
        with PREDICTION_LATENCY.time():
            async with aiohttp.ClientSession() as session:
                
                with MODEL_INFERENCE_TIME.labels('image_text_context').time():
                    image_task = session.post(f"{SERVICES['image']}/analyze", json={"image_data": request.image_data})
                    text_task = session.post(f"{SERVICES['text']}/analyze", json={"text_content": request.text_content})
                    context_task = session.post(f"{SERVICES['context']}/analyze", json={"context": request.context})
                    
                    image_response, text_response, context_response = await asyncio.gather(image_task, text_task, context_task)
                
                
                with MODEL_INFERENCE_TIME.labels('risk').time():
                    risk_payload = {
                        "image_analysis": await image_response.json(),
                        "text_analysis": await text_response.json(),
                        "context_analysis": await context_response.json()
                    }
                    
                    risk_response = await session.post(f"{SERVICES['risk']}/assess", json=risk_payload)
                
                
                with MODEL_INFERENCE_TIME.labels('fusion').time():
                    fusion_payload = {
                        "risk_assessment": await risk_response.json(),
                        "original_input": request.dict()
                    }
                    
                    fusion_response = await session.post(f"{SERVICES['fusion']}/fuse", json=fusion_payload)
                    final_result = await fusion_response.json()
                
                processing_time = time.time() - start_time
                
                return AnalysisResponse(
                    prediction_id=prediction_id,
                    risk_score=final_result.get("risk_score", 0.5),
                    confidence=final_result.get("confidence", 0.8),
                    flags=final_result.get("flags", []),
                    components_used=["image", "text", "context", "risk", "fusion"],
                    processing_time=processing_time
                )
                
    except Exception as e:
        REQUEST_COUNT.labels(method='POST', endpoint='/analyze', status=500).inc()
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "orchestrator"}

@app.get("/metrics")
async def metrics():
    return generate_latest(REGISTRY)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)