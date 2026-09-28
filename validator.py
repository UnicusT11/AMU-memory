# Copyright 2026 UnicusT11
# SPDX-License-Identifier: Apache-2.0
#
# Validation and parsing utilities for AMU.
#
# This module validates, parses, and combines intermediate model outputs
# used throughout the AMU memory write and retrieval pipelines.

import json
import re

class assistantFilter:
    def __init__(self, generate_text):
        self.generate_text = generate_text
        self.VALID_ASPECT = {
            "personal_profile", "social_relationship", "activity", "preference", "health", "other"
        }

        self.VALID_INTENT = {
            "request", "inform", "reflect",
            "express", "plan", "other"
        }

        self.VALID_HEALTH_MAP = {
            "mental_health", "mental_illness", "physical_health",
            "physical_illness", "illness", "symptom"
        }

        self.VALID_ACTIVITY_MAP = {
            "work"
        }


    def json_extract(self):
        matches = re.findall(r'\{.*?\}', self.generate_text, re.DOTALL)

        if len(matches) != 1:
            return None
        return matches[0]

    def clean_entities(self, entities):
        INVALID_ENTITIES = [[""], [" "], ["null"], ["none"], ["undefined"]]
        cleaned = []

        if entities in INVALID_ENTITIES:
            entities = cleaned
        return entities

    def validate_and_parse(self):
        json_str = self.json_extract()

        try:
            data = json.loads(json_str)
        except:
            return False

        # Required fields
        required_keys = [
            "aspect",
            "intent",
            "is_personal",
            "entities"
        ]

        # Check field completeness
        for key in required_keys:
            if key not in data:
                return False

        # Type check
        if data["aspect"] in self.VALID_HEALTH_MAP:
            data["aspect"] = "health"

        if data["aspect"] in self.VALID_ACTIVITY_MAP:
            data["aspect"] = "activity"

        if data.get("aspect") not in self.VALID_ASPECT:
            return False

        if data.get("intent") not in self.VALID_INTENT:
            return False

        if not isinstance(data["entities"], list):
            return False

        if not isinstance(data["is_personal"], bool):
            return False

        return data

    def reuse_function(self):
        data = self.validate_and_parse()
        if data:
            entities_score = len(self.clean_entities(data["entities"]))
            personal_score = 1 if data["is_personal"] else 0
            task_score = 0 if data["intent"] == "request" else 1
            reuse_score = entities_score * personal_score * task_score
            # #=======
            # # w/o Structure
            # reuse_score = True
            # data.pop("is_personal", None)
            # #=======
            if reuse_score:
                data.pop("is_personal", None)
                return True, data
            else:
                return False, data

        else:
            return False, data


class resultCombine:
    def __init__(self, generate_text):
        self.generate_text = generate_text
    def json_extract(self):
        matches = re.findall(r'\{.*?\}', self.generate_text, re.DOTALL)

        if len(matches) != 1:
            return None
        return matches[0]

    def clean_memory_summary(self, memory_summary):
        INVALID_ENTITIES = [[""], [" "], ["null"], ["none"], ["undefined"]]
        cleaned = []

        if memory_summary in INVALID_ENTITIES:
            memory_summary = cleaned
        return memory_summary

    def validate_parse(self):
        json_str = self.json_extract()

        try:
            data = json.loads(json_str)
        except:
            return False

        # Required fields
        required_keys = [
            "memory_summary",
            "sentiment",
            "confidence"
        ]

        # Check field completeness
        for key in required_keys:
            if key not in data:
                return False

        # Type check
        if not isinstance(data["memory_summary"], str):
            return False

        if not isinstance(data["sentiment"], str):
            return False

        return data

    def result_function(self, threshold):
        data = self.validate_parse()
        if data:
            summary_score = 1 if len(self.clean_memory_summary(data["memory_summary"])) else 0
            try:
                confidence = float(data["confidence"])
            except (ValueError, TypeError):
                confidence = 0.0  # fallback
            if summary_score * confidence >= threshold:
                data.pop("confidence", None)
                return True, data
            else:
                return False, data

        else:
            return False, data


class memoryFilter:
    def __init__(self, generate_text):
        self.generate_text = generate_text

        self.VALID_RELATION = {
            "separate", "update", "duplicate"
        }

    def json_extract(self):
        matches = re.findall(r'\{.*?\}', self.generate_text, re.DOTALL)

        if len(matches) != 1:
            return None
        return matches[0]

    def validate_and_parse(self, threshold):
        json_str = self.json_extract()

        try:
            data = json.loads(json_str)
        except:
            return False

        # Required fields
        required_keys = [
            "relation",
            "confidence"
        ]

        # Check field completeness
        for key in required_keys:
            if key not in data:
                return False

        # Type check
        if data.get("relation") not in self.VALID_RELATION:
            return False

        if data["confidence"] <= threshold:
            return False

        return data

class updateFilter:
    def __init__(self, generate_text):
        self.generate_text = generate_text

        self.VALID_SENTIMENT = {
            "positive", "neutral", "negative"
        }

    def json_extract(self):
        matches = re.findall(r'\{.*?\}', self.generate_text, re.DOTALL)

        if len(matches) != 1:
            return None
        return matches[0]

    def validate_and_parse(self):
        json_str = self.json_extract()

        try:
            data = json.loads(json_str)
        except:
            return False

        # Required fields
        required_keys = [
            "entities",
            "memory_summary",
            "sentiment"
        ]

        # Check field completeness
        for key in required_keys:
            if key not in data:
                return False

        # Type check
        if data.get("sentiment") not in self.VALID_SENTIMENT:
            return False

        return data


class readFilter:
    def __init__(self, generate_text):
        self.generate_text = generate_text
        self.VALID_ASPECT = {
            "personal_profile", "social_relationship", "activity", "preference", "health", "other"
        }

        self.VALID_INTENT = {
            "request", "inform", "reflect",
            "express", "plan", "other"
        }

        self.VALID_HEALTH_MAP = {
            "mental_health", "mental_illness", "physical_health",
            "physical_illness", "illness", "symptom"
        }

        self.VALID_ACTIVITY_MAP = {
            "work"
        }


    def json_extract(self):
        matches = re.findall(r'\{.*?\}', self.generate_text, re.DOTALL)

        if len(matches) != 1:
            return None
        return matches[0]

    def clean_entities(self, entities):
        INVALID_ENTITIES = [[""], [" "], ["null"], ["none"], ["undefined"]]
        cleaned = []

        if entities in INVALID_ENTITIES:
            entities = cleaned
        return entities

    def validate_and_parse(self):
        json_str = self.json_extract()

        try:
            data = json.loads(json_str)
        except:
            return False

        # Required fields
        required_keys = [
            "aspect",
            "intent",
            "is_personal",
            "entities"
        ]

        # Check field completeness
        for key in required_keys:
            if key not in data:
                return False

        # Type check
        if data["aspect"] in self.VALID_HEALTH_MAP:
            data["aspect"] = "health"

        if data["aspect"] in self.VALID_ACTIVITY_MAP:
            data["aspect"] = "activity"

        if data.get("aspect") not in self.VALID_ASPECT:
            return False

        if data.get("intent") not in self.VALID_INTENT:
            return False

        if not isinstance(data["entities"], list):
            return False

        if not isinstance(data["is_personal"], bool):
            return False

        return data

    def use_function(self):
        data = self.validate_and_parse()
        if data:
            data.pop("is_personal", None)
            return True, data

        else:
            return False, data


class readCombine:
    def __init__(self, generate_text):
        self.generate_text = generate_text

    def json_extract(self):
        matches = re.findall(r'\{.*?\}', self.generate_text, re.DOTALL)

        if len(matches) != 1:
            return None
        return matches[0]

    def clean_memory_summary(self, memory_summary):
        INVALID_ENTITIES = [[""], [" "], ["null"], ["none"], ["undefined"]]
        cleaned = []

        if memory_summary in INVALID_ENTITIES:
            memory_summary = cleaned
        return memory_summary

    def validate_parse(self):
        json_str = self.json_extract()

        try:
            data = json.loads(json_str)
        except:
            return False

        # Required fields
        required_keys = [
            "memory_summary",
            "sentiment",
            "confidence"
        ]

        # Check field completeness
        for key in required_keys:
            if key not in data:
                return False

        # Type check
        if not isinstance(data["memory_summary"], str):
            return False

        if not isinstance(data["sentiment"], str):
            return False

        return data

    def result_function(self, threshold):
        data = self.validate_parse()
        if data:
            summary_score = 1 if len(self.clean_memory_summary(data["memory_summary"])) else 0
            try:
                confidence = float(data["confidence"])
            except (ValueError, TypeError):
                confidence = 0.0  # fallback
            if summary_score * confidence >= threshold:
                data.pop("confidence", None)
                return True, data
            else:
                return False, data

        else:
            return False, data