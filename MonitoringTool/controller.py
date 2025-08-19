""" Controller for the app using FastAPI. """

import json
import logging
from time import time
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from MonitoringTool import models, views

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

@app.get("/", include_in_schema = False)
def index(request: Request):
    return RedirectResponse(url="/api/endpoints", status_code = status.HTTP_301_MOVED_PERMANENTLY)

endpoints = [{
"id": "uuid",
"name": "API Production",
"url": "https://api.example.com/health",
"method": "GET",
"expected_status": 200,
"last_check": "2024-01-15T10:30:00Z",
"last_status": 200,
"is_healthy": True
}]

@app.get("/api/endpoints", response_model=list[models.EndpointInfo], status_code=status.HTTP_200_OK,
description = "Get all endpoints", tags = ["Endpoints"])
def get_endpoints(request: Request):
    """ Returns a list of all monitored endpoints.
    This endpoint retrieves all endpoints that are currently being monitored
    and returns them in a JSON format.
    """
    if "text/html" in request.headers.get("accept", ""):
        return views.ResultsView().render(request, results=[models.EndpointInfo(**ep) for ep in endpoints])
    return endpoints

@app.post("/api/endpoints", status_code=status.HTTP_201_CREATED,
description = "Add a new endpoint", tags = ["Endpoints"])
def add_endpoint(request: Request, endpoint: models.EndpointInfo):
    """ Adds a new endpoint to be monitored.
    This endpoint allows the user to add a new endpoint by providing its details.
    The endpoint will be monitored for availability and status.
    """
    pass

@app.delete("/api/endpoints/{id}", status_code=status.HTTP_204_NO_CONTENT,
description = "Delete an endpoint", tags = ["Endpoints"])
def delete_endpoint(request: Request, id: str):
    """ Deletes an endpoint from monitoring.
    This endpoint allows the user to delete an existing endpoint by its ID.
    The endpoint will no longer be monitored for availability and status.
    """
    for index, ep in enumerate(endpoints):
        if ep["id"] == id:
            endpoints.pop(index)
            break
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

@app.get("/api/endpoints/{id}/check", status_code=status.HTTP_200_OK,
description = "Check an endpoint immediately", tags = ["Endpoints"])
def check_endpoint(request: Request, id: str):
    """ Checks an endpoint immediately.
    This endpoint allows the user to trigger an immediate check of an endpoint's availability
    and status, returning the updated information.
    """
    pass

@app.get("/api/endpoints/{id}/history", response_model=list[models.EndpointInfo], status_code=status.HTTP_200_OK,
description = "Get the last 10 statuses of an endpoint", tags = ["Endpoints"])
def get_endpoint_history(request: Request, id: str):
    """ Returns the last 10 statuses of an endpoint.
    This endpoint retrieves the last 10 status checks for a specific endpoint,
    providing insight into its availability and performance over time.
    """
    pass
