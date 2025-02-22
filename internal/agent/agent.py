from typing import List, Dict, Any, Optional
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_community.tools import BaseTool
from pydantic import BaseModel

class AgentConfig(BaseModel):
    """Configuration for the Tools Agent."""
    system_message: str
    max_iterations: int = 5
    return_intermediate_steps: bool = True
    temperature: float = 0
    memory_key: str = "chat_history"
    debug: bool = False

class ToolsAgent:
    def __init__(
        self,
        config: AgentConfig,
        tools: List[BaseTool],
        openai_api_key: str
    ):
        """Initialize the Tools Agent with configuration and tools."""
        self.config = config
        self.tools = tools
        
        # Initialize the language model
        self.llm = ChatOpenAI(
            temperature=config.temperature,
            openai_api_key=openai_api_key
        )
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key=config.memory_key,
            return_messages=True
        )
        
        # Initialize the agent with return_intermediate_steps always True
        self.agent = initialize_agent(
            tools=tools,
            llm=self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,  # Always enable verbose for capturing steps
            max_iterations=config.max_iterations,
            system_message=config.system_message,
            return_intermediate_steps=True  # Always return steps
        )
    
    async def execute(self, input_text: str, debug: bool = False) -> Dict[str, Any]:
        """Execute the agent with the given input."""
        try:
            # Run the agent with return_intermediate_steps=True
            agent_response = await self.agent.ainvoke(
                {"input": input_text},
                include_run_info=True
            )
            
            # Extract the final output and steps
            result = agent_response.get("output", "")
            steps = agent_response.get("intermediate_steps", [])
            
            # Initialize response structure
            response = {
                "result": {
                    "final_output": {
                        "response": result,
                        "confidence": 1.0  # TODO: Implement confidence scoring
                    },
                    "steps": []
                }
            }
            
            # Process steps
            if steps:
                processed_steps = []
                for step in steps:
                    # Each step is a tuple of (action, observation)
                    action = step[0]
                    observation = step[1]
                    
                    step_entry = {
                        "action": action.tool,
                        "input": action.tool_input,
                        "output": observation,
                        "timestamp": action.timestamp if hasattr(action, "timestamp") else None
                    }
                    
                    # Add debug information if requested
                    if debug:
                        step_entry.update({
                            "thought": action.log.split("\nAction:")[0].replace("Thought: ", "").strip() if hasattr(action, "log") else None,
                            "raw_log": action.log if hasattr(action, "log") else None
                        })
                    
                    processed_steps.append(step_entry)
                
                response["result"]["steps"] = processed_steps
                
                # Add debug information if requested
                if debug:
                    response["debug"] = {
                        "final_thought": result,
                        "total_steps": len(processed_steps),
                        "raw_steps": [
                            {
                                "thought": step[0].log.split("\nAction:")[0].replace("Thought: ", "").strip() if hasattr(step[0], "log") else None,
                                "action": step[0].tool,
                                "action_input": step[0].tool_input,
                                "observation": step[1]
                            }
                            for step in steps
                        ]
                    }
            
            return response
            
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def reset_memory(self):
        """Reset the agent's memory."""
        self.memory.clear() 