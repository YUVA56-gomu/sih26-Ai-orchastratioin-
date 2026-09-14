from ollama import chat


def get_location() -> str:
    return "Karwar, Karnataka"


response = chat(
    model="qwen3:8b",
    messages=[
        {
            "role": "user",
            "content": "Where should I look up my fishing location?",
        }
    ],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_location",
                "description": "Get the user's fishing location.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        }
    ],
)

print(response.message)
print()

if response.message.tool_calls:
    print("✅ TOOL CALLING WORKS")
    for call in response.message.tool_calls:
        print("Tool:", call.function.name)
        print("Arguments:", call.function.arguments)
else:
    print("❌ MODEL DID NOT RETURN A TOOL CALL")