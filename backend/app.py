import boto3
import json
import base64
import uuid
import os
import decimal
from datetime import datetime


rekognition = boto3.client('rekognition', region_name='us-east-1')
comprehend = boto3.client('comprehend', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('ContentModerationResults')


UNSAFE_WORDS = {
    'kill', 'murder', 'bomb', 'terrorist', 'weapon', 'gun', 'attack', 
    'racist', 'hate', 'porn', 'violent', 'protest', 'riot', 'assault',
    'weapons', 'violence', 'harm', 'danger', 'threat', 'death', 'dead',
    'suicide', 'bombing', 'explosion', 'shoot', 'shooting', 'hostage',
    'terrorism', 'extremist', 'radical', 'abuse', 'assault', 'rape',
    'pedophile', 'child abuse', 'molest', 'blackmail', 'extortion'
}

SAFE_WORDS = {'family', 'education', 'health', 'safety', 'community', 'peace'}

def lambda_handler(event, context):
    try:
        body = json.loads(event['body']) if 'body' in event else event
        
        if not body.get('image') or not body.get('text'):
            return error_response("Need image and text")
        
        
        image_b64 = body['image'].strip()
        
        
        missing_padding = len(image_b64) % 4
        if missing_padding:
            image_b64 += '=' * (4 - missing_padding)
        
        try:
            image_bytes = base64.b64decode(image_b64)
        except Exception as e:
            return error_response(f"Invalid image data: {str(e)}")
        
        image_result = analyze_image(image_bytes)
        text_result = analyze_text(body['text'])
        risk_score = assess_risk(image_result, text_result)
        
        analysis_id = f"mod_{uuid.uuid4().hex[:8]}"
        

        item = {
            'analysis_id': analysis_id,
            'timestamp': datetime.utcnow().isoformat(),
            'risk_score': decimal.Decimal(str(risk_score)),
            'needs_review': risk_score > 0.6,
            'image_categories': image_result['categories'][:3],
            'text_sentiment': text_result['sentiment'],
            'unsafe_words_found': text_result['unsafe_found'],
            'moderation_flagged': image_result['moderation_flagged'],
            'explanation': generate_explanation(risk_score, image_result, text_result)
        }
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'analysis_id': analysis_id,
                'risk_score': risk_score,
                'needs_review': risk_score > 0.6,
                'image_categories': image_result['categories'][:3],
                'text_sentiment': text_result['sentiment'],
                'unsafe_found': text_result['unsafe_found'],
                'explanation': generate_explanation(risk_score, image_result, text_result)
            })
        }
        
    except Exception as e:
        return error_response(str(e))

def analyze_image(image_bytes):
    labels = rekognition.detect_labels(Image={'Bytes': image_bytes}, MaxLabels=10, MinConfidence=60)
    moderation = rekognition.detect_moderation_labels(Image={'Bytes': image_bytes}, MinConfidence=50)
    
    return {
        'categories': [label['Name'] for label in labels['Labels']],
        'moderation_flagged': len(moderation['ModerationLabels']) > 0,
        'moderation_labels': [label['Name'] for label in moderation['ModerationLabels']]
    }

def analyze_text(text):
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

def assess_risk(image, text):
    risk = 0.0
    
    
    SAFE_IMAGE_CATEGORIES = {'Family', 'Child', 'Person', 'Nature', 'Animal', 'People', 'Face', 'Portrait', 'Kid', 'Baby'}
    UNSAFE_IMAGE_CATEGORIES = {'Weapon', 'Violence', 'Fire', 'Riot', 'Protest', 'Drugs', 'Alcohol'}
    
    # 1. CONTEXTUAL MISMATCH DETECTION 
    image_safe = any(cat in SAFE_IMAGE_CATEGORIES for cat in image['categories'])
    image_unsafe = any(cat in UNSAFE_IMAGE_CATEGORIES for cat in image['categories'])
    has_unsafe_words = len(text['unsafe_found']) > 0
    
    
    if image_safe and has_unsafe_words:
        risk += 0.6  
        print(f"🚨 CONTEXTUAL MISMATCH: Safe image with unsafe words: {text['unsafe_found']}")
    
      
    if image_unsafe and text['sentiment'] == 'POSITIVE':
        risk += 0.5
        print(f"🚨 CONTEXTUAL MISMATCH: Unsafe image with positive text")
    
    # 2. INDIVIDUAL RISK FACTORS
    if has_unsafe_words:
        risk += 0.3
        print(f"⚠️ UNSAFE WORDS DETECTED: {text['unsafe_found']}")
    
    if image['moderation_flagged']:
        risk += 0.4
        print(f"⚠️ IMAGE MODERATION FLAGGED: {image.get('moderation_labels', [])}")
    
    if text['sentiment'] == 'NEGATIVE':
        risk += 0.2
        print(f"📝 NEGATIVE SENTIMENT DETECTED")
    
    # 3. CONTEXTUAL ALIGNMENT BONUS (REDUCE RISK)
    if image_safe and text['sentiment'] == 'POSITIVE' and not has_unsafe_words:
        risk -= 0.3  
        risk = max(risk, 0.0)  
        print(f"✅ CONTEXTUALLY ALIGNED: Safe image with positive text")
    
    
    final_risk = min(max(risk, 0.0), 1.0)
    print(f"🎯 FINAL RISK SCORE: {final_risk}")
    
    return final_risk

def generate_explanation(risk_score, image, text):
    if risk_score > 0.7:
        return "High risk: Potential deceptive or harmful content detected"
    elif risk_score > 0.4:
        return "Medium risk: Content requires careful review"
    elif risk_score > 0.1:
        return "Low risk: Generally safe with minor concerns"
    else:
        return "Very low risk: Content appears safe and contextually aligned"

def error_response(message):
    return {
        'statusCode': 400,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': message})
    }