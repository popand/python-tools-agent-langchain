from typing import Dict, Any, List, Type
import yaml
import importlib
from pathlib import Path
from pydantic import BaseModel
from langchain_community.tools import BaseTool

class ToolConfig(BaseModel):
    """Configuration for a single tool."""
    enabled: bool = True
    type: str
    config: Dict[str, Any] = {}

class ToolsConfig(BaseModel):
    """Configuration for all tools."""
    tools: Dict[str, ToolConfig]

class ToolLoader:
    """Loader for tool configurations."""
    
    @staticmethod
    def load_config(config_path: str) -> ToolsConfig:
        """Load tool configurations from a YAML file."""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            return ToolsConfig(**config_data)
    
    @staticmethod
    def import_class(class_path: str) -> Type:
        """Import a class from a string path."""
        module_path, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    
    @classmethod
    def load_tools(cls, config_path: str) -> List[BaseTool]:
        """Load and initialize tools from configuration."""
        config = cls.load_config(config_path)
        tools = []
        
        for tool_name, tool_config in config.tools.items():
            if not tool_config.enabled:
                continue
                
            try:
                # Import the tool class
                tool_class = cls.import_class(tool_config.type)
                
                # Initialize the tool with configuration
                tool = tool_class(**tool_config.config)
                tools.append(tool)
                
            except Exception as e:
                print(f"Error loading tool {tool_name}: {str(e)}")
                continue
        
        return tools

    @staticmethod
    def get_default_config_path() -> str:
        """Get the default configuration path."""
        return str(Path(__file__).parent.parent.parent / 'config' / 'tools.yaml') 