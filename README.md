# Python Tools Agent with LangChain

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)](https://openai.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.0%2B-blue.svg)](https://python.langchain.com)

An extensible Python-based agent framework that combines OpenAI's GPT-4 capabilities with LangChain for practical tools and real-world tasks. Built with modern Python features, FastAPI, and LangChain's agent system, this framework provides a robust foundation for building AI-powered tools.

## Features

- LangChain-based agent system with custom tools:
  - **Calculator**: Perform basic mathematical operations (add, subtract, multiply, divide)
  - **HTTP Request**: Make HTTP requests to external APIs (GET, POST, PUT, DELETE)
  - **Wikipedia**: Search and retrieve information from Wikipedia in multiple languages
  - **Code Execution**: Execute Python code snippets with safety controls
- FastAPI-based REST API with Swagger UI documentation
- Async/await support throughout
- Conversation memory management with state persistence
- Configurable system messages and behavior
- Environment-based configuration
- Proper error handling and reporting
- Debug mode with detailed execution logs

## Tool Capabilities

### Calculator Tool
- Supports basic arithmetic operations: add, subtract, multiply, divide
- Input validation and error handling
- Protection against division by zero
- Returns structured results with error messages when needed

Example input:
```json
{
    "input": "Calculate 15 divided by 3 and multiply the result by 4"
}
```

### HTTP Request Tool
- Supports all major HTTP methods: GET, POST, PUT, DELETE
- Custom header support
- JSON body support for POST/PUT requests
- Automatic handling of JSON responses
- Error handling for network issues

Example input:
```json
{
    "input": "Make a GET request to https://api.github.com/repos/python/cpython"
}
```

### Wikipedia Tool
- Search Wikipedia articles
- Multi-language support
- Article summaries and full content
- Disambiguation handling
- Page metadata (URL, ID, etc.)

Example input:
```json
{
    "input": "Search Wikipedia for information about Python programming language"
}
```

### Code Execution Tool
- Execute Python code snippets
- Configurable timeout protection
- Sandbox execution
- Capture stdout/stderr
- Error handling and reporting

Example input:
```json
{
    "input": "Write and execute a Python script that calculates the first 10 Fibonacci numbers"
}
```

## Requirements

- Python 3.9 or later
- OpenAI API key (GPT-4 access required)
- Dependencies:
  - langchain>=0.3.0
  - langchain-community>=0.3.0
  - langchain-openai>=0.3.0
  - openai>=1.0.0
  - python-dotenv>=1.0.0
  - fastapi>=0.100.0
  - uvicorn>=0.20.0
  - pydantic>=2.0.0
  - wikipedia>=1.4.0
  - requests>=2.31.0

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/python-tools-agent-langchain.git
cd python-tools-agent-langchain
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up configuration:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

The `.env` file should contain:
```env
# Required
OPENAI_API_KEY=your-api-key-here

# Optional
SYSTEM_MESSAGE="You are a helpful assistant that can perform calculations, make HTTP requests, search Wikipedia, and execute code."
MAX_ITERATIONS=5  # Maximum number of tool execution iterations per request
PORT=8080        # Server port (default: 8080)
```

## API Usage

1. Start the API server:
```bash
PYTHONPATH=. python3 cmd/server/main.py
```

2. Access the API documentation:
   - Swagger UI: http://localhost:8080/docs
   - ReDoc: http://localhost:8080/redoc
   - OpenAPI Spec: http://localhost:8080/openapi.json

3. Available Endpoints:
   - POST `/execute`: Execute the agent with a given input
   - POST `/reset`: Reset the agent's memory

4. Make requests to the API:

```bash
# Basic request
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Calculate 15 divided by 3 and multiply the result by 4"
  }'

# Debug mode
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Calculate 15 divided by 3 and multiply the result by 4",
    "debug": true
  }'
```

## Architecture

The system consists of several components:

- **Agent**: Core LangChain agent implementation
  - Uses CONVERSATIONAL_REACT_DESCRIPTION agent type
  - Manages tool selection and execution
  - Maintains conversation context
  - Handles multi-step reasoning
- **Tools**: Custom LangChain tools
  - Each tool accepts a single JSON string input
  - Input validation using Pydantic models
  - Structured error handling
  - Async support
- **API**: FastAPI-based REST interface
  - Async request handling
  - Interactive Swagger UI documentation
  - Request/response validation
  - Error handling
- **Memory**: Conversation state management
  - Maintains chat history
  - Allows for context-aware responses
  - Can be reset as needed

## Adding New Tools

To add a new tool:

1. Create a new file in the `internal/tools` directory
2. Implement a new tool class inheriting from `BaseTool`
3. Add input validation using Pydantic models
4. Register the tool in `cmd/server/main.py`

Example:
```python
from langchain_community.tools import BaseTool
from pydantic import BaseModel, Field
import json

class YourToolInput(BaseModel):
    """Input schema for your tool."""
    tool_input: str = Field(description="A JSON string containing your tool's parameters")

class YourTool(BaseTool):
    name: str = "your_tool"
    description: str = """Description of your tool.
    The input should be a JSON string with these fields:
    - param1: description of param1
    - param2: description of param2"""
    
    args_schema: type[YourToolInput] = YourToolInput

    def _run(self, tool_input: str) -> dict:
        try:
            # Parse the input JSON
            params = json.loads(tool_input)
            # Implement your tool logic here
            return {"result": "success"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON input"}
        except Exception as e:
            return {"error": str(e)}

    async def _arun(self, tool_input: str) -> dict:
        return self._run(tool_input)
```

## Security Considerations

- Never commit your `.env` file or API keys
- Use environment-specific configurations
- Validate and sanitize all inputs
- Implement rate limiting for API endpoints
- Be cautious with code execution:
  - Set appropriate timeouts
  - Run in isolated environments
  - Limit available Python modules
  - Monitor resource usage
- Use HTTPS in production
- Implement authentication if needed
- Keep dependencies updated

## Error Handling

The service provides structured error handling:

- Input validation errors (400 Bad Request)
- Tool execution errors (captured in response)
- System errors (500 Internal Server Error)
- Memory management errors
- API rate limiting errors
- Timeout errors

Each error response includes:
- Error message
- Error type
- Additional context when available

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

Please ensure:
- Code follows the project style
- All tests pass
- Documentation is updated
- Changes are backward compatible

## License

MIT License 