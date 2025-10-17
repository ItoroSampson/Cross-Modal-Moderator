from fastapi import FastAPI
from pydantic import BaseModel
import time
from prometheus_client import Counter, Histogram, generate_latest

app = FastAPI(title="Risk Assessment Service")


RISK_REQUEST_COUNT = Counter('risk_requests_total', 'Total risk assessment requests')
RISK_PROCESSING_TIME = Histogram('risk_processing_seconds', 'Risk processing time')

class RiskRequest(BaseModel):
    image_analysis: dict
    text_analysis: dict

class RiskResponse(BaseModel):
    risk_score: float
    needs_review: bool
    explanation: str
    processing_time: float


SAFE_IMAGE_CATEGORIES = {'Family', 'Child', 'Person', 'Nature', 'Animal', 'People', 'Face', 'Portrait', 'Kid', 'Baby'}
UNSAFE_IMAGE_CATEGORIES = {'Weapon', 'Violence', 'Fire', 'Riot', 'Protest', 'Drugs', 'Alcohol'}

def assess_risk(image, text):
    """EXACT COPY FROM MY LAMBDA - My core risk assessment logic"""
    risk = 0.0
    
 
    image_safe = any(cat in SAFE_IMAGE_CATEGORIES for cat in image['categories'])
    image_unsafe = any(cat in UNSAFE_IMAGE_CATEGORIES for cat in image['categories'])
    has_unsafe_words = len(text['unsafe_found']) > 0
    
    
    if image_safe and has_unsafe_words:
        risk += 0.6  
        print(f"🚨 CONTEXTUAL MISMATCH: Safe image with unsafe words: {text['unsafe_found']}")
    
     
    if image_unsafe and text['sentiment'] == 'POSITIVE':
        risk += 0.5
        print(f"🚨 CONTEXTUAL MISMATCH: Unsafe image with positive text")
    
    
    if has_unsafe_words:
        risk += 0.3
        print(f"⚠️ UNSAFE WORDS DETECTED: {text['unsafe_found']}")
    
    if image['moderation_flagged']:
        risk += 0.4
        print(f"⚠️ IMAGE MODERATION FLAGGED: {image.get('moderation_labels', [])}")
    
    if text['sentiment'] == 'NEGATIVE':
        risk += 0.2
        print(f"📝 NEGATIVE SENTIMENT DETECTED")
    
    
    if image_safe and text['sentiment'] == 'POSITIVE' and not has_unsafe_words:
        risk -= 0.3  
        risk = max(risk, 0.0)  
        print(f"✅ CONTEXTUALLY ALIGNED: Safe image with positive text")
    
    
    final_risk = min(max(risk, 0.0), 1.0)
    print(f"🎯 FINAL RISK SCORE: {final_risk}")
    
    return final_risk

def generate_explanation(risk_score, image, text):
    """EXACT COPY FROM MY LAMBDA - Explanation generation"""
    if risk_score > 0.7:
        return "High risk: Potential deceptive or harmful content detected"
    elif risk_score > 0.4:
        return "Medium risk: Content requires careful review"
    elif risk_score > 0.1:
        return "Low risk: Generally safe with minor concerns"
    else:
        return "Very low risk: Content appears safe and contextually aligned"

@app.post("/assess")
async def assess_risk_endpoint(request: RiskRequest):
    start_time = time.time()
    RISK_REQUEST_COUNT.inc()
    
    try:
        with RISK_PROCESSING_TIME.time():
            
            risk_score = assess_risk(request.image_analysis, request.text_analysis)
            explanation = generate_explanation(risk_score, request.image_analysis, request.text_analysis)
            
            processing_time = time.time() - start_time
            
            return RiskResponse(
                risk_score=risk_score,
                needs_review=risk_score > 0.6,  
                explanation=explanation,
                processing_time=processing_time
            )
            
    except Exception as e:
        return {"error": f"Risk assessment failed: {str(e)}"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "risk-assessment"}

@app.get("/metrics")
async def metrics():
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)