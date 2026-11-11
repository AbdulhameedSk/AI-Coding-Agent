# Forge — a mini AI agent built from scratch

A fully working coding agent in ~200 lines of Python. No LangChain, no
framework — just the Anthropic API and a `while` loop.

## The core idea

An "AI agent" is not magic. It's this:

```python
while not done:
    response = claude(messages, tools)
    if response asks to use a tool:
        result = run_the_tool(response.tool_call)
        messages.append(result)   # feed the result back
    else:
        done = True               # final text answer
```

The model emits structured JSON like `{"name": "read_file", "input": {"path": "README.md"}}`.
Your code executes it and returns the output as a `tool_result` message.
The loop repeats until the model answers in plain text.

## Tools the agent has

| Tool          | What it does                                  |
| ------------- | --------------------------------------------- |
| `read_file`   | Read a file in the sandboxed workspace        |
| `write_file`  | Create/overwrite a file                       |
| `list_files`  | List workspace directory contents             |
| `run_command` | Run a shell command (30s timeout, in sandbox) |

All file/shell access is confined to `./sandbox/`.

## Setup

```bash
pip install -r requirements.txt
copy .env.example .env   # then put your ANTHROPIC_API_KEY in .env
```

## Run it

Terminal:

```bash
python cli.py
```

Web UI:

```bash
streamlit run app.py
```

## Try asking

- "Create a Python script that prints the first 20 Fibonacci numbers, then run it."
- "Write a small HTML page about Mars and a README describing this workspace."
- "List the files here and summarize what each one does."

## Project layout

```
agent.py    # the agent loop (the important file)
tools.py    # tool implementations + JSON schemas given to Claude
prompts.py  # system prompt
cli.py      # terminal UI
app.py      # Streamlit web UI
sandbox/    # the agent's playground (created on first run)
```

## How memory works

`self.messages` is a plain list. Every API call resends the whole
conversation plus tool results. That's all "memory" is — no database,
no vector store. (Those come later if you outgrow the context window.)
