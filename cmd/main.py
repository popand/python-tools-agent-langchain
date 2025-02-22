import asyncio
import json
import os
from dotenv import load_dotenv

from internal.agent.agent import ToolsAgent, AgentConfig
from internal.tools.calculator import CalculatorTool
from internal.tools.http_request import HTTPRequestTool
from internal.tools.wikipedia import WikipediaTool
from internal.tools.code_execution import CodeExecutionTool

async def main():
    # Load environment variables
    load_dotenv()

    # Get OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    # Create tools
    tools = [
        CalculatorTool(),
        HTTPRequestTool(),
        WikipediaTool(),
        CodeExecutionTool()
    ]

    # Create agent configuration
    config = AgentConfig(
        system_message="You are a helpful assistant that can perform calculations, make HTTP requests, search Wikipedia, and execute code.",
        max_iterations=5,
        return_intermediate_steps=True
    )

    # Create the agent
    agent = ToolsAgent(config, tools, openai_api_key)

    # Example input that uses multiple tools
    input_text = """Can you help me with these tasks:
1. Calculate 15 divided by 3 and multiply the result by 4
2. Search Wikipedia for information about Python programming language
3. Make an HTTP GET request to https://api.github.com/repos/python/cpython
4. Write and execute a Python script that prints "Hello from Python!"
"""

    print("🤖 Executing agent with input:", input_text)
    print("\n" + "="*80 + "\n")

    try:
        # Execute the agent
        response = await agent.execute(input_text)
        
        # Pretty print the response
        print("📝 Agent Response:")
        print(json.dumps(response, indent=2))
        
    except Exception as e:
        print("❌ Error:", str(e))

if __name__ == "__main__":
    asyncio.run(main()) 