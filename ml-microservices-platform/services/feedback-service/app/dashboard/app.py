import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime


API_GATEWAY_URL = "http://orchestrator:8000"  
FEEDBACK_SERVICE_URL = "http://feedback-service:8006"  

st.set_page_config(
    page_title="Content Moderation Platform",
    page_icon="🛡️",
    layout="wide"
)

def main():
    st.title("🛡️ Content Moderation Dashboard")
    st.markdown("Monitor and interact with your microservices platform")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Live Analysis", "Service Health", "Feedback Stats", "Model Management"])
    
    with tab1:
        show_live_analysis()
    
    with tab2:
        show_service_health()
    
    with tab3:
        show_feedback_stats()
    
    with tab4:
        show_model_management()

def show_live_analysis():
    st.subheader("Test Content Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        text_content = st.text_area("Text Content", placeholder="Enter text to analyze...", height=100)
        uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
        
        if st.button("🚀 Analyze Content", type="primary"):
            if text_content or uploaded_file:
                analyze_content(text_content, uploaded_file)
            else:
                st.warning("Please provide text or image content")

    with col2:
        st.info("""
        **Microservices Flow:**
        1. **Orchestrator** (8000) - API Gateway & Routing
        2. **Image Service** (8001) - AWS Rekognition
        3. **Text Service** (8002) - AWS Comprehend  
        4. **Context Service** (8003) - Mismatch detection
        5. **Risk Service** (8004) - Confidence scoring
        6. **Fusion Service** (8005) - Final decision
        7. **Feedback Service** (8006) - Feedback & retraining
        """)

def analyze_content(text_content, uploaded_file):
    with st.spinner("Analyzing across microservices..."):
        try:
            files = {}
            data = {"text": text_content}
            
            if uploaded_file:
                files = {"image": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            
            response = requests.post(
                f"{API_GATEWAY_URL}/analyze",
                data=data,
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                display_results(result)
            else:
                st.error(f"Analysis failed: {response.text}")
                
        except Exception as e:
            st.error(f"Error calling API: {str(e)}")

def display_results(result):
    st.success("✅ Analysis Complete!")
    

    st.session_state.last_result = result
    
    risk_score = result.get('risk_score', 0)
    
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Risk Score", f"{risk_score:.2%}")
    
    with col2:
        if risk_score < 0.3:
            st.metric("Risk Level", "LOW")
        elif risk_score < 0.7:
            st.metric("Risk Level", "MEDIUM")
        else:
            st.metric("Risk Level", "HIGH")
    
    with col3:
        st.metric("Confidence", f"{result.get('confidence', 0):.2%}")
    
    st.progress(risk_score)
    
    
    with st.expander("📊 Detailed Results", expanded=True):
        if 'text_analysis' in result:
            st.subheader("Text Analysis")
            st.json(result['text_analysis'])
        
        if 'image_analysis' in result:
            st.subheader("Image Analysis") 
            st.json(result['image_analysis'])
        
        if 'context_analysis' in result:
            st.subheader("Context Analysis")
            st.json(result['context_analysis'])
    
    
    st.subheader("📝 Provide Feedback")
    feedback_col1, feedback_col2, feedback_col3 = st.columns(3)
    
    with feedback_col1:
        if st.button("✅ Analysis Correct", use_container_width=True):
            submit_feedback(st.session_state.last_result, True)
    
    with feedback_col2:
        if st.button("⚠️ Partial Match", use_container_width=True):
            submit_feedback(st.session_state.last_result, "partial")
    
    with feedback_col3:
        if st.button("❌ Analysis Incorrect", use_container_width=True):
            submit_feedback(st.session_state.last_result, False)

def submit_feedback(result, user_feedback):
    """Submit feedback to your FastAPI feedback service"""
    feedback_data = {
        "prediction_id": result.get('analysis_id', str(datetime.now().timestamp())),
        "user_feedback": user_feedback,
        "actual_risk_score": result.get('risk_score'),
        "corrected_flags": [],
        "metadata": result
    }
    
    try:
        response = requests.post(
            f"{FEEDBACK_SERVICE_URL}/feedback",
            json=feedback_data
        )
        
        if response.status_code == 200:
            st.success("✅ Feedback submitted successfully!")
            st.balloons()
        else:
            st.error(f"Failed to submit feedback: {response.text}")
    except Exception as e:
        st.error(f"Error submitting feedback: {str(e)}")

def show_service_health():
    st.subheader("Microservices Health Status")
    
    services = [
        {"name": "Orchestrator", "url": "http://orchestrator:8000/health"},
        {"name": "Image Service", "url": "http://image-service:8001/health"},
        {"name": "Text Service", "url": "http://text-service:8002/health"},
        {"name": "Context Service", "url": "http://context-service:8003/health"},
        {"name": "Risk Service", "url": "http://risk-service:8004/health"},
        {"name": "Fusion Service", "url": "http://fusion-service:8005/health"},
        {"name": "Feedback Service", "url": "http://feedback-service:8006/health"},
    ]
    
    healthy_count = 0
    for service in services:
        try:
            response = requests.get(service['url'], timeout=2)
            if response.status_code == 200:
                st.success(f"✅ {service['name']} - Healthy")
                healthy_count += 1
            else:
                st.error(f"❌ {service['name']} - Unhealthy")
        except:
            st.error(f"❌ {service['name']} - Offline")
    
    st.metric("Services Healthy", f"{healthy_count}/{len(services)}")

def show_feedback_stats():
    st.subheader("Feedback Statistics")
    
    try:
        response = requests.get(f"{FEEDBACK_SERVICE_URL}/feedback-stats")
        if response.status_code == 200:
            stats = response.json()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Feedback", stats['total_feedback_samples'])
            with col2:
                st.metric("Retraining Threshold", stats['retraining_threshold'])
            with col3:
                st.metric("Last Retraining", stats['last_retraining'])
            
            
            progress = min(stats['total_feedback_samples'] / stats['retraining_threshold'], 1.0)
            st.progress(progress)
            st.write(f"Progress towards retraining: {stats['total_feedback_samples']}/{stats['retraining_threshold']} samples")
            
        else:
            st.info("No feedback statistics available yet")
    except Exception as e:
        st.error(f"Could not fetch feedback stats: {str(e)}")

def show_model_management():
    st.subheader("Model Management")
    
    st.info("""
    **Auto-Retraining Features:**
    - Automatic retraining every 24 hours
    - Minimum 100 feedback samples required
    - Performance threshold: 85% accuracy
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Trigger Manual Retraining", type="primary"):
            try:
                response = requests.post(f"{FEEDBACK_SERVICE_URL}/retrain")
                if response.status_code == 200:
                    st.success("✅ Retraining started!")
                else:
                    st.error("Failed to trigger retraining")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("📊 View Retraining Metrics"):
            try:
                response = requests.get(f"{FEEDBACK_SERVICE_URL}/metrics")
                st.code(response.text)
            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()