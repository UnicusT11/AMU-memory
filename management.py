# Copyright 2026 UnicusT11
# SPDX-License-Identifier: Apache-2.0
#
# Memory management utilities for AMU.
#
# This module provides utilities for memory persistence, preprocessing,
# field cleanup, and memory deletion used by the AMU pipeline.

import json
import threading

lock = threading.Lock()

def save_memory_data(content: dict, data_dir, memory_id):
    if memory_id is not None:
        content["memory_id"] = memory_id
    with lock:
        with open(data_dir, "a", encoding="utf-8") as f:
            f.write(json.dumps(content, ensure_ascii=False) + "\n")



def clean_embedding(content: dict):
    content.pop("embedding", None)
    return content

def clean_aspect_intent(content: dict):
    content.pop("aspect", None)
    content.pop("intent", None)
    return content

def delete_memories_by_summary(update_memories, path):

    target_summaries = {
        m.get("memory_summary")
        for m in update_memories
        if m.get("memory_summary") is not None
    }

    kept_records = []
    deleted_count = 0

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)

            if record.get("memory_summary") in target_summaries:
                deleted_count += 1
                continue

            kept_records.append(record)

    with open(path, "w", encoding="utf-8") as f:
        for record in kept_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
