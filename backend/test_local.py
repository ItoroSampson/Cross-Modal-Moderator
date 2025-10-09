# test_local.py
import boto3
import json
import base64


TEST_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
TEST_TEXT = "This is a family photo with children playing"

def test_moderation():
    try:
        
        rekognition = boto3.client('rekognition', region_name='us-east-1')
        comprehend = boto3.client('comprehend', region_name='us-east-1')
        
        print("🔄 Testing Rekognition...")
        
        image_bytes = base64.b64decode(TEST_IMAGE)
        labels = rekognition.detect_labels(Image={'Bytes': image_bytes}, MaxLabels=5)
        print("✅ Rekognition works! Labels:", [label['Name'] for label in labels['Labels']])
        
        print("🔄 Testing Comprehend...")
        
        sentiment = comprehend.detect_sentiment(Text=TEST_TEXT, LanguageCode='en')
        print("✅ Comprehend works! Sentiment:", sentiment['Sentiment'])
        
        print("🎉 ALL AWS SERVICES ARE WORKING!")
        return True
        
    except Exception as e:
        print(f"❌ AWS Service Error: {e}")
        print("💡 Check your AWS credentials with: aws configure list")
        return False

if __name__ == "__main__":
    test_moderation()