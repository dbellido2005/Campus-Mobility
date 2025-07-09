#!/bin/bash

# Load environment variables from .env file
export $(cat .env | xargs)

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000