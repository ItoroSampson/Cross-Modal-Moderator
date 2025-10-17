from fastapi import FastAPI
from pydantic import BaseModel
import time
from prometheus_client import Counter, Histogram, generate_latest

app = FastAPI(title="Context Intelligence Service")


CONTEXT_REQUEST_COUNT = Counter('context_requests_total', 'Total context analysis requests')
CONTEXT_PROCESSING_TIME = Histogram('context_processing_seconds', 'Context processing time')

class ContextRequest(BaseModel):
    context: dict

class ContextResponse(BaseModel):
    context_score: float
    platform_risk: str
    temporal_factors: dict
    geographic_risk: str
    processing_time: float


def analyze_context_enhanced(context_data: dict) -> dict:
    """ENHANCED CONTEXT ANALYSIS - Beyond my current Lambda logic"""
    
    platform = context_data.get('platform', 'unknown').lower()
    platform_risk = calculate_platform_risk(platform)
    
    temporal_factors = analyze_temporal_factors(context_data)
    geographic_risk = assess_geographic_risk(context_data)
    user_risk_profile = assess_user_context(context_data)
    
    context_score = calculate_overall_context_score(
        platform_risk, temporal_factors, geographic_risk, user_risk_profile
    )
    
    return {
        'context_score': context_score,
        'platform_risk': platform_risk,
        'temporal_factors': temporal_factors,
        'geographic_risk': geographic_risk
    }

def calculate_platform_risk(platform: str) -> str:
    high_risk_platforms = {'anonymous', 'darkweb', 'tor'}
    medium_risk_platforms = {'social', 'forum', 'chat'}
    
    if platform in high_risk_platforms:
        return "high"
    elif platform in medium_risk_platforms:
        return "medium"
    else:
        return "low"

def analyze_temporal_factors(context_data: dict) -> dict:
    import datetime
    hour = context_data.get('hour', datetime.datetime.utcnow().hour)
    day_of_week = context_data.get('day_of_week', datetime.datetime.utcnow().weekday())
    
    late_night_risk = 0.3 if 0 <= hour <= 4 else 0.0
    weekend_risk = 0.2 if day_of_week >= 5 else 0.0
    
    return {
        'late_night_risk': late_night_risk,
        'weekend_risk': weekend_risk,
        'peak_hour_risk': 0.1 if 8 <= hour <= 10 or 17 <= hour <= 19 else 0.0
    }

def assess_geographic_risk(context_data: dict) -> str:
    country = context_data.get('country', 'unknown')
    high_risk_countries = {'unknown', 'test', 'localhost'}
    return "high" if country in high_risk_countries else "low"

def assess_user_context(context_data: dict) -> float:
    user_reputation = context_data.get('user_reputation_score', 0.5)
    previous_flags = context_data.get('previous_moderation_flags', 0)
    user_risk = (1.0 - user_reputation) * 0.4
    user_risk += min(previous_flags * 0.1, 0.3)
    return user_risk

def calculate_overall_context_score(platform_risk: str, temporal_factors: dict, geographic_risk: str, user_risk: float) -> float:
    score = 0.0
    if platform_risk == "high": score += 0.4
    elif platform_risk == "medium": score += 0.2
    score += temporal_factors.get('late_night_risk', 0.0)
    score += temporal_factors.get('weekend_risk', 0.0)
    score += temporal_factors.get('peak_hour_risk', 0.0)
    if geographic_risk == "high": score += 0.2
    score += user_risk
    return min(score, 1.0)

@app.post("/analyze")
async def analyze_context(request: ContextRequest):
    start_time = time.time()
    CONTEXT_REQUEST_COUNT.inc()
    
    try:
        with CONTEXT_PROCESSING_TIME.time():
            context_result = analyze_context_enhanced(request.context)
            processing_time = time.time() - start_time
            
            return ContextResponse(
                context_score=context_result['context_score'],
                platform_risk=context_result['platform_risk'],
                temporal_factors=context_result['temporal_factors'],
                geographic_risk=context_result['geographic_risk'],
                processing_time=processing_time
            )
    except Exception as e:
        return {"error": f"Context analysis failed: {str(e)}"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "context-analysis"}

@app.get("/metrics")
async def metrics():
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)