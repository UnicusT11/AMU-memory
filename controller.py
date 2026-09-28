# Copyright 2026 UnicusT11
# SPDX-License-Identifier: Apache-2.0
#
# Memory control utilities for AMU.
#
# This module provides control logic for memory storage and matching,
# including memory-saving decisions and exact memory matching.

import json
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parent

data_dir = ROOT /"memory data/memory_emb.jsonl"

def find_exact_match_memory(new_record: dict, memory_list: list):
    new_aspect = new_record.get("aspect", [])
    new_intent = new_record.get("intent", [])

    if isinstance(new_aspect, str):
        new_aspect = [new_aspect]
    if isinstance(new_intent, str):
        new_intent = [new_intent]

    new_aspect_set = set(new_aspect)
    new_intent_set = set(new_intent)

    results = []

    for m in memory_list:
        mem_aspect = m.get("aspect", [])
        mem_intent = m.get("intent", [])

        if isinstance(mem_aspect, str):
            mem_aspect = [mem_aspect]
        if isinstance(mem_intent, str):
            mem_intent = [mem_intent]

        mem_aspect_set = set(mem_aspect)
        mem_intent_set = set(mem_intent)

        if new_aspect_set == mem_aspect_set and new_intent_set == mem_intent_set:
            results.append(m)

    return results if results else False

def memory_save(result):
    memory_list = []
    if not os.path.exists(data_dir):
        return True, None

    else:
        with open(data_dir, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    record = json.loads(line)
                    memory_list.append(record)

        find_result = find_exact_match_memory(result, memory_list)
        # # =======
        # # w/o Structure
        # find_result = memory_list if memory_list else False
        # # =======
        if find_result:
            return False, find_result
        else:
            return True, None


