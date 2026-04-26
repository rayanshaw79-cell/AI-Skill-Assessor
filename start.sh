#!/bin/bash
# Start the FastAPI backend in the background
echo "Starting FastAPI backend on port 8000..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 &

# Wait a few seconds for the backend to initialize
sleep 5

# Start the Streamlit frontend in the foreground
# Hugging Face Spaces expects the app to be on port 7860
echo "Starting Streamlit frontend on port 7860..."
streamlit run frontend/app.py --server.port 7860 --server.address 0.0.0.0
