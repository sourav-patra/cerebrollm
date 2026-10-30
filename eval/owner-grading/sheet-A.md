# Owner grading sheet A

Grade each answer correct (Y) or incorrect (N) against the reference. The arm is hidden. Fill the Grade line of each entry. Known limit: an answer with citations in square brackets came from the retrieval arm.

## S01

Question: Which promptfoo command starts the browser interface for looking at results?

Answer:

```text
The command is `promptfoo view`. The docs describe it as: "Start a browser UI for visualization of results." [promptfoo/site/docs/usage/command-line.md]

The web viewer guide shows it run through npx: "npx promptfoo@latest view" [promptfoo/site/docs/usage/web-ui.md]
```

Reference (promptfoo/site/docs/usage/command-line.md): ## `promptfoo view`; Start a browser UI for visualization of results.

Key facts: ["promptfoo view"]

Grade (Y/N): Y

## S02

Question: Which Azure provider option in promptfoo marks a deployment as a reasoning model?

Answer:

```text
In promptfoo's Azure OpenAI provider, you set **`isReasoningModel: true`** in the provider's `config` block to mark a deployment as a reasoning model (such as an o-series deployment). I believe this changes how requests are formatted for those models, for example by using `max_completion_tokens` instead of `max_tokens` and omitting unsupported parameters like `temperature`. I'm not certain of every detail, so check the Azure provider section of the promptfoo docs for the exact behavior in your version.
```

Reference (promptfoo/site/docs/providers/azure.md): | isReasoningModel  | current: `o1` is deprecated; use isReasoningModel. | out of date: The Azure option `o1` marks a reasoning deployment.

Key facts: ["isReasoningModel"]

Grade (Y/N):  Y

## S03

Question: Which promptfoo prompt-object field holds the text shown for the prompt in outputs and the web UI?

Answer:

```text
The field is **`label`**. In promptfoo, a prompt object can set `label` to a human-readable name, and that name is what appears in the CLI output and the web UI in place of the raw prompt text. The prompt's actual content is in `raw`, which is a separate field.

I'm fairly confident in this, but I'm working from memory and haven't checked the current docs for this version.
```

Reference (promptfoo/site/docs/configuration/reference.md): label: string; // How to display it in outputs and web UI | current: display is deprecated; use label. | out of date: The display field names the prompt.

Key facts: ["label"]

Grade (Y/N): Y

## S04

Question: Which Ollama API endpoint should I call to generate embeddings, and what does it take as input?

Answer:

````text
Use **`POST /api/embed`** on your Ollama server (default `http://localhost:11434`).

**Input:**
- `model` (required): the name of an embedding model, such as `nomic-embed-text`. It must be pulled first.
- `input` (required): a string, or an array of strings for batch embedding.
- Optional fields include `truncate` (whether to cut inputs that exceed the context length, default true), `options` (model parameters), and `keep_alive` (how long the model stays loaded).

**Output:** a JSON object with `model` and `embeddings`, which is an array of vectors, one per input string, in the same order as the input.

Example request:
```json
{
  "model": "nomic-embed-text",
  "input": ["first text", "second text"]
}
```

The older **`POST /api/embeddings`** endpoint takes a single `prompt` string and returns one vector in `embedding`. I believe it is deprecated in favor of `/api/embed`, so prefer the newer one. Ollama also exposes an OpenAI-compatible `/v1/embeddings` endpoint.

I'm not certain of the exact field names and defaults in the latest Ollama release, so check the API docs in the Ollama repository if something doesn't match.
````

Reference (ollama/docs/api.md): POST /api/embed; - `input`: text or list of text to generate embeddings for. | current: /api/embeddings is superseded by /api/embed (field `input`). | out of date: Embeddings come from POST /api/embeddings with a `prompt` field.

Key facts: ["/api/embed", "input"]

Grade (Y/N): Y

## S05

Question: What exit code does promptfoo eval return when at least one test case fails?

Answer:

```text
According to my knowledge of promptfoo, `promptfoo eval` exits with **code 100** when at least one test case fails. I believe a general error returns code 1, and a fully passing run returns 0. I'm less certain about the exact codes in your installed version, so check the promptfoo CLI docs or run `promptfoo eval --help` to confirm.
```

Reference (promptfoo/site/docs/usage/command-line.md): will return exit code `100` when there is at least 1 test case failure

Key facts: ["100"]

Grade (Y/N): Y

## S06

Question: Which LlamaIndex function loads a persisted index back from a storage context?

Answer:

```text
The function is `load_index_from_storage`. You pass it a `StorageContext` built from the persist directory, for example `StorageContext.from_defaults(persist_dir="./storage")`, and it returns the reconstructed index.
```

Reference (llama_index/docs/src/content/docs/framework/getting_started/starter_example.md): index = load_index_from_storage(storage_context)

Key facts: ["load_index_from_storage"]

Grade (Y/N): Y

## S07

Question: What is the status of Python 3.9 support across the LlamaIndex packages?

Answer:

```text
I can't verify the current status from this environment. I don't have a reliable, up-to-date record of LlamaIndex's Python 3.9 support, and I can't check the repository or PyPI from here.

What I can say:

- Python 3.9 reached end of life in October 2025. Projects like LlamaIndex typically drop support for a Python version some time after its EOL, so 3.9 may no longer be supported, but I can't confirm when or whether LlamaIndex made that change.
- Each LlamaIndex package (for example `llama-index-core` and the integration packages) declares its own `requires-python` range, so support can differ between packages.

To get a definitive answer, check:

1. The `requires-python` field in each package's `pyproject.toml` on GitHub (run-llama/llama_index).
2. The "Requires: Python" line on each package's PyPI page, or the output of `pip install <package>` under Python 3.9.
3. The project's release notes or changelog for a note about dropping 3.9.

If you share the package versions or the error you're seeing, I can help interpret it.
```

Reference (llama_index/docs/src/content/docs/framework/CHANGELOG.md): chore: deprecate python 3.9 once and for all | current: The 2026-03-16 release deprecates Python 3.9. | out of date: The AgentCore integration page lists Python 3.9+ as a requirement.

Key facts: [["deprecated", "deprecate"]]

Grade (Y/N): N

## S08

Question: Which LlamaIndex facility should I use to orchestrate multi-step, event-driven LLM application logic?

Answer:

```text
Use **Workflows**. The concepts guide describes it this way: "A Workflow in LlamaIndex is a specific event-driven abstraction that allows you to orchestrate a sequence of steps and LLMs calls." [llama_index/docs/src/content/docs/framework/getting_started/concepts.md]

Workflows can also keep state across steps. The understanding guide lists "Stateful workflows" as a topic and says "workflows can maintain state, which is important for building more complex applications." [llama_index/docs/src/content/docs/framework/understanding/index.md]

The agent docs point to the same facility for custom logic. They say you can "build your own agentic workflows from scratch" in the "Building Workflows" section, rather than using prebuilt agents like `FunctionAgent`. [llama_index/docs/src/content/docs/framework/understanding/agent/index.md]

The retrieved excerpts don't show the Workflow API itself (decorators, event classes, or code examples), so for those, check the "Building Workflows" section of the docs.
```

Reference (llama_index/docs/src/content/docs/framework/changes/deprecated_terms.md): QueryPipeline has been deprecated in favour of [Workflows] | current: QueryPipeline is deprecated in favour of Workflows. | out of date: Multi-step logic is composed with QueryPipeline.

Key facts: ["Workflows"]

Grade (Y/N): Y

## S09

Question: What does the pgvector <#> operator return?

Answer:

```text
The `<#>` operator returns the negative inner product. The README says: "`<#>` returns the negative inner product since Postgres only supports `ASC` order index scans on operators" [pgvector/README.md]. The operator reference table also lists it as "negative inner product" [pgvector/README.md].
```

Reference (pgvector/README.md): `<#>` returns the negative inner product

Key facts: ["negative inner product"]

Grade (Y/N): Y

## S10

Question: How do I count embedding and LLM tokens in current LlamaIndex?

Answer:

````text
In LlamaIndex, you count tokens with `TokenCountingHandler`, a callback handler that tallies LLM and embedding tokens as they run. This is from my knowledge of the API, and I can't confirm details against the latest release, so check the docs if something doesn't match.

```python
import tiktoken
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler

token_counter = TokenCountingHandler(
    tokenizer=tiktoken.encoding_for_model("gpt-3.5-turbo").encode
)
Settings.callback_manager = CallbackManager([token_counter])

# ... build an index, run queries, call embeddings, etc. ...

print("LLM prompt tokens:    ", token_counter.prompt_llm_token_count)
print("LLM completion tokens:", token_counter.completion_llm_token_count)
print("LLM total tokens:     ", token_counter.total_llm_token_count)
print("Embedding tokens:     ", token_counter.total_embedding_token_count)

token_counter.reset_counts()  # clear counts before the next measurement
```

Notes:

- **Tokenizer:** The handler needs a function that turns a string into tokens. The example uses tiktoken's encoder for an OpenAI model. For other models, pass that model's tokenizer. If you don't pass one, I believe it falls back to a default, so counts may not match your provider's billing.
- **Per-call detail:** The handler also keeps per-event lists, such as `llm_token_counts` and `embedding_token_counts`, which you can inspect to see the count for each call.
- **Dependencies:** You need `llama-index-core` and `tiktoken` installed.
- **Setting the callback:** Setting `Settings.callback_manager` applies the handler globally. You can also pass a `CallbackManager` to individual components instead.
- **Counts are estimates:** These are local tokenizer counts, not usage figures reported by the API. If you need exact billing numbers, compare them with the provider's usage data in the response.
````

Reference (llama_index/docs/src/content/docs/framework/module_guides/observability/callbacks/token_counting_migration.md): Using the `TokenCountingHandler` callback | current: Token counting moved into the TokenCountingHandler callback. | out of date: Token counts lived on the llm_predictor and embed_model objects (last_token_usage, total_token_usage).

Key facts: ["TokenCountingHandler"]

Grade (Y/N): Y

## S11

Question: Which environment variable sets the pass-rate threshold below which promptfoo eval returns a failing exit code?

Answer:

```text
I don't know of an environment variable that sets a pass-rate threshold. The excerpts I have don't show one.

- The environment variables table in `command-line.md` is truncated in every excerpt, so I can't check its contents.
- The quality-gate examples hardcode the 95% threshold in shell logic rather than reading it from an environment variable. For example: "if (( $(echo "$PASS_RATE < 95" | bc -l) )); then" [promptfoo/site/docs/integrations/ci-cd.md]
- The only built-in failure option shown is a flag, not a threshold: "Fail on any test failures" [promptfoo/site/docs/integrations/ci-cd.md], which corresponds to `npx promptfoo@latest eval --fail-on-error`.

The full environment variables table or the `promptfoo eval` reference in the docs may list such a variable, but I can't confirm that from these excerpts.
```

Reference (promptfoo/site/docs/usage/command-line.md): PROMPTFOO_PASS_RATE_THRESHOLD

Key facts: ["PROMPTFOO_PASS_RATE_THRESHOLD"]

Grade (Y/N): N

## S12

Question: Which two Ollama CLI commands show the models I have downloaded and the models currently loaded in memory?

Answer:

```text
Use `ollama ls` to list the models you have downloaded, and `ollama ps` to see which models are currently loaded into memory.

For `ollama ls`, the docs list it under the heading "### List models" with the command "ollama ls" [ollama/docs/cli.md]. For `ollama ps`, the FAQ says "Use the `ollama ps` command to see what models are currently loaded into memory." [ollama/docs/faq.md]
```

Reference (ollama/docs/cli.md): ollama ls; ollama ps

Key facts: ["ollama ls", "ollama ps"]

Grade (Y/N): Y

## S13

Question: How do I cap the number of concurrent API calls in a promptfoo eval run?

Answer:

````text
In promptfoo, you cap concurrency with the `-j` / `--max-concurrency` flag on `promptfoo eval`:

```bash
promptfoo eval -j 2
promptfoo eval --max-concurrency 2
```

You can also set it in the config file under `evaluateOptions`:

```yaml
evaluateOptions:
  maxConcurrency: 2
```

I believe the default is around 4 concurrent requests, but I'm not certain of the current value. I also believe there's a `delay` option under `evaluateOptions` that adds a pause between requests, which can help with rate limits, but I'm less sure of its exact name and behavior.

I don't know whether individual providers accept their own concurrency limit, so check the docs for your provider. To confirm the flag names and defaults for your installed version, run `promptfoo eval --help` or check the promptfoo configuration docs.
````

Reference (promptfoo/site/docs/usage/command-line.md): `-j, --max-concurrency <number>`

Key facts: [["--max-concurrency", "max concurrency", "-j"]]

Grade (Y/N): Y

## S14

Question: Which LlamaIndex facility should I use to orchestrate multi-step, event-driven LLM application logic?

Answer:

````text
LlamaIndex's facility for this is **Workflows**. It's an event-driven orchestration system in `llama_index.core.workflow` (also available as the `llama-index-workflows` package in newer releases; check your installed version, since the import path has changed over time).

The core pieces are:

- **Steps**: async methods decorated with `@step` on a `Workflow` subclass. Each step takes an incoming event and can emit new events.
- **Events**: subclasses of `Event` that carry data between steps. Steps declare which event type they handle through type annotations, and the framework routes events accordingly.
- **Start and stop**: a `StartEvent` kicks off the run, and a `StopEvent` (returned from a step) ends it and produces the final result.
- **Context**: shared state across steps within a run, with `ctx.store` for storing and retrieving values.
- **Branching, loops, and fan-out**: you can return different event types to route control flow, loop by emitting an event a earlier step handles, and use `ctx.send_event()` with collection helpers to run several branches in parallel and wait for them.
- **Streaming**: you can emit progress events from steps and consume them while the workflow runs.

A minimal example looks like this:

```python
from llama_index.core.workflow import Workflow, StartEvent, StopEvent, step, Event

class MyEvent(Event):
    text: str

class MyWorkflow(Workflow):
    @step
    async def first(self, ev: StartEvent) -> MyEvent:
        return MyEvent(text="processed")

    @step
    async def second(self, ev: MyEvent) -> StopEvent:
        return StopEvent(result=ev.text)

async def main():
    w = MyWorkflow(timeout=60)
    result = await w.run(query="hello")
    print(result)
```

Workflows are the recommended choice over the older query pipelines or chaining approaches for agentic and multi-step logic. Higher-level abstractions such as agents in LlamaIndex are themselves built on top of Workflows. I'm not certain about the exact API details for the latest release, so verify parameter names and import paths against the current LlamaIndex docs.
````

Reference (llama_index/docs/src/content/docs/framework/changes/deprecated_terms.md): QueryPipeline has been deprecated in favour of [Workflows] | current: QueryPipeline is deprecated in favour of Workflows. | out of date: Multi-step logic is composed with QueryPipeline.

Key facts: ["Workflows"]

Grade (Y/N): Y

## S15

Question: What should I use in current LlamaIndex to build an agent that calls tools?

Answer:

````text
For current LlamaIndex, use the **agent workflow API**, mainly `FunctionAgent`. It's built on LlamaIndex Workflows and supports async, streaming, and multi-turn state.

```python
import asyncio
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI

def multiply(a: float, b: float) -> float:
    """Multiply two numbers and return the result."""
    return a * b

def add(a: float, b: float) -> float:
    """Add two numbers and return the result."""
    return a + b

agent = FunctionAgent(
    tools=[multiply, add],  # plain functions are wrapped as tools automatically
    llm=OpenAI(model="gpt-4o-mini"),
    system_prompt="You are a helpful math assistant. Use the tools for arithmetic.",
)

async def main():
    ctx = Context(agent)  # keeps conversation state across calls
    r1 = await agent.run("What is 3 times 4?", ctx=ctx)
    print(r1)
    r2 = await agent.run("Now add 10 to that.", ctx=ctx)
    print(r2)

asyncio.run(main())
```

Key points:

- **Tools:** Write typed Python functions with docstrings, which the LLM uses to decide when to call them. For more control, wrap them with `FunctionTool.from_defaults(fn=...)`. Other tool sources include `QueryEngineTool` for RAG and LlamaHub tool specs.
- **Agent types:** `FunctionAgent` is for LLMs with native function/tool calling. `ReActAgent` is for text-based reasoning with LLMs that lack native tool calling. `CodeActAgent` is for agents that write and execute code.
- **Multi-agent:** `AgentWorkflow` coordinates several agents with handoffs.
- **Deprecated:** `OpenAIAgent.from_tools()` and `ReActAgent.from_tools()` from the older `llama_index.agent` API are legacy. Avoid them in new code.

I'm not certain of the exact import paths and class names as of your current version, since LlamaIndex changes often. Check the official docs (docs.llamaindex.ai) and your installed version's release notes before relying on this.
````

Reference (llama_index/docs/src/content/docs/framework/changes/deprecated_terms.md): classes have been deprecated in favour of [AgentWorkflow] | current: AgentRunner/AgentWorker are deprecated in favour of AgentWorkflow and Workflows. | out of date: Agents are built with AgentRunner and AgentWorker (for example FunctionCallingAgentWorker).

Key facts: ["AgentWorkflow"]

Grade (Y/N):  N

## S16

Question: Which Ollama API endpoint should I call to generate embeddings, and what does it take as input?

Answer:

```text
Call **`POST http://localhost:11434/api/embed`**. The docs show it with a JSON body containing a `model` and an `input` field. The cURL example reads:

"curl -X POST http://localhost:11434/api/embed \" [ollama/docs/capabilities/embeddings.md]

`input` takes a single string, as in "input": "The quick brown fox jumps over the lazy dog." [ollama/docs/capabilities/embeddings.md]. For several texts at once, it takes an array of strings: "Pass an array of strings to `input`." [ollama/docs/capabilities/embeddings.md]

The API reference also documents an older-looking endpoint, `/api/embeddings`, which takes a `prompt` field instead of `input`: "curl http://localhost:11434/api/embeddings -d '{" [ollama/docs/api.md]. The excerpts don't say whether that endpoint is deprecated, so I'd use `/api/embed` unless you have a reason to need the other one.
```

Reference (ollama/docs/api.md): POST /api/embed; - `input`: text or list of text to generate embeddings for. | current: /api/embeddings is superseded by /api/embed (field `input`). | out of date: Embeddings come from POST /api/embeddings with a `prompt` field.

Key facts: ["/api/embed", "input"]

Grade (Y/N):Y

## S17

Question: Which two attributes of the LlamaIndex Settings object hold the maximum input size to the LLM and the number of tokens reserved for generation?

Answer:

```text
The two attributes are **`Settings.context_window`**, the maximum input size sent to the LLM, and **`Settings.num_output`**, the number of tokens reserved for the model's output.
```

Reference (llama_index/docs/src/content/docs/framework/module_guides/supporting_modules/settings.md): Settings.context_window = 4096; Settings.num_output = 256

Key facts: ["context_window", "num_output"]

Grade (Y/N): Y

## S18

Question: Which promptfoo provider should I use to test IBM-hosted models?

Answer:

```text
The provided documents don't mention IBM or any IBM-hosted model, so I can't name a provider for them.

The only related text is the general statement that "Promptfoo supports 60+ providers including OpenAI, Anthropic, Google, and many others:" [promptfoo/site/docs/getting-started.md]. That confirms a broad provider list but doesn't say whether IBM is included.

The providers documentation lives under promptfoo/site/docs/providers/, so checking there for an IBM entry would be the next step. If IBM models are served through an OpenAI-compatible endpoint, the red-team quickstart describes pointing an `openai:chat:` target at a custom `apiBaseUrl`: "For llamafile, vLLM, and Text Generation WebUI, keep the `openai:chat:` prefix, enter the server's model name, and set `apiBaseUrl` including `/v1`." [promptfoo/site/docs/red-team/quickstart.md]. That passage is about other servers, so I can't confirm it applies to IBM's endpoints.
```

Reference (promptfoo/site/docs/providers/ibm-bam.md): **Use [IBM WatsonX](/docs/providers/watsonx) instead.** | current: IBM BAM was sunset in March 2025; use IBM WatsonX. | out of date: IBM models are tested with the IBM BAM provider.

Key facts: ["watsonx"]

Grade (Y/N): N

## S19

Question: Which environment variable sets the pass-rate threshold below which promptfoo eval returns a failing exit code?

Answer:

```text
I don't know of a specific environment variable that sets this threshold in promptfoo, so I can't name one without guessing.

I believe the pass-rate threshold is set with a `--threshold` CLI flag on `promptfoo eval`, but I'm not certain of that either. Check `promptfoo eval --help` for your installed version, or the promptfoo docs, to confirm the flag and whether an environment variable also exists.
```

Reference (promptfoo/site/docs/usage/command-line.md): PROMPTFOO_PASS_RATE_THRESHOLD

Key facts: ["PROMPTFOO_PASS_RATE_THRESHOLD"]

Grade (Y/N): N

## S20

Question: After installing a newer pgvector build, what SQL statement upgrades the extension inside a database?

Answer:

```text
The upgrade statement is run in each database you want to upgrade, after installing the latest version: "ALTER EXTENSION vector UPDATE;" [pgvector/README.md (lines 1272-1284) > pgvector > Upgrading].

You can check the installed version in the current database with: "SELECT extversion FROM pg_extension WHERE extname = 'vector';" [pgvector/README.md (lines 1272-1284) > pgvector > Upgrading].
```

Reference (pgvector/README.md): ALTER EXTENSION vector UPDATE;

Key facts: ["ALTER EXTENSION vector UPDATE"]

Grade (Y/N): Y
