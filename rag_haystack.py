# RAG-based memory retrieval for AMU.
#
# This module implements the retrieval-augmented memory search component
# used by the AMU read pipeline.

import json
import os
from typing import Any
from tqdm import tqdm
from haystack import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)
from haystack.components.retrievers import FilterRetriever
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from transformers import logging as hf_logging

os.environ["TOKENIZERS_PARALLELISM"] = "false"
hf_logging.set_verbosity_error()


def normalize_to_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def canonical_key(values: Any) -> str:
    values = normalize_to_list(values)
    values = sorted(values)
    return "|".join(values)


def load_jsonl_memories(file_path: str) -> list[dict[str, Any]]:
    if not os.path.exists(file_path):
        return []

    memories: list[dict[str, Any]] = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_no}: {e}") from e

            if not isinstance(record, dict):
                raise ValueError(f"Line {line_no} is not a JSON object.")

            memories.append(record)

    return memories


def memory_to_document(memory: dict[str, Any]) -> Document:
    """
    Convert one structured memory into a Haystack Document.
    content: memory_summary
    meta: aspect / intent / entities / sentiment
    """
    return Document(
        content=memory.get("memory_summary", ""),
        meta={
            "memory_id": memory.get("memory_id"),
            "aspect": normalize_to_list(memory.get("aspect")),
            "intent": normalize_to_list(memory.get("intent")),  # 保留在库里
            "entities": normalize_to_list(memory.get("entities")),
            "sentiment": memory.get("sentiment"),
            "aspect_key": canonical_key(memory.get("aspect")),  # 用于结构过滤
        },
    )


def build_document_store_from_jsonl(
        file_path: str,
        model_path: str,
) -> InMemoryDocumentStore:
    memories = load_jsonl_memories(file_path)
    docs = [memory_to_document(m) for m in memories]

    document_store = InMemoryDocumentStore(
        return_embedding=True,
        embedding_similarity_function="cosine",
    )

    if not docs:
        return document_store

    doc_embedder = SentenceTransformersDocumentEmbedder(
        model=model_path,
        progress_bar=False
                                                        )
    doc_embedder.warm_up()
    embedded_docs = doc_embedder.run(docs)["documents"]

    document_store.write_documents(embedded_docs, policy="overwrite")
    return document_store


def retrieve_memory_with_haystack(
        query_record: dict[str, Any],
        file_path: str,
        model_path: str,
        top_k: int = 5,
        threshold: float = 0.5,
        use_filter: bool = True,
):
    """
    Input: query_record, Output: memory list。

    query_record example:
    {
        "aspect": ["study", "language_learning"],
        "entities": ["japanese", "weekly plan"],
        "memory_summary": "User wants to reschedule japanese study planning",
        "sentiment": "positive"
    }
    """
    # 1. set document store（from jsonl）
    document_store = build_document_store_from_jsonl(file_path, model_path)

    # 2. If the memory store is empty, return False
    all_docs = document_store.filter_documents()
    if not all_docs:
        return False

    # 3. Filter by aspect first
    if use_filter:
        query_aspect = canonical_key(query_record.get("aspect"))
        filters = {
            "operator": "AND",
            "conditions": [
                {
                    "field": "meta.aspect_key",
                    "operator": "==",
                    "value": query_aspect,
                }
            ],
        }

        filter_retriever = FilterRetriever(document_store=document_store)
        filtered_docs = filter_retriever.run(filters=filters)["documents"]

        if not filtered_docs:
            return []
    else:
        filters = None

    # 4. Compute embeddings for memory_summary of query
    query_text = query_record.get("memory_summary", "")
    if not query_text:
        return []

    text_embedder = SentenceTransformersTextEmbedder(
        model=model_path,
        progress_bar=False
    )
    text_embedder.warm_up()
    query_embedding = text_embedder.run(text=query_text)["embedding"]


    # 5. Apply embedding top-k retrieval to the filtered subset
    retriever = InMemoryEmbeddingRetriever(
        document_store=document_store,
        top_k=top_k,
    )
    if use_filter:
        result = retriever.run(
            query_embedding=query_embedding,
            filters=filters,
            top_k=top_k,
        )["documents"]
    else:
        result = retriever.run(
            query_embedding=query_embedding,
            top_k=top_k,
        )["documents"]

    # threshold
    result = [
        doc for doc in result
        if doc.score is not None and doc.score >= threshold
    ]

    if not result:
        return []


    # 6. Restore original memory format
    retrieved_memories = []
    for doc in result:
        retrieved_memories.append(
            {
                "memory_id": doc.meta.get("memory_id"),
                "aspect": doc.meta.get("aspect", []),
                "intent": doc.meta.get("intent", []),
                "entities": doc.meta.get("entities", []),
                "memory_summary": doc.content,
                "sentiment": doc.meta.get("sentiment"),
                "score": doc.score,
            }
        )

    return retrieved_memories