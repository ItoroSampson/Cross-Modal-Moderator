
@'
from fastapi import FastAPI, HTTPException
import aiohttp
import asyncio
from pydantic import BaseModel
import json

app = FastAPI(title="Cross-Modal Orchestrator")

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
    "fusion": "http://fusion-service:8005"
    "feedback": "http://feedback-service:8006"
}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_content(request: AnalysisRequest):
    import time
    start_time = time.time()
    prediction_id = str(uuid.uuid4())
    
    try:
        
        async with aiohttp.ClientSession() as session:
            image_task = session.post(f"{SERVICES['image']}/analyze", 
                                    json={"image_data": request.image_data})
            text_task = session.post(f"{SERVICES['text']}/analyze",
                                   json={"text_content": request.text_content})
            context_task = session.post(f"{SERVICES['context']}/analyze",
                                      json={"context": request.context})
            
            image_response, text_response, context_response = await asyncio.gather(
                image_task, text_task, context_task
            )
            
            risk_payload = {
                "image_analysis": await image_response.json(),
                "text_analysis": await text_response.json(), 
                "context_analysis": await context_response.json()
            }
            
            risk_response = await session.post(f"{SERVICES['risk']}/assess",
                                             json=risk_payload)
            
            fusion_payload = {
                "risk_assessment": await risk_response.json(),
                "original_input": request.dict()
            }
            
            fusion_response = await session.post(f"{SERVICES['fusion']}/fuse",
                                               json=fusion_payload)
            
            final_result = await fusion_response.json()
            processing_time = time.time() - start_time
            
            return AnalysisResponse(
                prediction_id=prediction_id,
                risk_score=final_result.get("risk_score", 0.5),
                confidence=final_result.get("confidence", 0.8),
                flags=final_result.get("flags", []),
                components_used=["image", "text", "context", "risk", "fusion"],
                processing_time=processing_time
                feedback_endpoint="/v1/feedback" 
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")


@app.post("/v1/feedback")
async def submit_feedback(feedback_request: dict):
    """
    Receive feedback from clients and forward to feedback service
    """
    try:
        async with aiohttp.ClientSession() as session:
            feedback_response = await session.post(
                f"{SERVICES['feedback']}/feedback",
                json=feedback_request,
                timeout=10.0
            )
            
            if feedback_response.status == 200:
                return await feedback_response.json()
            else:
                raise HTTPException(
                    status_code=feedback_response.status,
                    detail="Feedback service error"
                )
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")


@app.get("/v1/feedback-stats")
async def get_feedback_stats():
    """Get feedback statistics from feedback service"""
    try:
        async with aiohttp.ClientSession() as session:
            stats_response = await session.get(
                f"{SERVICES['feedback']}/feedback-stats",
                timeout=5.0
            )
            
            if stats_response.status == 200:
                return await stats_response.json()
            else:
                return {"error": "Could not fetch feedback stats"}
                
    except Exception as e:
        return {"error": f"Failed to get feedback stats: {str(e)}"}
    
@app.get("/health")
async def health_check():
    health_status = {}
    
    async with aiohttp.ClientSession() as session:
        for service_name, service_url in SERVICES.items():
            try:
                async with session.get(f"{service_url}/health", timeout=2.0) as response:
                    health_status[service_name] = {
                        "status": "healthy" if response.status == 200 else "unhealthy"
                    }
            except Exception as e:
                health_status[service_name] = {
                    "status": "unhealthy", 
                    "error": str(e)
                }
    
    return {
        "orchestrator": "healthy",
        "services": health_status,
        "platform": "cross-modal-microservices"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'@ | Out-File -FilePath app.py -Encoding utf8