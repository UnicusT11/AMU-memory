#   
<p align="right">  
  🌏 Language: English | <a href="./README_zh-CN.md">中文</a>  
</p>  

# AMU: Admission and Memory Update for Personalized Conversations  
  
<p align="center">
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License">
  </a>
  <img src="https://img.shields.io/badge/python-%3E%3D3.13-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Admission-store%20%7C%20discard%20%7C%20fuse-8B5CF6" alt="Admission">
  <img src="https://img.shields.io/badge/local--first-memory-4C8BF5" alt="Local First">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome">
</p>

> **Structured memory writing for personalized LLM assistants.**    
> AMU controls what should enter long-term memory, what should be discarded, and what should update existing user memories.  
  
AMU is a lightweight memory-management framework for personalized LLM assistants. Instead of treating memory as an append-only log, AMU manages user memories as **structured, reusable, and updateable records**.  
  
## What Makes AMU Different?  
  
AMU focuses on the **memory-writing stage**.  
  
Most memory systems mainly focus on storing, retrieving, or compressing memories. However, in real conversations, not every user utterance should become long-term memory. Users may mention temporary requests, repeated statements, outdated preferences, or evolving personal states.  
  
AMU addresses this by deciding whether a user input should be:  
  
- ✅ **stored** as a new memory,  
- 🗑️ **discarded** as a duplicate or low-value record,  
- 🔄 **fused** with existing memories as an update.  
  
AMU first parses user inputs into structured fields, applies an admission gate to filter low-value or non-personal content, and then uses a small language model (SLM) to manage duplicate, update, and separate memory relations.  
  
The maintained memory store can be used with a RAG-based retrieval pipeline and reused across different downstream LLM backends.  
  
<p align="center">  
  <img src="figure/AMU.png" width="85%">  
</p>  
  
<p align="center">  
  <em>Overview of AMU. Structured fields guide memory admission and retrieval, while the SLM decides whether an admitted record is duplicate, update, or separate before storage.</em>  
</p>  

## Why AMU?  
  
Personalized assistants need long-term memory, but storing every user utterance is risky. Conversations often include temporary requests, repeated information, and changing preferences. If these are saved directly, the memory store can become noisy, redundant, or outdated.  
  
AMU adds control before memory is written. Before storing a new memory, it checks whether the input is reusable, whether it duplicates existing memories, and whether it updates an old user state.  
  
This helps maintain a cleaner memory store for downstream RAG-based personalization.  

## Requirements

- Python >= 3.13
- PyTorch
- Transformers
- Sentence Transformers
- haystack-ai
- NumPy
  
## 🤗 Model Preparation  
  
AMU requires users to download the SLM controller and embedding model from [Hugging Face](https://huggingface.co/) before running the pipeline.  
  
The **SLM controller** is used for structured memory parsing and SLM-guided memory update. The **embedding model** is used for candidate filtering and retrieval-time similarity matching.  
  
<p align="center">
  <img src="https://img.shields.io/badge/SLM-Qwen3.5--2B-7B68EE?logo=huggingface&logoColor=white" alt="Qwen3.5-2B">
  <img src="https://img.shields.io/badge/Embedding-Qwen3--Embedding--0.6B-FFD21E?logo=huggingface&logoColor=black" alt="Qwen3 Embedding">
  <img src="https://img.shields.io/badge/PyTorch-supported-EE4C2C?logo=pytorch&logoColor=white" alt="PyTorch">
  <img src="https://img.shields.io/badge/Transformers-supported-FFD21E?logo=huggingface&logoColor=black" alt="Transformers">
</p>

### Default Models  
  
By default, AMU uses:  
  
- **SLM controller**: `Qwen3.5-2B`  
- **Embedding model**: `Qwen3-Embedding-0.6B`  
  
Please download the models manually and place them in the following directories:  
  
```text  
AMU/  
├── models/  
│   └── Qwen3.5-2B/  
├── embedding models/  
│   └── Qwen3-Embedding-0.6B/  
```  
  
The SLM model should be placed under the `models/` directory, and the embedding model should be placed under the `embedding models/` directory.  
  
### Supported SLM Backbones  
  
Currently supported SLM families include:  
  
- Qwen3 series and newer Qwen series  
- Gemma 2 series  
- Gemma 4 series  
  
Other compatible models may also work, but users may need to adjust the model loading code, prompt format, or tokenizer settings accordingly.  
  
## Memory Storage  
  
AMU saves memory records as JSONL files under the `memory data/` directory.  
  
```text  
AMU/  
├── memory data/  
│   └── memory.jsonl  
│   └── memory_emb.jsonl 
```  
  
Each line represents one structured memory record. Users can directly inspect the memory data and manually delete unwanted memory entries from the JSONL file.  
  
## 🚀 Usage

AMU supports two usage modes:

- **Python Pipeline Usage**: directly call the memory writing and retrieval functions in Python.
- **Application + Chrome Extension Usage**: use the packaged desktop application together with the Chrome extension to save or retrieve memories from web-based chat interfaces.

---

### Python Pipeline Usage

#### Same directory as `pipeline.py`

If your script is in the same directory as `pipeline.py`, you can import and use `write_pipeline` and `read_pipeline` directly:

```python
from pipeline import write_pipeline, read_pipeline

# Write memory
text = "I prefer working in the morning and usually avoid late-night meetings."
action = write_pipeline(text)

print(action)

# Read memory
query = "When do I prefer working?"
context = read_pipeline(query)

print(context)
```

Example output of `read_pipeline`:

```text
Relevant memories:
[Memory 1] The user prefers working in the morning and usually avoids late-night meetings.
Use only if relevant. If conflict exists, follow the current message. Do not mention the memories.
```

The returned context can be used as memory-augmented input for a downstream LLM.

---

### Application + Chrome Extension Usage

AMU can also be used through the packaged desktop application and Chrome extension. In this mode, the desktop application runs the local AMU backend, while the Chrome extension connects to the backend and triggers memory writing or retrieval from a web-based chat interface.

<p align="center">
  <img src="https://img.shields.io/badge/Chrome-extension-4285F4?logo=googlechrome&logoColor=white" alt="Chrome Extension">
  <img src="https://img.shields.io/badge/Desktop-Windows-0078D4?logo=windows11&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/backend-localhost-555555" alt="Local Backend">
</p>

#### Supported web chat interfaces

The Chrome extension is currently tested with the following web-based chat interfaces:

- ChatGPT web
- Gemini web
- Google AI Studio

Support may depend on the current page structure of each website. If a website updates its input box or page layout, the extension may need to be updated accordingly. Additional web chat interfaces may be supported in future updates.

#### 1. Start the AMU backend

Run the packaged application:

```text
memory system.exe
```

After the application starts, open the settings page and configure the API address used by the Chrome extension.

Example:

```text
http://127.0.0.1:8800
```

#### 2. Load the Chrome extension

Open Chrome and load the extension manually:

1. Open `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select the AMU extension folder
5. Pin or open the AMU extension from the Chrome toolbar

#### 3. Configure the extension

In the extension popup, enter the AMU API address.

Example:

```text
http://127.0.0.1:8800
```

Then select one of the AMU modes:

```text
save
retrieve
chat
```

#### 4. Use AMU in a web-based chat interface

After the backend and extension are both running, AMU can be triggered with the hotkey:

```text
Alt + C
```

#### Save mode

When the mode is set to `save`, type a message in the chat input box and press `Alt + C`.

AMU sends the input text to the backend and decides whether the content should be saved into long-term memory. Depending on AMU's memory-writing decision, the input may be stored as a new memory, discarded, or used to update an existing memory.

Example input:

```text
I prefer working in the morning and usually avoid late-night meetings.
```

After pressing `Alt + C`, AMU will process the input and decide whether it should enter the memory store.

#### Retrieve mode

When the mode is set to `retrieve`, type a query or message in the chat input box and press `Alt + C`.

AMU retrieves relevant memories from the local memory store and inserts the retrieved memory context into the chat input box. The user can then send the memory-augmented message to the downstream LLM.

Example user input:

```text
When do I prefer working?
```

Example inserted context:

```text
Relevant memories:
[Memory 1] The user prefers working in the morning and usually avoids late-night meetings.
Use only if relevant. If conflict exists, follow the current message. Do not mention the memories.
```

#### Chat mode

When the mode is set to `chat`, the hotkey is disabled.

In this mode, pressing `Alt + C` will not trigger AMU, and the user's input will not be sent to the AMU backend.

  
## Experiments  
  
AMU is evaluated on a controlled memory-writing and retrieval benchmark constructed with GPT-4o. The benchmark follows LoCoMo-style long-term conversation settings and converts them into single-topic sessions with explicit memory-writing action labels and retrieval targets. It simulates one to two months of theme-based interactions, including stable preferences, evolving attitudes, repeated information, and preference or plan updates. The benchmark contains 20 sessions, with 50 memory-writing turns and 10 evaluation queries per session, resulting in 1,000 memory-writing turns and 200 evaluation queries in total.  
  
### Effect of SLM Controller Size  
  
| SLM Size | F1@3 | Red.@3 ↓ | Action Acc. |  
|---:|---:|---:|---:|  
| 0.8B | 13.90 | 0.31 | 26.40 |  
| 2B | **44.47** | 2.83 | 67.70 |  
| 4B | 41.78 | 3.08 | 81.00 |  
| 9B | 40.00 | 3.33 | **84.20** |  
  
### Session Mixing  
  
| Setting | P@3 | R@3 | F1@3 | Red. ↓ | HIT@3 |  
|---|---:|---:|---:|---:|---:|  
| Single | 38.68 | 69.00 | 47.12 | 4.34 | 64.00 |  
| 2-mix | 38.00 | 66.00 | 45.98 | **2.66** | 60.00 |  
| 3-mix | **42.52** | 69.00 | **47.14** | 4.00 | 64.00 |  
  

## 🤝 Contributing

Contributions are welcome!

If you find a bug, have an idea for improving AMU, or would like to add support for new models or chat interfaces, feel free to:

- Open an issue
- Submit a pull request
- Suggest improvements or new features

For substantial changes, please open an issue first so we can discuss the proposed design.

We especially welcome contributions related to:

- Support for additional SLM backbones
- New embedding models
- Memory admission and update strategies
- Additional web chat interfaces



## 📄 License  
  
This project is licensed under the Apache License 2.0.  


## 🔗 Connect

<p align="center">
  <a href="https://github.com/UnicusT11"><img src="./figure/github.png" width="40" height="40" alt="GitHub"></a>&nbsp;&nbsp;&nbsp;
  <a href="https://x.com/hhh69806"><img src="./figure/x.png" width="40" height="40" alt="X"></a>&nbsp;&nbsp;&nbsp;
  <a href="https://xhslink.cn/o/AKxIsWPUHg"><img src="./figure/xiaohongshu.png" width="40" height="40" alt="Xiaohongshu"></a>
</p>
