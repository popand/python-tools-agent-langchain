from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

from internal.agent.agent import ToolsAgent, AgentConfig
from internal.tools.calculator import CalculatorTool
from internal.tools.http_request import HTTPRequestTool
from internal.tools.wikipedia import WikipediaTool
from internal.tools.code_execution import CodeExecutionTool

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Python Tools Agent",
    description="An extensible Python-based agent framework using LangChain",
    version="1.0.0"
)

class ExecuteRequest(BaseModel):
    input: str
    debug: Optional[bool] = False

class StepDetails(BaseModel):
    action: str
    input: str
    output: Any
    timestamp: Optional[str] = None
    thought: Optional[str] = None
    raw_log: Optional[str] = None

class FinalOutput(BaseModel):
    response: str
    confidence: float

class ResultDetails(BaseModel):
    final_output: FinalOutput
    steps: List[StepDetails]

class DebugInfo(BaseModel):
    final_thought: str
    total_steps: int
    raw_steps: List[Dict[str, Any]]

class ExecuteResponse(BaseModel):
    result: ResultDetails
    debug: Optional[DebugInfo] = None

# Initialize the agent
def create_agent():
    # Get configuration from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    system_message = os.getenv(
        "SYSTEM_MESSAGE",
        "You are a helpful assistant that can perform calculations, make HTTP requests, search Wikipedia, and execute code."
    )
    max_iterations = int(os.getenv("MAX_ITERATIONS", "5"))

    # Create tools
    tools = [
        CalculatorTool(),
        HTTPRequestTool(),
        WikipediaTool(),
        CodeExecutionTool()
    ]

    # Create agent configuration with debug and steps enabled
    config = AgentConfig(
        system_message=system_message,
        max_iterations=max_iterations,
        return_intermediate_steps=True,  # Always return steps
        debug=True,  # Enable verbose output
        temperature=0  # Ensure deterministic responses
    )

    # Create and return the agent
    return ToolsAgent(config, tools, openai_api_key)

# Create the agent instance
agent = create_agent()

@app.post("/execute", response_model=ExecuteResponse)
async def execute(request: ExecuteRequest):
    """Execute the agent with the given input."""
    try:
        response = await agent.execute(request.input, debug=request.debug)
        if "error" in response:
            raise HTTPException(status_code=400, detail=response["error"])
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset")
async def reset_memory():
    """Reset the agent's memory."""
    agent.reset_memory()
    return {"status": "ok"}

def main():
    """Run the FastAPI server."""
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main() 