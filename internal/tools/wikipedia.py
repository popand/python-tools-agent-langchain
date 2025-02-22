from langchain_community.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import wikipedia
import json

class WikipediaInput(BaseModel):
    """Input for Wikipedia Tool."""
    tool_input: str = Field(description="A JSON string containing query and optional language")

class WikipediaTool(BaseTool):
    name: str = "wikipedia"
    description: str = """Useful for searching Wikipedia articles and retrieving information.
    The input should be a JSON string with these fields:
    - query: The search term or article title
    - language: Optional language code (default: "en")"""
    
    args_schema: type[WikipediaInput] = WikipediaInput

    def _run(self, tool_input: str) -> Dict[str, Any]:
        """Execute the Wikipedia search."""
        try:
            # Parse the input JSON
            params = json.loads(tool_input)
            query = params["query"]
            language = params.get("language", "en")

            # Set the language
            wikipedia.set_lang(language)
            
            # Search for the page
            search_results = wikipedia.search(query)
            if not search_results:
                return {
                    "error": f"No Wikipedia articles found for: {query}"
                }
            
            # Get the first result
            page_title = search_results[0]
            page = wikipedia.page(page_title, auto_suggest=False)
            
            return {
                "title": page.title,
                "url": page.url,
                "extract": page.summary,
                "page_id": page.pageid
            }
            
        except json.JSONDecodeError:
            return {"error": "Invalid JSON input"}
        except wikipedia.exceptions.DisambiguationError as e:
            return {
                "error": "Disambiguation page",
                "options": e.options[:5]  # Return first 5 options
            }
        except wikipedia.exceptions.PageError:
            return {
                "error": f"No Wikipedia page found for: {query}"
            }
        except Exception as e:
            return {"error": str(e)}

    async def _arun(self, tool_input: str) -> Dict[str, Any]:
        """Execute the Wikipedia search asynchronously."""
        return self._run(tool_input) 