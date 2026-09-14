from __future__ import annotations

import asyncio

from dotenv import load_dotenv

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent


load_dotenv()


APP_NAME = "orca_marine_intelligence"

USER_ID = "local_user"

SESSION_ID = "local_session"


async def main() -> None:

    print("=" * 70)
    print("🌊 ORCA — Marine Intelligence Platform")
    print("=" * 70)
    print()

    session_service = (
        InMemorySessionService()
    )

    await session_service.create_session(

        app_name=APP_NAME,

        user_id=USER_ID,

        session_id=SESSION_ID,
    )

    runner = Runner(

        app_name=APP_NAME,

        agent=root_agent,

        session_service=session_service,
    )

    print(
        "Type 'exit' to quit."
    )

    print()

    while True:

        user_input = input(
            "You: "
        ).strip()

        if not user_input:
            continue

        if user_input.lower() in {
            "exit",
            "quit",
        }:
            break


        print(
            "\nORCA: ",
            end="",
            flush=True,
        )


        content = types.Content(

            role="user",

            parts=[

                types.Part(
                    text=user_input
                )

            ],
        )


        try:

            async for event in (
                runner.run_async(

                    user_id=USER_ID,

                    session_id=SESSION_ID,

                    new_message=content,
                )
            ):

                if not event.is_final_response():
                    continue

                if not event.content:
                    continue

                for part in (
                    event.content.parts or []
                ):

                    if part.text:

                        print(
                            part.text
                        )


        except Exception as exc:

            print()
            print(
                "ERROR:",
                exc,
            )


        print()


if __name__ == "__main__":

    asyncio.run(main())