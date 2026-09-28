# Copyright 2026 UnicusT11
# SPDX-License-Identifier: Apache-2.0
#
# AMU Main Pipeline
#
# This module implements the core memory write and retrieval pipelines
# of AMU, including memory extraction, embedding-based similarity matching,
# memory deduplication and updating, persistent storage, and RAG-based retrieval.
import json
import numpy as np
from pathlib import Path
from SLM import generate_text, append_content, embed_func, Similarity, append_mem, append_update
from validator import assistantFilter, resultCombine, memoryFilter, updateFilter, readFilter, readCombine
from controller import memory_save, find_exact_match_memory
from management import save_memory_data, clean_embedding, clean_aspect_intent, delete_memories_by_summary
from rag_haystack import retrieve_memory_with_haystack
ROOT = Path(__file__).resolve().parent

def add_embedding(record: dict, embed_func):
    text = record.get("memory_summary", "")

    embedding = embed_func(text)

    record["embedding"] = embedding
    return record



def embedding_similarity(record: dict, emb_memory_list: list, threshold: float = 0.6):

    memory_list = []
    data_dir = ROOT /"memory data/memory.jsonl"
    with open(data_dir, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                mem_record = json.loads(line)
                memory_list.append(mem_record)

    query_emb = record.get("embedding", "")

    emb_list = []

    for m in emb_memory_list:
        emb = m.get("embedding", "")
        emb_list.append(emb)

    emb_matrix = np.array(emb_list, dtype=np.float32)
    query = np.array(query_emb, dtype=np.float32)

    #computing similarity score
    score = Similarity(query, emb_matrix)

    #threshold
    idx = np.where(score >= threshold)[0]

    if len(idx) == 0:
        return False, None
    else:

        # # =======
        # # w/o Structure
        # memory_result = memory_list
        # # =======
        memory_result = find_exact_match_memory(record, memory_list)
        similarity_list = [memory_result[i] for i in idx]

        return True, similarity_list


def write_pipeline(input_text, memory_id=None, language="English"):
    threshold_save = 0.8

    # =========================
    # Loading prompt
    # =========================
    input_text = input_text.replace("\n", " ")
    with open(ROOT /f"PROMPT/{language}/prompt stage1.txt", "r", encoding="utf-8") as f:
        prompt_stage1 = f.read()
    with open(ROOT /f"PROMPT/{language}/prompt stage2.txt", "r", encoding="utf-8") as f:
        prompt_stage2 = f.read()

    # =========================
    #Stage1
    # =========================
    stage1_result = generate_text(input_text, prompt_stage1)
    Filter = assistantFilter(stage1_result)
    reuse_score, stage1_data = Filter.reuse_function()
    if not reuse_score:
        return "filter"
    if reuse_score:

        # =========================
        #Stage2
        # =========================
        stage2_input = append_content(input_text, stage1_result)
        content_result = generate_text(stage2_input, prompt_stage2)
        resultFilter = resultCombine(content_result)
        final_score, stage2_data = resultFilter.result_function(threshold_save)
        #Final result
        if not final_score:
            return "filter"
        if final_score:
            final_result = {**stage1_data, **stage2_data}
            # print(final_result)
            final_embedded_result = add_embedding(final_result, embed_func)

            save_continue, memory_list = memory_save(final_embedded_result)

            # =========================
            # No matching aspect and intent found in memory
            # =========================
            if save_continue:

                # Save embedding memory
                save_memory_data(final_embedded_result, ROOT /"memory data/memory_emb.jsonl", memory_id)

                # Save no embedding memory
                mem_no_emb = clean_embedding(final_embedded_result)
                save_memory_data(mem_no_emb, ROOT /"memory data/memory.jsonl", memory_id)
                return "store"

            else:
                # return "discard"
                # Embedding similarity computing
                similarity_score, similarity_data = embedding_similarity(final_embedded_result, memory_list)

                if not similarity_score:

                    # Save low-similarity memories (below threshold)
                    save_memory_data(final_embedded_result, ROOT /"memory data/memory_emb.jsonl", memory_id)

                    mem_no_emb = clean_embedding(final_embedded_result)
                    save_memory_data(mem_no_emb, ROOT /"memory data/memory.jsonl", memory_id)
                    return "store"

                else:

                    # =========================
                    # There exists a similarity score above the threshold
                    # =========================
                    relation_list = []
                    save_emb_ = final_embedded_result.copy()

                    mem_no_emb = clean_embedding(final_embedded_result)
                    save_mem_ = mem_no_emb.copy()

                    replace_relation = {'relation': 'none', 'confidence': 'none'}

                    with open(ROOT /f"PROMPT/{language}/memory stage1.txt", "r", encoding="utf-8") as f:
                        memory_stage1 = f.read()

                    # =========================
                    # SLM to compare memories one by one and classify them as update, separate, duplicate
                    # =========================
                    for similar_ in similarity_data:
                        mem_combine = append_mem(clean_aspect_intent(similar_), clean_aspect_intent(mem_no_emb))

                        mem_relation = generate_text(mem_combine, memory_stage1)
                        memF = memoryFilter(mem_relation)
                        relation_score = memF.validate_and_parse(threshold=0.7)
                        if relation_score:
                            relation_list.append(relation_score)
                        else:
                            relation_list.append(replace_relation)

                    # Get label of update, separate, duplicate
                    relation_field = [item.get("relation") for item in relation_list]


                    if not all(r == 'none' for r in relation_field):

                        # No memory classified as update
                        if 'update' not in relation_field:

                            # No memory classified as duplicate
                            if 'duplicate' not in relation_field:
                                save_memory_data(save_emb_, ROOT /"memory data/memory_emb.jsonl", memory_id)
                                save_memory_data(save_mem_, ROOT /"memory data/memory.jsonl", memory_id)
                                return "store"
                            else:
                                return "discard"

                        else:

                            # =========================
                            # Update exists
                            # =========================

                            # Delete duplicate memory
                            duplicate_idx = [
                                i for i, r in enumerate(relation_field)
                                if r == 'duplicate'
                            ]

                            del_dupl = [similarity_data[i] for i in duplicate_idx]  #Find duplicate memories
                            # Delete
                            delete_memories_by_summary(del_dupl, ROOT /"memory data/memory.jsonl")
                            delete_memories_by_summary(del_dupl, ROOT /"memory data/memory_emb.jsonl")

                            # Merge updates with user input
                            update_idx = [
                                i for i, r in enumerate(relation_field)
                                if r == 'update'
                            ]
                            # Find update memory and merge with user input
                            update_memory = [similarity_data[i] for i in update_idx]
                            up = append_update(update_memory, mem_no_emb)

                            # SLM-based memory merging
                            with open(ROOT /f"PROMPT/{language}/memory stage2.txt", "r", encoding="utf-8") as f:
                                memory_stage2 = f.read()

                            gen_update = generate_text(up, memory_stage2)
                            upF = updateFilter(gen_update)

                            # Filter after merging
                            upF_data = upF.validate_and_parse()
                            if upF_data:

                                # Update user input
                                save_emb_["entities"] = upF_data["entities"]
                                save_emb_["memory_summary"] = upF_data["memory_summary"]
                                save_emb_["sentiment"] = upF_data["sentiment"]
                                save_emb_["embedding"] = embed_func(upF_data["memory_summary"])

                                save_mem_["entities"] = upF_data["entities"]
                                save_mem_["memory_summary"] = upF_data["memory_summary"]
                                save_mem_["sentiment"] = upF_data["sentiment"]

                            # Delete old memory
                            delete_memories_by_summary(update_memory, ROOT /"memory data/memory.jsonl")
                            delete_memories_by_summary(update_memory, ROOT /"memory data/memory_emb.jsonl")

                            save_memory_data(save_emb_, ROOT /"memory data/memory_emb.jsonl", memory_id)
                            save_memory_data(save_mem_, ROOT /"memory data/memory.jsonl", memory_id)

                            return "update"


def read_pipeline(input_text, language="English"):
    threshold_read = 0.8

    # =========================
    # Loading prompt
    # =========================
    input_text = input_text.replace("\n", " ")
    with open(ROOT /f"PROMPT/{language}/prompt stage1.txt", "r", encoding="utf-8") as f:
        prompt_stage1 = f.read()
    with open(ROOT /f"PROMPT/{language}/prompt read.txt", "r", encoding="utf-8") as f:
        prompt_stage2 = f.read()

    # =========================
    # Stage1
    # =========================
    stage1_result = generate_text(input_text, prompt_stage1)
    Filter = readFilter(stage1_result)
    use_score, stage1_data = Filter.use_function()
    if use_score:

        # =========================
        # Stage2
        # =========================
        stage2_input = append_content(input_text, stage1_result)
        content_result = generate_text(stage2_input, prompt_stage2)
        resultFilter = readCombine(content_result)
        final_score, stage2_data = resultFilter.result_function(threshold_read)

        #Final result
        if final_score:
            final_result = {**stage1_data, **stage2_data}
            # print(final_result)
            # RAG
            retrieved_memories = retrieve_memory_with_haystack(
                final_result,
                str(ROOT /"memory data/memory.jsonl"),
                str(ROOT /"./embedding models/qwen3-embedding-0.6b"),
                top_k=3,
                threshold=0.55,
                use_filter=True
            )

            # Get memory
            read_memory = [
                m.get("memory_summary")
                for m in retrieved_memories
                if m.get("memory_summary") is not None
            ]

            # retrieved_ids = [
            #     a.get("memory_id")
            #     for a in retrieved_memories
            #     if a.get("memory_id") is not None
            # ]
            #
            # if retrieved_ids is None:
            #     return []
            # return retrieved_ids, read_memory

            memory_block = "\n".join(
                [f"[Memory {i + 1}]\n{s}" for i, s in enumerate(read_memory)]
            )

            prompt = f"""Relevant memories:\n{memory_block}\nUse only if relevant. If conflict exists, follow the current message. Do not mention the memories."""

            return prompt





