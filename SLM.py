import torch
import re
import os
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
from transformers import logging as hf_logging
from transformers import AutoTokenizer, AutoModelForCausalLM

ROOT = Path(__file__).resolve().parent
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "true"

# =========================
# Model path
# =========================
# By default, use the model identifier supported by Transformers.
# If the model has been downloaded locally, you can instead use:
# model_path = ROOT / "models" / "qwen3.5_2b"
# embedding_path = str(ROOT/ "embedding models"/ "qwen3-embedding-0.6b")
model_path = "Qwen/Qwen3.5-2B"
embedding_path = "Qwen/Qwen3-Embedding-0.6B"


hf_logging.set_verbosity_error()

logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

# tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    model_path,
    trust_remote_code=True,
    local_files_only=True
)

def build_input(user_prompt, system_prompt, model_name="qwen"):
    model_name_lower = model_name.lower()

    if "gemma" in model_name_lower:
        # Gemma
        content = user_prompt.strip()
        if system_prompt:
            content = f"""
            Instruction:

                {system_prompt.strip()}

            User input:

                {content.strip()}
            """

        messages = [
            {"role": "user", "content": content}
        ]

        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    elif "qwen" in model_name_lower:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )

    elif "llama" in model_name_lower:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        return tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(model.device)

    else:
        # fallback
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            tokenizer=True,
            return_dict=True,
        )



# model
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.float16,
    device_map="cuda",
    trust_remote_code=True,
    local_files_only=True,
)

def clean_output(text):
    patterns = [
        r"<\|system\|>.*?<\|user\|>",
        r"<\|user\|>.*?<\|assistant\|>",
        r"system:.*?(?=user:|assistant:|$)",
        r"user:.*?(?=assistant:|$)",
        r"assistant:"
    ]

    for p in patterns:
        text = re.sub(p, "", text, flags=re.S)

    return text.strip()

def append_content(original_input, stage1_result):
    return f"""
    original user input:
    {original_input}
    
    Stage 1 result:
    {stage1_result}   
    """


def append_mem(original_input, new_input):
    return f"""
    New memory:
    {new_input}

    Old memory:
    {original_input}   
    """

def append_update(original_input, new_input):
    return f"""
    New memory:
    {new_input}

    Update memories:
    {original_input}   
    """

def generate_text(user_text, system_prompt):
    text = build_input(user_text, system_prompt)

    input = tokenizer(text, return_tensors="pt").to("cuda")

    output = model.generate(
        **input,
        max_new_tokens=120,
        do_sample=False,
        temperature=0.0,
        repetition_penalty=1.2,
        eos_token_id=tokenizer.eos_token_id,

    )

    result = tokenizer.decode(output[0][(input["input_ids"].shape[-1]):], skip_special_tokens=True)

    return result

#embedding
embedding_model = SentenceTransformer(embedding_path)

def embed_func(text: str):
    vec = embedding_model.encode(text, normalize_embeddings=True)
    return vec.tolist() if hasattr(vec, "tolist") else vec

def Similarity(query_emb, memory_emb):
    return memory_emb @ query_emb.T

