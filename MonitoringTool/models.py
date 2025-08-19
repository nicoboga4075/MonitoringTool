""" Models for the app """
from pydantic import BaseModel, Field

class EndpointInfo(BaseModel):
    """ Representation of an endpoint """
    id: str = Field(..., exclude=True)
    name: str = Field(..., min_length=10, max_length=100)
    url: str
    method: str = Field(default="GET", pattern="^(GET|POST)$")
    expected_status: int = Field(default=200, ge=100, le=599)
    last_check : str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
    last_status: int = Field(..., ge=100, le=599)
    is_healthy: bool = Field(default=False)
