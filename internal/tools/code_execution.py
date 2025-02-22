from langchain_community.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import subprocess
import tempfile
import os
import json

class CodeExecutionInput(BaseModel):
    """Input for Code Execution Tool."""
    tool_input: str = Field(description="A JSON string containing code, language, and optional timeout")

class CodeExecutionTool(BaseTool):
    name: str = "code_execution"
    description: str = """Useful for executing code snippets.
    The input should be a JSON string with these fields:
    - code: The code to execute
    - language: Programming language (currently only supports "python")
    - timeout: Optional timeout in seconds (default: 10)"""
    
    args_schema: type[CodeExecutionInput] = CodeExecutionInput

    def _run(self, tool_input: str) -> Dict[str, Any]:
        """Execute the code snippet."""
        try:
            # Parse the input JSON
            params = json.loads(tool_input)
            code = params["code"]
            language = params.get("language", "python")
            timeout = int(params.get("timeout", 10))

            if language.lower() != "python":
                return {
                    "error": f"Unsupported language: {language}. Only Python is currently supported."
                }

            try:
                # Create a temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                    temp_file.write(code)
                    temp_file_path = temp_file.name

                try:
                    # Execute the code
                    result = subprocess.run(
                        ['python', temp_file_path],
                        capture_output=True,
                        text=True,
                        timeout=timeout
                    )

                    return {
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "exit_code": result.returncode
                    }

                except subprocess.TimeoutExpired:
                    return {
                        "error": f"Code execution timed out after {timeout} seconds"
                    }
                except subprocess.CalledProcessError as e:
                    return {
                        "error": f"Code execution failed: {str(e)}",
                        "stdout": e.stdout,
                        "stderr": e.stderr,
                        "exit_code": e.returncode
                    }
                finally:
                    # Clean up the temporary file
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass

            except Exception as e:
                return {"error": str(e)}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON input"}
        except (KeyError, ValueError) as e:
            return {"error": str(e)}

    async def _arun(self, tool_input: str) -> Dict[str, Any]:
        """Execute the code snippet asynchronously."""
        return self._run(tool_input) 