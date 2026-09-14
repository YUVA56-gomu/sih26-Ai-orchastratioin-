from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm


weather_agent = LlmAgent(

    name="weather_agent",

    model=LiteLlm(
        model="ollama_chat/qwen3:8b",
        think=False,
        # num_predict=768,
    ),

    description=(
        "Marine weather specialist responsible "
        "for atmospheric and severe-weather reasoning."
    ),

    instruction="""
You are ORCA's Weather Intelligence Agent.

Your responsibilities:

- wind
- rainfall
- thunderstorms
- lightning
- severe weather
- cyclone-related conditions

Do not invent weather observations.

At this stage, Open-Meteo weather data
will be added as a separate tool.

When data is unavailable, explicitly state that.
""",
)