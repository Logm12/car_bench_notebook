"""A simple demo script to verify function calling with litellm using the project's config."""
import os
import json
from dotenv import load_dotenv
from litellm import completion

# Load environment variables
load_dotenv()

# Define dummy tools for the demo
demo_tools = [
    {
        "type": "function",
        "function": {
            "name": "adjust_ac_temperature",
            "description": "Adjust the air conditioning temperature in the car.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_temperature": {
                        "type": "integer",
                        "description": "The target temperature in Celsius, e.g., 22."
                    },
                    "zone": {
                        "type": "string",
                        "description": "The AC zone to adjust: 'all', 'driver', 'passenger', or 'rear'.",
                        "default": "all"
                    }
                },
                "required": ["target_temperature"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_info",
            "description": "Get current weather info for a location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city/location to check weather for."
                    }
                },
                "required": ["location"]
            }
        }
    }
]

def run_demo():
    # Use OPENAI_API_KEY if available, default to gpt-4o-mini
    model_name = os.getenv("AGENT_LLM", "gpt-4o-mini")
    print(f"--- Running Function Calling Demo ---")
    print(f"LLM Model: {model_name}")
    
    # We ask the model to adjust the AC temperature to 21 degrees in the driver zone
    user_query = "Hey assistant, please set the temperature in the driver seat to 21 degrees Celsius."
    print(f"User Query: {user_query}")
    
    messages = [
        {"role": "system", "content": "You are an in-car assistant capable of controlling car functions and getting weather info."},
        {"role": "user", "content": user_query}
    ]
    
    try:
        response = completion(
            model=model_name,
            messages=messages,
            tools=demo_tools,
            temperature=0.0
        )
        
        # Get the assistant message
        assistant_message = response.choices[0].message
        print("\nLLM Response choices:")
        print(json.dumps(assistant_message.model_dump(exclude_unset=True), indent=2))
        
        # Check for tool calls
        if assistant_message.get("tool_calls"):
            print("\nDetected Tool Calls:")
            for tc in assistant_message["tool_calls"]:
                name = tc["function"]["name"]
                args = tc["function"]["arguments"]
                print(f"  - Tool Name: {name}")
                print(f"  - Arguments: {args}")
        else:
            print("\nNo tool calls detected. LLM Content:")
            print(assistant_message.get("content"))
            
    except Exception as e:
        print(f"\nError running litellm.completion: {e}")

if __name__ == "__main__":
    run_demo()
