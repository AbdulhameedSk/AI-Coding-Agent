"""
cli.py — talk to the agent in your terminal.

    python cli.py

You'll see the agent "think out loud": each tool call and its result prints
so you can watch the loop from agent.py in action.
"""
from agent import Agent


def main():
    try:
        agent = Agent()
    except RuntimeError as e:
        print(e)
        return

    print("Forge agent ready. Type 'quit' to exit.\n")

    def show(kind, data):
        if kind == "tool_call":
            name, inputs = data
            print(f"  >> tool call: {name}({inputs})")
        elif kind == "tool_result":
            preview = data if len(data) < 300 else data[:300] + "..."
            print(f"  << result: {preview}\n")
        elif kind == "text":
            print(data)

    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() in ("quit", "exit", ""):
            break
        print("agent>", end=" ", flush=True)
        agent.run(user_input, on_event=show)
        print()


if __name__ == "__main__":
    main()
