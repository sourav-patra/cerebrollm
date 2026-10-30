---
library_name: vllm
language:
- en
- fr
- de
- es
- pt
- it
- ja
- ko
- ru
- zh
- ar
- fa
- id
- ms
- ne
- pl
- ro
- sr
- sv
- tr
- uk
- vi
- hi
- bn
license: apache-2.0
inference: false
base_model:
- mistralai/Mistral-Small-3.1-24B-Instruct-2503
extra_gated_description: >-
  If you want to learn more about how we process your personal data, please read
  our <a href="https://mistral.ai/terms/">Privacy Policy</a>.
tags:
- mistral-common
---

# Devstral Small 1.0

Devstral is an agentic LLM for software engineering tasks built under a collaboration between [Mistral AI](https://mistral.ai/) and [All Hands AI](https://www.all-hands.dev/) 🙌. Devstral excels at using tools to explore codebases, editing multiple files and power software engineering agents. The model achieves remarkable performance on SWE-bench which positionates it as the #1 open source model on this [benchmark](#benchmark-results). 

It is finetuned from [Mistral-Small-3.1](https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Base-2503), therefore it has a long context window of up to 128k tokens. As a coding agent, Devstral is text-only and before fine-tuning from `Mistral-Small-3.1` the vision encoder was removed.

For enterprises requiring specialized capabilities (increased context, domain-specific knowledge, etc.), we will release commercial models beyond what Mistral AI contributes to the community.

Learn more about Devstral in our [blog post](https://mistral.ai/news/devstral).


## Key Features:
- **Agentic coding**: Devstral is designed to excel at agentic coding tasks, making it a great choice for software engineering agents.
- **lightweight**: with its compact size of just 24 billion parameters, Devstral is light enough to run on a single RTX 4090 or a Mac with 32GB RAM, making it an appropriate model for local deployment and on-device use.
- **Apache 2.0 License**: Open license allowing usage and modification for both commercial and non-commercial purposes.
- **Context Window**: A 128k context window.
- **Tokenizer**: Utilizes a Tekken tokenizer with a 131k vocabulary size.



## Benchmark Results

### SWE-Bench

Devstral achieves a score of 46.8% on SWE-Bench Verified, outperforming prior open-source SoTA by 6%.

| Model            | Scaffold           | SWE-Bench Verified (%) |
|------------------|--------------------|------------------------|
| Devstral         | OpenHands Scaffold | **46.8**               |
| GPT-4.1-mini     | OpenAI Scaffold    | 23.6                   |
| Claude 3.5 Haiku | Anthropic Scaffold | 40.6                   |
| SWE-smith-LM 32B | SWE-agent Scaffold | 40.2                   |


 When evaluated under the same test scaffold (OpenHands, provided by All Hands AI 🙌), Devstral exceeds far larger models such as Deepseek-V3-0324 and Qwen3 232B-A22B.

![SWE Benchmark](assets/swe_bench.png)

## Usage

We recommend to use Devstral with the [OpenHands](https://github.com/All-Hands-AI/OpenHands/tree/main) scaffold.
You can use it either through our API or by running locally. 

### API 
Follow these [instructions](https://docs.mistral.ai/getting-started/quickstart/#account-setup) to create a Mistral account and get an API key.

Then run these commands to start the OpenHands docker container.
```bash
export MISTRAL_API_KEY=<MY_KEY>

docker pull docker.all-hands.dev/all-hands-ai/runtime:0.39-nikolaik

mkdir -p $HOME/.openhands-state && echo '{"language":"en","agent":"CodeActAgent","max_iterations":null,"security_analyzer":null,"confirmation_mode":false,"llm_model":"mistral/devstral-small-2505","llm_api_key":"'$MISTRAL_API_KEY'","remote_runtime_resource_factor":null,"github_token":null,"enable_default_condenser":true}' > $HOME/.openhands-state/settings.json

docker run -it --rm --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.39-nikolaik \
    -e LOG_ALL_EVENTS=true \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v $HOME/.openhands-state:/.openhands-state \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app \
    docker.all-hands.dev/all-hands-ai/openhands:0.39
```

### Local inference 

The model can also be deployed with the following libraries:
- [`vllm (recommended)`](https://github.com/vllm-project/vllm): See [here](#vllm-recommended)
- [`mistral-inference`](https://github.com/mistralai/mistral-inference): See [here](#mistral-inference)
- [`transformers`](https://github.com/huggingface/transformers): See [here](#transformers)
- [`LMStudio`](https://lmstudio.ai/): See [here](#lmstudio)
- [`llama.cpp`](https://github.com/ggml-org/llama.cpp): See [here](#llama.cpp)
- [`ollama`](https://github.com/ollama/ollama): See [here](#ollama)


### OpenHands (recommended)

#### Launch a server to deploy Devstral Small 1.0

Make sure you launched an OpenAI-compatible server such as vLLM or Ollama as described above. Then, you can use OpenHands to interact with `Devstral Small 1.0`.

In the case of the tutorial we spineed up a vLLM server running the command:
```bash
vllm serve mistralai/Devstral-Small-2505 --tokenizer_mode mistral --config_format mistral --load_format mistral --tool-call-parser mistral --enable-auto-tool-choice --tensor-parallel-size 2
```

The server address should be in the following format: `http://<your-server-url>:8000/v1`

#### Launch OpenHands

You can follow installation of OpenHands [here](https://docs.all-hands.dev/modules/usage/installation).

The easiest way to launch OpenHands is to use the Docker image:
```bash
docker pull docker.all-hands.dev/all-hands-ai/runtime:0.38-nikolaik

docker run -it --rm --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.38-nikolaik \
    -e LOG_ALL_EVENTS=true \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v $HOME/.openhands-state:/.openhands-state \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app \
    docker.all-hands.dev/all-hands-ai/openhands:0.38
```


Then, you can access the OpenHands UI at `http://localhost:3000`.

#### Connect to the server

When accessing the OpenHands UI, you will be prompted to connect to a server. You can use the advanced mode to connect to the server you launched earlier.

Fill the following fields:
- **Custom Model**: `openai/mistralai/Devstral-Small-2505`
- **Base URL**: `http://<your-server-url>:8000/v1`
- **API Key**: `token` (or any other token you used to launch the server if any)

#### Use OpenHands powered by Devstral

Now you're good to use Devstral Small inside OpenHands by **starting a new conversation**. Let's build a To-Do list app.

<details>
  <summary>To-Do list app</summary

1. Let's ask Devstral to generate the app with the following prompt:

```txt
Build a To-Do list app with the following requirements:
- Built using FastAPI and React.
- Make it a one page app that:
   - Allows to add a task.
   - Allows to delete a task.
   - Allows to mark a task as done.
   - Displays the list of tasks.
- Store the tasks in a SQLite database.
```

![Agent prompting](assets/tuto_open_hands/agent_prompting.png)


2. Let's see the result

You should see the agent construct the app and be able to explore the code it generated.

If it doesn't do it automatically, ask Devstral to deploy the app or do it manually, and then go the front URL deployment to see the app.

![Agent working](assets/tuto_open_hands/agent_working.png)
![App UI](assets/tuto_open_hands/app_ui.png)


3. Iterate

Now that you have a first result you can iterate on it by asking your agent to improve it. For example, in the app generated we could click on a task to mark it checked but having a checkbox would improve UX. You could also ask it to add a feature to edit a task, or to add a feature to filter the tasks by status.

Enjoy building with Devstral Small and OpenHands!

</details>


### vLLM (recommended)

We recommend using this model with the [vLLM library](https://github.com/vllm-project/vllm)
to implement production-ready inference pipelines.

**_Installation_**

Make sure you install [`vLLM >= 0.8.5`](https://github.com/vllm-project/vllm/releases/tag/v0.8.5):

```
pip install vllm --upgrade
```

Doing so should automatically install [`mistral_common >= 1.5.5`](https://github.com/mistralai/mistral-common/releases/tag/v1.5.5).

To check:
```
python -c "import mistral_common; print(mistral_common.__version__)"
```

You can also make use of a ready-to-go [docker image](https://github.com/vllm-project/vllm/blob/main/Dockerfile) or on the [docker hub](https://hub.docker.com/layers/vllm/vllm-openai/latest/images/sha256-de9032a92ffea7b5c007dad80b38fd44aac11eddc31c435f8e52f3b7404bbf39).

#### Server

We recommand that you use Devstral in a server/client setting. 

1. Spin up a server:

```
vllm serve mistralai/Devstral-Small-2505 --tokenizer_mode mistral --config_format mistral --load_format mistral --tool-call-parser mistral --enable-auto-tool-choice --tensor-parallel-size 2
```


2. To ping the client you can use a simple Python snippet.

```py
import requests
import json
from huggingface_hub import hf_hub_download


url = "http://<your-server-url>:8000/v1/chat/completions"
headers = {"Content-Type": "application/json", "Authorization": "Bearer token"}

model = "mistralai/Devstral-Small-2505"

def load_system_prompt(repo_id: str, filename: str) -> str:
    file_path = hf_hub_download(repo_id=repo_id, filename=filename)
    with open(file_path, "r") as file:
        system_prompt = file.read()
    return system_prompt

SYSTEM_PROMPT = load_system_prompt(model, "SYSTEM_PROMPT.txt")

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "<your-command>",
            },
        ],
    },
]

data = {"model": model, "messages": messages, "temperature": 0.15}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json()["choices"][0]["message"]["content"])
```

### Mistral-inference

We recommend using mistral-inference to quickly try out / "vibe-check" Devstral.

#### Install

Make sure to have mistral_inference >= 1.6.0 installed.

```bash
pip install mistral_inference --upgrade
```

#### Download

```python
from huggingface_hub import snapshot_download
from pathlib import Path

mistral_models_path = Path.home().joinpath('mistral_models', 'Devstral')
mistral_models_path.mkdir(parents=True, exist_ok=True)

snapshot_download(repo_id="mistralai/Devstral-Small-2505", allow_patterns=["params.json", "consolidated.safetensors", "tekken.json"], local_dir=mistral_models_path)
```

#### Python

You can run the model using the following command:

```bash
mistral-chat $HOME/mistral_models/Devstral --instruct --max_tokens 300
```

You can then prompt it with anything you'd like.

### Transformers

To make the best use of our model with transformers make sure to have [installed](https://github.com/mistralai/mistral-common) `    mistral-common >= 1.5.5` to use our tokenizer.

```bash
pip install mistral-common --upgrade
```

Then load our tokenizer along with the model and generate:

```python
import torch

from mistral_common.protocol.instruct.messages import (
    SystemMessage, UserMessage
)
from mistral_common.protocol.instruct.request import ChatCompletionRequest
from mistral_common.tokens.tokenizers.mistral import MistralTokenizer
from huggingface_hub import hf_hub_download
from transformers import AutoModelForCausalLM

def load_system_prompt(repo_id: str, filename: str) -> str:
    file_path = hf_hub_download(repo_id=repo_id, filename=filename)
    with open(file_path, "r") as file:
        system_prompt = file.read()
    return system_prompt

model_id = "mistralai/Devstral-Small-2505"
tekken_file = hf_hub_download(repo_id=model_id, filename="tekken.json")
SYSTEM_PROMPT = load_system_prompt(model_id, "SYSTEM_PROMPT.txt")

tokenizer = MistralTokenizer.from_file(tekken_file)

model = AutoModelForCausalLM.from_pretrained(model_id)

tokenized = tokenizer.encode_chat_completion(
    ChatCompletionRequest(
        messages=[
            SystemMessage(content=SYSTEM_PROMPT),
            UserMessage(content="<your-command>"),
        ],
    )
)

output = model.generate(
    input_ids=torch.tensor([tokenized.tokens]),
    max_new_tokens=1000,
)[0]

decoded_output = tokenizer.decode(output[len(tokenized.tokens):])
print(decoded_output)
```

### LMStudio
Download the weights from huggingface:

```
pip install -U "huggingface_hub[cli]"
huggingface-cli download \
"mistralai/Devstral-Small-2505_gguf" \
--include "devstralQ4_K_M.gguf" \
--local-dir "mistralai/Devstral-Small-2505_gguf/"
```

You can serve the model locally with [LMStudio](https://lmstudio.ai/).
* Download [LM Studio](https://lmstudio.ai/) and install it
* Install `lms cli $HOME/.lmstudio/bin/lms bootstrap`
* In a bash terminal, run `lms import devstralQ4_K_M.gguf` in the directory where you've downloaded the model checkpoint (e.g. `mistralai/Devstral-Small-2505_gguf`)
* Open the LMStudio application, click the terminal icon to get into the developer tab. Click select a model to load and select Devstral Q4 K M. Toggle the status button to start the model, in setting toggle Serve on Local Network to be on.
* On the right tab, you will see an API identifier which should be devstralq4_k_m and an api address under API Usage. Keep note of this address, we will use it in the next step.

Launch Openhands
You can now interact with the model served from LM Studio with openhands. Start the openhands server with the docker

```bash
docker pull docker.all-hands.dev/all-hands-ai/runtime:0.38-nikolaik
docker run -it --rm --pull=always \
	-e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.38-nikolaik \
	-e LOG_ALL_EVENTS=true \
	-v /var/run/docker.sock:/var/run/docker.sock \
	-v $HOME/.openhands-state:/.openhands-state \
	-p 3000:3000 \
	--add-host host.docker.internal:host-gateway \
	--name openhands-app \
	docker.all-hands.dev/all-hands-ai/openhands:0.38
```

Click “see advanced setting” on the second line. 
In the new tab, toggle advanced to on. Set the custom model to be mistral/devstralq4_k_m and Base URL the api address we get from the last step in LM Studio. Set API Key to dummy. Click save changes.

### llama.cpp

Download the weights from huggingface:

```
pip install -U "huggingface_hub[cli]"
huggingface-cli download \
"mistralai/Devstral-Small-2505_gguf" \
--include "devstralQ4_K_M.gguf" \
--local-dir "mistralai/Devstral-Small-2505_gguf/"
```

Then run Devstral using the llama.cpp CLI.

```bash
./llama-cli -m Devstral-Small-2505_gguf/devstralQ4_K_M.gguf -cnv
```

### Ollama

You can run Devstral using the [Ollama](https://ollama.ai/) CLI.

```bash
ollama run devstral
```

### Example: Understanding Test Coverage of Mistral Common

We can start the OpenHands scaffold and link it to a repo to analyze test coverage and identify badly covered files.
Here we start with our public `mistral-common` repo.


After the repo is mounted in the workspace, we give the following instruction
```
Check the test coverage of the repo and then create a visualization of test coverage. Try plotting a few different types of graphs and save them to a png.
```
The agent will first browse the code base to check test configuration and structure.

![Repo Exploration](assets/images_example/example_mistral_common_1.png)

Then it sets up the testing dependencies and launches the coverage test:

![Repo Exploration](assets/images_example/example_mistral_common_2.png)

Finally, the agent writes necessary code to visualize the coverage.
![Repo Exploration](assets/images_example/example_mistral_common_3.png)

At the end of the run, the following plots are produced:
![Repo Exploration](assets/images_example/example_mistral_common_res_1.png)
![Repo Exploration](assets/images_example/example_mistral_common_res_2.png)
![Repo Exploration](assets/images_example/example_mistral_common_res_3.png)