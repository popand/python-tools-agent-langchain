from langchain_community.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import subprocess
import tempfile
import os
import json
import sys
import shutil

class CodeExecutionInput(BaseModel):
    """Input for Code Execution Tool."""
    tool_input: str = Field(description="A JSON string containing code, language, and optional timeout")

class CodeExecutionConfig(BaseModel):
    """Configuration for Code Execution Tool."""
    timeout: int = 10
    max_memory_mb: int = 512
    allowed_modules: List[str] = ["math", "numpy", "pandas"]
    disable_subprocess: bool = True
    disable_file_access: bool = True
    disable_network_access: bool = True

class CodeExecutionTool(BaseTool):
    name: str = "code_execution"
    description: str = """Useful for executing code snippets.
    The input should be a JSON string with these fields:
    - code: The code to execute
    - language: Programming language (currently only supports "python")
    - timeout: Optional timeout in seconds (default: 10)"""
    
    args_schema: type[CodeExecutionInput] = CodeExecutionInput
    
    # Tool configuration
    config: CodeExecutionConfig = Field(default_factory=CodeExecutionConfig)
    python_executable: str = Field(default_factory=lambda: sys.executable)
    
    def __init__(self, **kwargs):
        # Extract configuration parameters
        config_params = {
            'timeout': kwargs.pop('timeout', 10),
            'max_memory_mb': kwargs.pop('max_memory_mb', 512),
            'allowed_modules': kwargs.pop('allowed_modules', ['math', 'numpy', 'pandas']),
            'disable_subprocess': kwargs.pop('disable_subprocess', True),
            'disable_file_access': kwargs.pop('disable_file_access', True),
            'disable_network_access': kwargs.pop('disable_network_access', True)
        }
        
        # Initialize parent class
        super().__init__(**kwargs)
        
        # Set configuration
        self.config = CodeExecutionConfig(**config_params)
        
        # Find Python executable
        self.python_executable = self._get_python_executable()
    
    def _get_python_executable(self) -> str:
        """Get the Python executable path."""
        # First try the current Python interpreter
        if sys.executable and os.path.exists(sys.executable):
            return sys.executable
        
        # Then try common Python commands
        for cmd in ['python3', 'python']:
            path = shutil.which(cmd)
            if path:
                return path
        
        raise ValueError("Could not find Python executable")

    def _validate_imports(self, code: str) -> bool:
        """Validate that only allowed modules are imported."""
        import ast
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for name in node.names:
                        module = name.name.split('.')[0]
                        if module not in self.config.allowed_modules:
                            return False
            return True
        except:
            return False

    def _run(self, tool_input: str) -> Dict[str, Any]:
        """Execute the code snippet."""
        try:
            # Parse the input JSON
            params = json.loads(tool_input)
            code = params["code"]
            timeout = int(params.get("timeout", self.config.timeout))

            # Validate imports
            if not self._validate_imports(code):
                return {
                    "error": f"Code contains unauthorized imports. Allowed modules: {', '.join(self.config.allowed_modules)}"
                }

            try:
                # Create a temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                    # Add print statement if the code doesn't have one
                    if not any(line.strip().startswith('print(') for line in code.splitlines()):
                        code += "\nprint(result)"
                    
                    temp_file.write(code)
                    temp_file_path = temp_file.name

                try:
                    # Execute the code with resource limits
                    result = subprocess.run(
                        [self.python_executable, temp_file_path],
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        env={
                            **os.environ,
                            'PYTHONPATH': os.getcwd(),  # Add current directory to Python path
                            'MALLOC_ARENA_MAX': '2',  # Limit memory fragmentation
                            'PYTHONMALLOC': 'malloc',  # Use system malloc
                            'PYTHONIOENCODING': 'utf-8'  # Ensure proper encoding
                        }
                    )

                    response = {
                        "stdout": result.stdout.strip() if result.stdout else None,
                        "stderr": result.stderr.strip() if result.stderr else None,
                        "exit_code": result.returncode
                    }

                    # Only include non-empty fields
                    return {k: v for k, v in response.items() if v is not None}

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
                return {"error": f"Execution error: {str(e)}"}
                
        except json.JSONDecodeError:
            return {"error": "Invalid JSON input"}
        except (KeyError, ValueError) as e:
            return {"error": str(e)}

    async def _arun(self, tool_input: str) -> Dict[str, Any]:
        """Execute the code snippet asynchronously."""
        return self._run(tool_input) 