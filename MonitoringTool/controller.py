""" Controller for the app using FastAPI. """

import json
import logging
from time import time
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

# FastAPI Setup
app = FastAPI(
    title="ANSSI Monitoring Tool",
    description="Monitoring Tool to track the availability of multiple external APIs",
    version="1.0",
    contact={
        "name": "API Support",
        "email": "nicolas.bogalheiro@gmail.com",
    }
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins= ["http://localhost:8000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
    max_age= 24 * 60 * 60  # One day
)

logger = logging.getLogger("uvicorn")

# Basic Middleware Setup
async def dispatch(request: Request, call_next):
    """ Middleware function for logging request details in the FastAPI application.

    This function is executed for every incoming HTTP request. It records the start time,
    processes the request, and logs the HTTP method, request URL, and the time taken.

    """
    start_time = time()
    response = await call_next(request)
    process_time = time() - start_time
    log_msg = (
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Process time: {process_time:.3f}s"
    )
    if response.status_code == 200:
        logger.info(log_msg)
    else:
        logger.error(log_msg)
    return response

app.add_middleware(BaseHTTPMiddleware, dispatch = dispatch)

# Custom Open API Tags Setup
tags_metadata = [
    {
        "name": "Endpoints",
        "description": "",
    }
]
app.openapi_tags = tags_metadata

# Gives access to static directory at the beginning
@app.on_event("startup")
def startup_event():
    """ Mounts the static directory to serve static files on startup.  
    """
    logger.info("Started API.")
    app.mount("/static", StaticFiles(directory="MonitoringTool/static"), name="static")
    logger.info("Mounted static files.")

@app.get("/", response_class=HTMLResponse, status_code=status.HTTP_200_OK,
description = "Home", tags = ["Endpoints"])
def index(request: Request):
    message = "Welcome to ANSSI Monitoring Tool !"
    return message
