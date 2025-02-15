from custom_deepseek import CustomDeepSeekChat
from agno.agent import Agent
import os

def test_simple_query():
    # Initialize our custom model
    agent = Agent(
        model=CustomDeepSeekChat(api_key=os.getenv('AIMLAPI_KEY')),
        show_tool_calls=True,
        markdown=True
    )

    # Test with a simple query
    agent.print_response("Write a one-sentence story about a cat.")

if __name__ == "__main__":
    test_simple_query()