from langchain_community.tools import BaseTool
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any, ClassVar
import requests
import json

class HTTPRequestInput(BaseModel):
    """Input for HTTP Request Tool."""
    tool_input: str = Field(description="A JSON string containing method, url, headers, and body")

class HTTPRequestTool(BaseTool):
    name: str = "http_request"
    description: str = """Useful for making HTTP requests to external APIs.
    The input should be a JSON string with these fields:
    - method: HTTP method (GET, POST, PUT, DELETE)
    - url: The URL to make the request to
    - headers: Optional headers dictionary
    - body: Optional request body for POST/PUT requests"""
    
    args_schema: type[HTTPRequestInput] = HTTPRequestInput

    def _run(self, tool_input: str) -> Dict[str, Any]:
        """Execute the HTTP request."""
        try:
            # Parse the input JSON
            params = json.loads(tool_input)
            method = params["method"].upper()
            url = params["url"]
            headers = params.get("headers", {})
            body = params.get("body")

            if method not in ["GET", "POST", "PUT", "DELETE"]:
                raise ValueError(f"Unsupported HTTP method: {method}")

            try:
                response = requests.request(
                    method=method,
                    url=str(url),
                    headers=headers or {},
                    json=body if body else None
                )
                
                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                }
                
            except requests.exceptions.RequestException as e:
                return {"error": str(e)}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON input"}
        except (KeyError, ValueError) as e:
            return {"error": str(e)}

    async def _arun(self, tool_input: str) -> Dict[str, Any]:
        """Execute the HTTP request asynchronously."""
        return self._run(tool_input) 