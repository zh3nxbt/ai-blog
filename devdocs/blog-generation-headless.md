# Running Claude Code headless with `claude -p`

Technical reference for how Blog uses the Claude Code CLI to run autonomous tasks without human interaction. Written so you can replicate the pattern in any system that shells out or calls APIs.

## What `claude -p` does

`claude -p` (print mode) runs Claude Code as a one-shot process. You pass a prompt, it executes, and it exits. No TTY required. No interactive approval dialogs. Stdout contains the final text output; stderr gets debug/status info.

This is the equivalent of giving an engineer a written brief and letting them work autonomously — Claude reads files, runs shell commands, writes files, and chains tool calls together until the task is done.

## Blog's invocation

```bash
PROMPT=$(cat blog/prompts/generate.md)

claude -p "$PROMPT" \
    --dangerously-skip-permissions \
    --allowedTools "Bash(execute commands),Read(read files),Write(write files)" \
    --model sonnet
```

### Flag breakdown

| Flag | Purpose |
|------|---------|
| `-p` / `--print` | Headless mode. Runs the prompt, prints output, exits. No interactive session. |
| `--dangerously-skip-permissions` | Suppresses all tool-approval prompts. Required when there is no TTY (systemd, cron, Docker, CI). |
| `--allowedTools` | Whitelist of tools Claude can use. Format: `"ToolName(description),ToolName(description)"`. Anything not listed is blocked. |
| `--model` | Model alias (`sonnet`, `opus`, `haiku`) or full ID (`claude-sonnet-4-6`). |

### Other useful flags for headless use

| Flag | Purpose |
|------|---------|
| `--output-format json` | Returns structured JSON with `result`, `cost_usd`, `duration_ms`, `session_id`, etc. |
| `--output-format stream-json` | Streams NDJSON events as Claude works — tool calls, results, text chunks. |
| `--max-budget-usd 0.50` | Hard cost cap. Process exits if spend exceeds this. |
| `--system-prompt "..."` | Override the default system prompt entirely. |
| `--append-system-prompt "..."` | Add instructions to the default system prompt without replacing it. |
| `--json-schema '{"type":"object",...}'` | Force structured output conforming to a JSON Schema. |
| `--no-session-persistence` | Don't save the session to disk. Useful for ephemeral tasks. |
| `--fallback-model haiku` | If primary model is overloaded, fall back to this model. Only works with `-p`. |
| `--add-dir /path/to/other` | Grant file access to directories outside the working directory. |

## How the prompt works

The prompt file (`blog/prompts/generate.md`) is a self-contained instruction set. It tells Claude Code:

1. Which files to read (skill files, config)
2. Which shell commands to run (Python CLI helpers)
3. What decisions to make (topic selection, content strategy)
4. What files to write (the blog post draft)
5. How to validate and retry
6. How to persist results (save to database via CLI helper)

Claude Code executes this as an autonomous loop — reading the prompt, then calling tools (Bash, Read, Write) in whatever sequence makes sense. There is no external orchestration. The prompt **is** the orchestration.

### Key design pattern: CLI helpers as the tool boundary

Claude Code has Bash access, so it can run arbitrary commands. But rather than letting it write raw SQL or make HTTP calls, we expose a Python CLI that wraps every side-effecting operation:

```bash
# Check if post already exists today
.venv/bin/python -m blog.generate_helpers check-today

# Fetch source material
.venv/bin/python -m blog.generate_helpers fetch-sources --rss-limit 10

# Validate content quality
.venv/bin/python -m blog.generate_helpers validate --title "..." --content-file /tmp/blog_post.md

# Save to database
.venv/bin/python -m blog.generate_helpers save-post --title "..." --content-file /tmp/blog_post.md --status published

```

Every helper returns JSON to stdout. Claude parses it and decides the next step. This gives you:

- **Auditability** — every database write goes through a known codepath
- **Testability** — helpers are unit-testable Python, not LLM-generated SQL
- **Sandboxing** — Claude can't do anything the helpers don't expose

## CLAUDE.md: implicit context injection

When `claude -p` runs from a directory containing a `CLAUDE.md` file, that file is automatically loaded into the system prompt. You don't pass it explicitly — Claude Code picks it up from the working directory.

This means your `CLAUDE.md` acts as persistent project-level instructions that apply to every invocation. In Blog's case it defines:

- Database schema and connection details
- Content rules and forbidden patterns
- Code style and git workflow
- Security constraints

The prompt you pass via `-p` can be task-specific and lean, because `CLAUDE.md` handles the shared context.

## Replicating this with the Anthropic API

If you are building a similar system using the Claude API directly (no CLI), here is how each piece maps.

### 1. The basic call

```python
import anthropic

client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16384,
    system="<contents of CLAUDE.md>",
    messages=[
        {"role": "user", "content": "<contents of generate.md prompt>"}
    ],
    tools=[...],  # tool definitions
)
```

### 2. Mapping `--allowedTools` to API tool definitions

Claude Code's `--allowedTools "Bash(execute commands),Read(read files),Write(write files)"` maps to tool definitions in the API:

```python
tools = [
    {
        "name": "bash",
        "description": "Execute a shell command and return stdout/stderr.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The bash command to run"}
            },
            "required": ["command"]
        }
    },
    {
        "name": "read_file",
        "description": "Read a file from disk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute file path"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file on disk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute file path"},
                "content": {"type": "string", "description": "File content"}
            },
            "required": ["path", "content"]
        }
    }
]
```

### 3. The agentic loop

`claude -p` handles the tool-use loop internally. With the raw API, you implement it yourself:

```python
import subprocess

def run_agent(system_prompt: str, user_prompt: str, tools: list) -> str:
    messages = [{"role": "user", "content": user_prompt}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=16384,
            system=system_prompt,
            messages=messages,
            tools=tools,
        )

        # If Claude is done (no more tool calls), return the text
        if response.stop_reason == "end_turn":
            return "".join(
                block.text for block in response.content
                if block.type == "text"
            )

        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            result = execute_tool(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })

        # Append assistant response and tool results, then loop
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})


def execute_tool(name: str, params: dict) -> str:
    """Execute a tool call and return the result as a string."""
    if name == "bash":
        proc = subprocess.run(
            params["command"],
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = proc.stdout
        if proc.returncode != 0:
            output += f"\nSTDERR:\n{proc.stderr}\nEXIT CODE: {proc.returncode}"
        return output

    elif name == "read_file":
        with open(params["path"], "r") as f:
            return f.read()

    elif name == "write_file":
        with open(params["path"], "w") as f:
            f.write(params["content"])
        return f"Wrote {len(params['content'])} bytes to {params['path']}"

    return f"Unknown tool: {name}"
```

### 4. Mapping other CLI flags to API concepts

| CLI flag | API equivalent |
|----------|---------------|
| `--model sonnet` | `model="claude-sonnet-4-6"` parameter |
| `--system-prompt "..."` | `system="..."` parameter |
| `--append-system-prompt "..."` | Concatenate to your system string |
| `--json-schema '{...}'` | Use `tool_choice` with a single tool whose schema matches, or parse/validate output yourself |
| `--max-budget-usd 0.50` | Track `response.usage` tokens and multiply by per-token pricing; break the loop when you hit the cap |
| `--dangerously-skip-permissions` | Not applicable — you control tool execution directly |
| `--allowedTools` | Only define tools you want the model to call |
| `--output-format json` | Already structured — `response.content` gives you typed blocks |
| `--output-format stream-json` | Use `client.messages.stream()` for SSE events |
| `CLAUDE.md` auto-loading | Read the file and prepend to your `system` parameter |

### 5. What `claude -p` does that you have to handle yourself

- **Tool execution sandboxing.** Claude Code runs Bash in a restricted sandbox. Your API implementation runs `subprocess.run` raw — you need to handle timeouts, working directory, and restrict what commands can run.
- **Context window management.** Long agent runs can exceed the context window. Claude Code auto-compresses old messages. With the API, you need to implement truncation or summarization when `input_tokens` approaches the model's limit.
- **Retries on transient API errors.** Claude Code retries on 429s and 500s with backoff. Wrap your API calls in retry logic (the `anthropic` SDK has built-in retries).
- **Cost tracking.** `response.usage.input_tokens` and `response.usage.output_tokens` are returned on every call. Accumulate these across the loop to enforce a budget.
- **Session persistence.** Claude Code saves conversation history for `--resume`. If you need resumability, persist the `messages` array.

## Environment requirements

Claude Code needs:

- **`ANTHROPIC_API_KEY`** — set in the environment or via `claude auth`
- **Working directory** — `cd` to the project root before invoking. `CLAUDE.md` and file paths are relative to this.
- **`unset CLAUDECODE`** — if launching `claude -p` from within a Claude Code session (e.g., a systemd service triggered by Claude Code), unset this env var to avoid "nested session" errors.
- **No TTY required** — `-p` mode works in cron, systemd, Docker, CI pipelines, SSH without a terminal.

## Invocation patterns

### From systemd

```ini
# blog-generator.service
[Service]
Type=oneshot
WorkingDirectory=/opt/blog-backend
ExecStart=/bin/bash blog/generate.sh
Environment=ANTHROPIC_API_KEY=sk-ant-...
```

### From cron

```cron
0 8 * * * cd /opt/blog-backend && bash blog/generate.sh >> /var/log/blog-generator.log 2>&1
```

### From Python (subprocess)

```python
import subprocess

result = subprocess.run(
    [
        "claude", "-p", prompt_text,
        "--dangerously-skip-permissions",
        "--allowedTools", "Bash(execute commands),Read(read files),Write(write files)",
        "--model", "sonnet",
        "--output-format", "json",
        "--max-budget-usd", "0.50",
    ],
    capture_output=True,
    text=True,
    cwd="/opt/blog-backend",
    timeout=600,
)

if result.returncode == 0:
    import json
    output = json.loads(result.stdout)
    print(f"Cost: ${output['cost_usd']}, Duration: {output['duration_ms']}ms")
```

### From Docker

```dockerfile
FROM node:20-slim
RUN npm install -g @anthropic-ai/claude-code
COPY . /app
WORKDIR /app
CMD ["claude", "-p", "--dangerously-skip-permissions", "--model", "sonnet"]
```

Pass the prompt via stdin or mount the prompt file and use `$(cat prompt.md)`.

## Cost control

Blog's generation typically costs $0.15-0.40 per run (Sonnet). To keep costs predictable:

1. **`--max-budget-usd`** — hard cap per invocation
2. **`--allowedTools`** — fewer tools = fewer round trips = lower cost
3. **Prompt design** — front-load decisions in the prompt so Claude doesn't explore dead ends
4. **CLI helpers return JSON** — structured output is cheaper to parse than free-form text
5. **Idempotency check first** — the prompt starts by checking if today's post already exists, avoiding wasted runs
