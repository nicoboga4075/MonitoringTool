""" Controller for the app using FastAPI. """

import json
import logging
import requests
from datetime import datetime
from time import time
from uuid import uuid4
from fastapi import FastAPI, Request, HTTPException, Form, status
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
    request.state.process_time = process_time
    log_msg = (
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Process time: {process_time:.3f}s"
    )
    if response.status_code in [200, 201, 204, 301, 302, 303, 304]:
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
"url": "https://jsonplaceholder.typicode.com/todos",
"method": "GET",
"expected_status": 200,
"last_check": "2024-01-15T10:30:00Z",
"last_status": 200,
"is_healthy": True
}]

status_endpoints = {"uuid": [True]}

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
def add_endpoint(request: Request, name = Form(...), url = Form(...), method = Form("GET"), expected_status = Form(200)):
    try:
        id_endpoint = str(uuid4())
        endpoint = models.EndpointInfo(
            id= id_endpoint,
            name=name,
            url=url,
            method=method,
            expected_status=expected_status
        )
        endpoints.append({"id": id_endpoint, **endpoint.dict()})
        status_endpoints[id_endpoint] = []
    except Exception as e:
        logger.error(f"Error while creating endpoint: {e}")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(e)})
    if "text/html" in request.headers.get("accept", ""):
        return RedirectResponse("/api/endpoints", status_code=status.HTTP_301_MOVED_PERMANENTLY)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"id": id_endpoint, **endpoint.dict()})

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
    start_req = time()
    try:
        # Find the endpoint by ID
        matches = [ep for ep in endpoints if ep["id"] == id]
        if not matches:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endpoint with id {id} not found")
        endpoint = matches[0]
        response = requests.get(endpoint["url"])
        status_code = response.status_code
        status_endpoint = status_code == endpoint["expected_status"]
        # Update the status of the endpoint
        endpoints[endpoints.index(endpoint)]["is_healthy"] = status_endpoint
        endpoints[endpoints.index(endpoint)]["last_status"] = status_code
        endpoints[endpoints.index(endpoint)]["last_check"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        status_endpoints[endpoint["id"]].append(status_endpoint)
        # Response time calculation
        response_time = time() - start_req
        logger.info(f"Checked endpoint {endpoint["url"]}: {status_code} - Healthy: {status_endpoint}")
        return JSONResponse(status_code=status.HTTP_200_OK, content = {"endpoint":endpoint, "response_time": f"{response_time:.3f}s"})
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Error checking endpoint {id}: {str(e)}"}
        )

@app.get("/api/endpoints/{id}/history", status_code=status.HTTP_200_OK,
description = "Get the last 10 statuses of an endpoint", tags = ["Endpoints"])
def get_endpoint_history(request: Request, id: str):
    """ Returns the last 10 statuses of an endpoint.
    This endpoint retrieves the last 10 status checks for a specific endpoint,
    providing insight into its availability and performance over time.
    """
    matches = [ep for ep in endpoints if ep["id"] == id]
    if not matches:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endpoint with id {id} not found")
    endpoint = models.EndpointInfo(**matches[0])
    checks = status_endpoints.get(id,[])[-10:]
    if "text/html" in request.headers.get("accept", ""):
        return views.HistoryView().render(request, checks=checks)
    return checks
