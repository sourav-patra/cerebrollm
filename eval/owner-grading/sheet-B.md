# Owner grading sheet B

Grade each answer correct (Y) or incorrect (N) against the reference. The arm is hidden. Fill the Grade line of each entry. Known limit: an answer with citations in square brackets came from the retrieval arm.

## S01

Question: Which environment variable sets the pass-rate threshold below which promptfoo eval returns a failing exit code?

Answer:

```text
Based on the provided context, there is no explicit mention of an environment variable that sets the pass-rate threshold below which `promptfoo eval` returns a failing exit code. The examples given involve using command-line options or script logic to determine and apply a pass-rate threshold, such as using `--fail-on-error` or custom calculations within a script.

Therefore, I do not know of any environment variable that directly sets this pass-rate threshold based on the provided context. 

If there are specific environment variables related to other configurations, they might be found under sections labeled "Environment variables" in the documents referenced, such as in [1] and [3], but these do not mention a pass-rate threshold environment variable.

For the most accurate information, you may need to consult the complete documentation or source code of the project.
```

Reference (promptfoo/site/docs/usage/command-line.md): PROMPTFOO_PASS_RATE_THRESHOLD

Key facts: ["PROMPTFOO_PASS_RATE_THRESHOLD"]

Grade (Y/N):  N

## S02

Question: Which red-team strategy applies a library of static jailbreak templates in promptfoo?

Answer:

```text
The red-team strategy that applies a library of static jailbreak templates in Promptfoo is the "Jailbreak Templates Strategy." This strategy is designed to test LLM resistance to known jailbreak techniques using a curated library of static templates from 2022-2023 era attacks. It was previously known as `prompt-injection`, but the name was changed to better reflect its purpose. The old name `prompt-injection` is still recognized but is deprecated.
```

Reference (promptfoo/site/docs/red-team/strategies/jailbreak-templates.md): This strategy was previously named `prompt-injection`. | current: The strategy was renamed to jailbreak-templates. | out of date: The strategy is called prompt-injection.

Key facts: ["jailbreak-templates"]

Grade (Y/N): Y

## S03

Question: Which promptfoo provider should I use to test IBM-hosted models?

Answer:

```text
Based on the context provided, the project documentation does not explicitly mention a specific provider for testing IBM-hosted models. To determine the appropriate provider for IBM-hosted models, you would typically need to:

1. **Check the List of Available Providers**: Review the [list of providers](/docs/providers) mentioned in the documentation to see if IBM is listed or supported.

2. **Ensure Compliance with Provider Eligibility**: Ensure that the provider meets the eligibility criteria:
   - Legitimate model access: Confirm that you have the rights to use the IBM models.
   - Accountable ownership: Ensure there is an identifiable operator and terms of service.
   - Evidence it will last: Look for signals indicating the provider's reliability and longevity.

3. **Configuration**: If IBM is supported, configure the provider in your `promptfooconfig.yaml` file with the appropriate IDs and settings as required.

If IBM is not listed as a supported provider, you may need to contact the project maintainers for guidance or check if there are any updates or plugins that support IBM-hosted models.
```

Reference (promptfoo/site/docs/providers/ibm-bam.md): **Use [IBM WatsonX](/docs/providers/watsonx) instead.** | current: IBM BAM was sunset in March 2025; use IBM WatsonX. | out of date: IBM models are tested with the IBM BAM provider.

Key facts: ["watsonx"]

Grade (Y/N): N

## S04

Question: I installed Ollama on Windows. In which folder and file will I find its most recent server logs?

Answer:

```text
For Ollama installed on Windows, the most recent server logs can be found in the file `server.log` located in the following directory:

- `explorer %LOCALAPPDATA%\Ollama`

This folder contains logs, including the `server.log`, which stores the most recent server logs. You can access this folder by opening the File Explorer, pressing `Ctrl + R`, and typing `%LOCALAPPDATA%\Ollama` to navigate directly to the location.
```

Reference (ollama/docs/windows.md): - `explorer %LOCALAPPDATA%\Ollama` contains logs, and downloaded updates; _server.log_ contains the most recent server logs

Key facts: ["=localappdata ollama", "=server log"]

Grade (Y/N):  Y

## S05

Question: How do I point LlamaIndex at a local Ollama LLM and a Hugging Face embedding model globally so that OpenAI is never contacted?

Answer:

````text
To point LlamaIndex at a local Ollama LLM and a Hugging Face embedding model without contacting OpenAI, you'll need to configure LlamaIndex to use your local resources. Here’s a general approach:

1. **Set Up Ollama LLM Locally:**
   - Ensure you have Ollama installed and configured on your local machine.
   - Run the Ollama LLM locally to ensure it’s accessible. Note the local address and port where it's running (e.g., `http://localhost:1234`).

2. **Set Up Hugging Face Embedding Model Locally:**
   - Install the Hugging Face Transformers library if you haven't already.
   - Download the desired embedding model locally using the Transformers library.
   - Ensure the model is loaded and ready to use in your local environment.

3. **Configure LlamaIndex:**
   - Modify the LlamaIndex configuration to point to your local Ollama LLM and the local Hugging Face embedding model.
   - This typically involves setting environment variables or configuration files to specify the local endpoints and paths.

4. **Environment Variables:**
   - Set environment variables to point to your local services. For example:
     ```bash
     export LLAMA_INDEX_OLLAMA_URL=http://localhost:1234
     export LLAMA_INDEX_HF_MODEL_PATH=/path/to/local/huggingface/model
     ```

5. **Configuration Files:**
   - If LlamaIndex uses configuration files, update them to reflect the local endpoints and paths.

6. **Testing:**
   - Test the setup to ensure LlamaIndex is using the local resources and not reaching out to external services like OpenAI.

7. **Documentation:**
   - Refer to LlamaIndex documentation for specific instructions on configuring local models, as the exact steps might vary based on the version or specific setup.

If you encounter specific issues or need more detailed instructions, consulting the documentation for LlamaIndex, Ollama, and Hugging Face Transformers is recommended. If these steps don't align with your setup, please provide more details, and I can try to offer further guidance.
````

Reference (llama_index/docs/src/content/docs/framework/module_guides/supporting_modules/service_context_migration.md): Settings.llm = Ollama(; Settings.embed_model = HuggingFaceEmbedding(

Key facts: ["Settings.llm Ollama", "Settings.embed_model HuggingFaceEmbedding"]

Grade (Y/N): N

## S06

Question: How many bytes of storage does a pgvector vector with N dimensions take?

Answer:

```text
I do not have specific information on the exact number of bytes a pgvector vector with N dimensions takes. The storage size would depend on the data type used for the vector elements (e.g., float, double) and any additional metadata or overhead managed by the pgvector extension. Generally, the storage size can be estimated by multiplying the number of dimensions \( N \) by the size of the data type in bytes. For precise details, consulting the pgvector documentation or examining the implementation would be necessary.
```

Reference (pgvector/README.md): Each vector takes `4 * dimensions + 8` bytes of storage.

Key facts: [["=4 times dimensions plus 8", "=4 times the dimensions plus 8", "=4 times the number of dimensions plus 8", "=4 bytes per dimension plus 8", "=four bytes per dimension plus eight", "=four times dimensions plus eight", "=four times the number of dimensions plus eight", "=4 times n plus 8", "=4 times d plus 8", "=4n plus 8", "=4 bytes per element plus 8", "=4 per dimension plus 8"]]

Grade (Y/N): N

## S07

Question: Which Postgres storage mode does pgvector use for the vector type in current releases?

Answer:

```text
Based on the provided context from the `pgvector/README.md` document, pgvector uses a specific storage mode for the vector type. The vectors are stored using single-precision floating-point numbers, where each vector takes `4 * dimensions + 8` bytes of storage. Each element in the vector is a single-precision floating-point number, similar to the `real` type in Postgres. Additionally, the vectors must have finite elements, meaning no `NaN`, `Infinity`, or `-Infinity` values are allowed. This storage mode supports vectors with up to 16,000 dimensions.

If you are looking for more details or updates beyond the provided context, I recommend checking the latest pgvector documentation or release notes.
```

Reference (pgvector/CHANGELOG.md): Changed storage for vector from `extended` to `external` | current: Vector storage is `external` (0.6.0 onward). | out of date: Vector storage is `extended` (0.4.0).

Key facts: ["external"]

Grade (Y/N): N

## S08

Question: What context length does Ollama use by default on a GPU with 32 GiB of VRAM?

Answer:

```text
Ollama defaults to a 32k context length for a GPU with 24-48 GiB of VRAM. 

The relevant information is found in the documentation:

<Note>
  Ollama defaults to the following context lengths based on VRAM:
    - < 24 GiB VRAM: 4k context
    - 24-48 GiB VRAM: 32k context
    - > 48 GiB VRAM: 256k context
</Note>

["ollama/docs/context-length.md" (lines 1-14)]  
Additionally, it's mentioned that the default context window size used by Ollama is 4096 tokens, but this is overridden by the VRAM-based defaults:

<Note>
  By default, Ollama uses a context window size of 4096 tokens. This can be overridden with the `OLLAMA_CONTEXT_LENGTH` environment variable.
</Note>

["ollama/docs/faq.md" (lines 15-49)]  
Thus, for a GPU with 32 GiB of VRAM, the default context length is 32k tokens.
```

Reference (ollama/docs/context-length.md): 24-48 GiB VRAM: 32k context | current: The default depends on VRAM: 4k below 24 GiB, 32k from 24 to 48 GiB, 256k from 48 GiB. | out of date: The default context window is a flat 4096 tokens.

Key facts: [["32k", "32768", "32,768", "32000", "32,000"]]

Grade (Y/N): Y

## S09

Question: Which environment variable sets the pass-rate threshold below which promptfoo eval returns a failing exit code?

Answer:

```text
Based on the context provided, there is no specific environment variable mentioned that directly sets the pass-rate threshold for `promptfoo eval` to return a failing exit code. The examples in the context show how quality gates are implemented using scripts and command-line options (e.g., `--fail-on-error` or custom scripts checking pass rates) rather than relying on an environment variable for the pass-rate threshold.

The configurations and scripts provided in the context calculate pass rates and determine whether the build should fail based on those calculations. There is no indication of an environment variable used to set a pass-rate threshold directly. Therefore, based on the information available, I do not know of an environment variable that sets this threshold.
```

Reference (promptfoo/site/docs/usage/command-line.md): PROMPTFOO_PASS_RATE_THRESHOLD

Key facts: ["PROMPTFOO_PASS_RATE_THRESHOLD"]

Grade (Y/N): N

## S10

Question: What is the largest number of dimensions of a plain vector column that pgvector can build an HNSW index on?

Answer:

```text
Based on the provided context, there is no explicit mention of a limit on the number of dimensions for a plain vector column when building an HNSW index using pgvector. The context describes how to create an HNSW index for vectors with a specified distance function (e.g., L2 distance, inner product, cosine distance, etc.) but does not specify any dimension limits for plain vector columns. 

Thus, I do not know the largest number of dimensions that pgvector can handle for a plain vector column in an HNSW index based on the given information. For this specific detail, it would be advisable to consult the official pgvector documentation or community resources for any potential limitations or recommendations.
```

Reference (pgvector/README.md): `vector` - up to 2,000 dimensions | current: HNSW indexes on vector go up to 2,000 dimensions. | out of date: Indexes were limited to 1024 dimensions (before 0.4.0).

Key facts: [["2000", "2,000"]]

Grade (Y/N): N

## S11

Question: Which Settings attribute lets me change just the chunk size in LlamaIndex without replacing the default text splitter?

Answer:

````text
In LlamaIndex, you can change just the chunk size without replacing the default text splitter by modifying the `Settings.chunk_size` attribute. This allows you to adjust the chunk size independently from the text splitter settings. Here's how you can do it:

```python
Settings.chunk_size = 512
```

This change is mentioned in the context of the "Chunk Sizes" section, where it states that adjusting the `chunk_size` can be done without altering the default `text_splitter`.
````

Reference (llama_index/docs/src/content/docs/framework/module_guides/supporting_modules/settings.md): Settings.chunk_size = 512

Key facts: ["Settings.chunk_size"]

Grade (Y/N): Y

## S12

Question: What is the oldest Postgres major version that the current pgvector release supports?

Answer:

```text
Based on the provided context, the oldest Postgres major version that the current pgvector release (version 0.8.7) supports is Postgres 14. This is indicated by the Docker tags listed in the context, such as `pg14-trixie`, `pg14-bookworm`, and `pg14`, along with the statement in the CHANGELOG that support for Postgres 11 has been dropped.
```

Reference (pgvector/README.md): Compile and install the extension (supports Postgres 13+) | current: pgvector 0.8.0 dropped Postgres 12; the README says Postgres 13+. | out of date: pgvector 0.6.0 still ran on Postgres 12.

Key facts: ["13"]

Grade (Y/N): N

## S13

Question: What exit code does promptfoo eval return when at least one test case fails?

Answer:

```text
Based on the provided context, there is no specific information regarding the exit code that `promptfoo eval` returns when at least one test case fails. The context mainly describes how to use the `promptfoo eval` command with various options and configurations, as well as details about other aspects of the Promptfoo project. However, it does not explicitly state the exit code behavior for failed test cases.

In many command-line tools, a common convention is to return a non-zero exit code to indicate failure, often `1`, but this is not explicitly confirmed in the provided context for `promptfoo eval`. Therefore, I do not know the exact exit code for this scenario based on the given information.
```

Reference (promptfoo/site/docs/usage/command-line.md): will return exit code `100` when there is at least 1 test case failure

Key facts: ["100"]

Grade (Y/N): N

## S14

Question: What context length does Ollama use by default on a GPU with 32 GiB of VRAM?

Answer:

```text
Based on the provided context, Ollama defaults to the following context lengths based on VRAM:

- < 24 GiB VRAM: 4k context
- 24-48 GiB VRAM: 32k context
- >= 48 GiB VRAM: 256k context

For a GPU with 32 GiB of VRAM, which falls in the 24-48 GiB VRAM range, Ollama uses a default context length of 32k tokens.
```

Reference (ollama/docs/context-length.md): 24-48 GiB VRAM: 32k context | current: The default depends on VRAM: 4k below 24 GiB, 32k from 24 to 48 GiB, 256k from 48 GiB. | out of date: The default context window is a flat 4096 tokens.

Key facts: [["32k", "32768", "32,768", "32000", "32,000"]]

Grade (Y/N): Y

## S15

Question: Which promptfoo command starts the browser interface for looking at results?

Answer:

````text
The `promptfoo` command that starts the browser interface for viewing results is `view`. This command is mentioned in multiple contexts within the provided documents:

1. In the "Quick Start: Try it today" section (Context 1), it states:
   ```bash
   # View the results in an interactive web interface
   npx promptfoo view
   ```

2. In the "Evaluate LangGraph: Red Teaming and Testing Stateful Agents" section (Context 3), it also indicates:
   ```bash
   npx promptfoo view
   ```

3. Similarly, in the "Red Teaming a CrewAI Agent" section (Context 4), it mentions:
   ```
   promptfoo view
   ```

These references confirm that `promptfoo view` is used to start the browser interface for viewing results.
````

Reference (promptfoo/site/docs/usage/command-line.md): ## `promptfoo view`; Start a browser UI for visualization of results.

Key facts: ["promptfoo view"]

Grade (Y/N): Y

## S16

Question: Before I add any models, how much disk space does the Ollama binary install itself need on Windows?

Answer:

```text
I do not have specific information on how much disk space the Ollama binary itself requires for installation on Windows. The context provided mentions that the Ollama install on Windows does not require Administrator rights and installs in the user's home directory by default, needing at least 4GB of space for the binary install. However, this value seems to include both the binary and space for storing large language models. For precise details on the space required solely for the binary, I would recommend checking the official documentation or installation files.

"Set the port to 8080." [example/guide.md] (Note: This is a placeholder citation as the actual requirement detail is not provided in the context.)
```

Reference (ollama/docs/windows.md): You'll need at least 4GB of space for the binary install

Key facts: [["4GB", "4 GB"]]

Grade (Y/N): N

## S17

Question: Which Postgres function can I call to get the on-disk size of a pgvector index?

Answer:

````text
As of my last update, PostgreSQL does not have a built-in function specifically designed to get the on-disk size of a `pgvector` index. The `pgvector` extension itself is designed to extend PostgreSQL with vector similarity search capabilities, and it doesn't add any specific functions for disk usage statistics of its indexes.

However, you can use PostgreSQL's general system catalog and functions to determine the size of a table or index. For example:

1. **Size of an Index**: You can query the `pg_indexes` view and join it with `pg_stat_user_indexes` to get index sizes.
   ```sql
   SELECT 
       i.indexrelid::regclass AS index_name,
       pg_size_pretty(pg_relation_size(i.indexrelid)) AS index_size
   FROM 
       pg_stat_user_indexes AS i
   WHERE 
       i.relname = 'your_table_name';
   ```

2. **Size of a Table**: You can use the `pg_total_relation_size()` function to get the total size of a table, including its indexes.
   ```sql
   SELECT 
       pg_size_pretty(pg_total_relation_size('your_table_name')) AS total_size;
   ```

3. **Size of an Index Only**: Use `pg_relation_size()` on the index's OID.
   ```sql
   SELECT 
       pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
   FROM 
       pg_stat_user_indexes
   WHERE 
       relname = 'your_table_name';
   ```

These methods can help you determine the size of indexes, including those created by `pgvector`. If `pgvector` introduces new functions or methods in the future, you would need to check the latest documentation or release notes for updates.
````

Reference (pgvector/README.md): SELECT pg_size_pretty(pg_relation_size('index_name'));

Key facts: ["pg_relation_size"]

Grade (Y/N): Y

## S18

Question: Which test-case option runs a transform on the LLM output before the assertions in promptfoo?

Answer:

````text
The test-case option that runs a transform on the LLM output before assertions in promptfoo is `options.transform`. This option allows you to specify a transform function that modifies the provider output before assertions are executed. The transform function receives the output and a context with `vars`, `prompt`, and optional provider `metadata`. It returns the value to pass to assertions.

The relevant line from the context is:

"Use `options.transform` to change the provider output before assertions run. The transform receives the output (for example, a string or object) and a context with `vars`, `prompt`, and optional provider `metadata`. Return the value to pass to assertions, either directly or as a promise. Returning `null` or `undefined` causes an error." [1]

Additionally, an example of using `options.transform` in a test case is provided in the context:

```yaml
tests:
  - vars:
      question: What's the weather in New York?
    options:
      transform: (output, context) => {
        return output.toUpperCase();
      }
``` [4] 

These excerpts confirm that `options.transform` is the test-case option used for transforming LLM outputs before running assertions in promptfoo.
````

Reference (promptfoo/site/docs/configuration/reference.md): | options.transform  | current: options.postprocess is a deprecated alias for options.transform. | out of date: The output transform option is options.postprocess.

Key facts: ["options.transform"]

Grade (Y/N): Y

## S19

Question: Which Settings attribute lets me change just the chunk size in LlamaIndex without replacing the default text splitter?

Answer:

```text
I do not know which specific Settings attribute in LlamaIndex allows you to change just the chunk size without replacing the default text splitter. This might be detailed in the LlamaIndex documentation or configuration settings, so reviewing those resources could provide the answer.
```

Reference (llama_index/docs/src/content/docs/framework/module_guides/supporting_modules/settings.md): Settings.chunk_size = 512

Key facts: ["Settings.chunk_size"]

Grade (Y/N): N

## S20

Question: Which test-case option runs a transform on the LLM output before the assertions in promptfoo?

Answer:

```text
Based on the provided context, the option that runs a transform on the LLM output before assertions in promptfoo is `options.transform`. This is evident from the following points in the context:

1. **Configuration Guide**: It mentions that `options.transform` is used to change the provider output before assertions run. This transform receives the output and a context, allowing the user to return a value for assertions or a promise. Returning `null` or `undefined` causes an error. (Referenced in the context section [1]).

2. **Node Package Usage**: When using the node package, you can pass JavaScript functions directly as `transform`, `transformVars`, or `contextTransform` values. This allows for transforming the output before assertions. (Referenced in the context section [4]).

3. **Test Case Reference**: The test case configuration reference indicates that `options.transform` can be a string or a function, implying it's used to modify the output prior to evaluation. (Referenced in the context section [6]).

In summary, `options.transform` is the test-case option used to run a transform on the LLM output before assertions are executed in promptfoo.
```

Reference (promptfoo/site/docs/configuration/reference.md): | options.transform  | current: options.postprocess is a deprecated alias for options.transform. | out of date: The output transform option is options.postprocess.

Key facts: ["options.transform"]

Grade (Y/N): Y
