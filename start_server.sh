#!/bin/bash
pip install -r requirements.txt
python -m uvicorn fastapi_server:app --host 0.0.0.0 --port $PORT
