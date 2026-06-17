import os
import chainlit as cl
from dotenv import load_dotenv
from openai import AsyncOpenAI

from helpers.agent import run_turn
from helpers.callbacks import register_callbacks
from helpers.prompts import SYSTEM_PROMPT

load_dotenv()

DEVELOPER_MODE = True

llm_client = AsyncOpenAI(
    api_key=os.environ["LLM_API_KEY"],
    base_url=os.environ["LLM_BASE_URL"],
)

register_callbacks(run_turn, llm_client)


@cl.on_chat_start
async def start():
    if DEVELOPER_MODE:
        from helpers.dev_data import DEV_CONTEXT
        cl.user_session.set("system_prompt", SYSTEM_PROMPT + DEV_CONTEXT)
        welcome = (
            "Hi! (dev mode)"
        )
    else:
        welcome = (
            "Hi!"
        )

    cl.user_session.set("conversation_history", [])

    await cl.Message(content=welcome).send()


@cl.on_message
async def on_message(message: cl.Message):
    text = message.content.strip()
    lower = text.lower()
    if DEVELOPER_MODE and lower == "test":
        from helpers.dev_tools_demo import run_all_tools_demo
        await run_all_tools_demo()
        return
    await run_turn(llm_client, message)
