# Copyright 2026 UnicusT11
# SPDX-License-Identifier: Apache-2.0
#
# API entry point for AMU.
#
# This module exposes the AMU memory pipelines through the API interface
# and handles the configuration required to connect API requests with
# the core pipeline.

import uvicorn
import os
import time
import threading
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pipeline import write_pipeline, read_pipeline


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    text: str
    mode: str
    time: int | None = None

@app.get("/health")

def health():

    return {"status": "ok"}

@app.post("/shutdown")

def shutdown():

    def _kill():
        time.sleep(0.5)
        os._exit(0)

    threading.Thread(target=_kill, daemon=True).start()
    return {"status": "shutting down"}

@app.post("/save")
def save_message(msg: Message):
    input_text = msg.text
    if msg.mode == "retrieve":
        output_prompt = read_pipeline(input_text)
        return {
            "status": "success",
            "data": output_prompt
        }
    elif msg.mode == "save":
        write_pipeline(input_text)
        return {
            "status": "success"
        }

    return {
        "status": "success"
    }

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=8800,
        reload=False,
                )