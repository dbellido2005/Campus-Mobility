#!/bin/bash

# Load environment variables from .env file (skip comments and empty lines)
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
