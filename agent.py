"""
agent.py — THE AGENT LOOP. This is the whole idea.

    while the model hasn't finished:
        send conversation + tool definitions to Claude
        if Claude asks for a tool -> run it -> append result -> loop again
        if Claude replies with text -> that's the final answer, stop

Everything else (memory, tools, streaming) hangs off this loop.
"""
import os
import anthropic
from dotenv import load_dotenv

from tools import TOOL_SCHEMAS, dispatch
from prompts import SYSTEM_PROMPT

load_dotenv()

MODEL = "claude-sonnet-4-5"
MAX_STEPS = 25  # safety valve so a buggy agent can't loop forever


class Agent:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key."
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        self.messages = []  # the entire "memory": a growing list of messages

    def run(self, user_input: str, on_event=None):
        """Run one user request through the agent loop.

        on_event(kind, data) is an optional callback the UI uses to show
        progress: ("text", str) | ("tool_call", (name, inputs)) | ("tool_result", str)
        """
        def emit(kind, data=None):
            if on_event:
                on_event(kind, data)

        self.messages.append({"role": "user", "content": user_input})

        for step in range(MAX_STEPS):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_SCHEMAS,
                messages=self.messages,
            )

            # Collect this turn's content blocks (text + tool calls).
            assistant_content = response.content
            self.messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for block in assistant_content:
                if block.type == "text":
                    emit("text", block.text)
                elif block.type == "tool_use":
                    emit("tool_call", (block.name, block.input))
                    result = dispatch(block.name, block.input)
                    emit("tool_result", result)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            # Claude says "end_turn" when it's done — no tools requested.
            if response.stop_reason == "end_turn" or not tool_results:
                return

            # Feed every tool result back as a user-role message. THIS is how
            # the model "sees" what its tools did — and why we loop.
            self.messages.append({"role": "user", "content": tool_results})

        emit("text", "(stopped: hit max steps)")
