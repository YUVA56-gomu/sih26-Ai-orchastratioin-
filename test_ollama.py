from litellm import completion


response = completion(
    model="ollama/qwen3:8b",
    api_base="http://localhost:11434",
    messages=[
        {
            "role": "user",
            "content": (
                "You are ORCA, a marine intelligence AI. "
                "Say READY and explain that you are running locally."
            ),
        }
    ],
)

print(response.choices[0].message.content)