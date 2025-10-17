from fastapi import FastAPI
from pydantic import BaseModel
import boto3
import time
from prometheus_client import Counter, Histogram, generate_latest

app = FastAPI(title="Text Analysis Service")


TEXT_REQUEST_COUNT = Counter('text_requests_total', 'Total text analysis requests')
TEXT_PROCESSING_TIME = Histogram('text_processing_seconds', 'Text processing time')

class TextRequest(BaseModel):
    text_content: str

class TextResponse(BaseModel):
    sentiment: str
    unsafe_found: list
    sentiment_scores: dict
    processing_time: float


UNSAFE_WORDS = {
    'kill', 'murder', 'bomb', 'terrorist', 'weapon', 'gun', 'attack', 
    'racist', 'hate', 'porn', 'violent', 'protest', 'riot', 'assault',
    'weapons', 'violence', 'harm', 'danger', 'threat', 'death', 'dead',
    'suicide', 'bombing', 'explosion', 'shoot', 'shooting', 'hostage',
    'terrorism', 'extremist', 'radical', 'abuse', 'assault', 'rape',
    'pedophile', 'child abuse', 'molest', 'blackmail', 'extortion'
}


comprehend = boto3.client('comprehend', region_name='us-east-1')

def analyze_text(text):
    """EXACT COPY FROM YOUR LAMBDA - Text analysis logic"""
    sentiment = comprehend.detect_sentiment(Text=text, LanguageCode='en')
    text_lower = text.lower()
    
    
    unsafe_found = []
    for word in UNSAFE_WORDS:
        if f' {word} ' in f' {text_lower} ':
            unsafe_found.append(word)
    
    return {
        'sentiment': sentiment['Sentiment'],
        'unsafe_found': unsafe_found,
        'sentiment_scores': sentiment['SentimentScore']
    }

@app.post("/analyze")
async def analyze_text_endpoint(request: TextRequest):
    start_time = time.time()
    TEXT_REQUEST_COUNT.inc()
    
    try:
        with TEXT_PROCESSING_TIME.time():
            
            text_result = analyze_text(request.text_content)
            
            processing_time = time.time() - start_time
            
            return TextResponse(
                sentiment=text_result['sentiment'],
                unsafe_found=text_result['unsafe_found'],
                sentiment_scores=text_result['sentiment_scores'],
                processing_time=processing_time
            )
            
    except Exception as e:
        return {"error": f"Text processing failed: {str(e)}"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "text-analysis"}

@app.get("/metrics")
async def metrics():
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)