#!/usr/bin/env python3
import io
import json
import os
import time

from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request
from flask_sock import Sock

import lameenc

from openai import OpenAI


app = Flask(__name__)
sock = Sock(app)

ASR_URL = "https://openrouter.ai/api/v1"
LLM_URL = "https://openrouter.ai/api/v1"

ASR_MODEL_NAME = "qwen/qwen3-asr-flash-2026-02-10"
LLM_MODEL_NAME = "deepseek/deepseek-v4.1-flash"

API_KEY = os.environ["API_KEY"]

def pcm_to_mp3(pcm_bytes: bytes) -> bytes:
    enc = lameenc.Encoder()
    enc.set_bit_rate(16)
    enc.set_in_sample_rate(48000)
    enc.set_channels(1)
    enc.set_quality(2)
    mp3_data = enc.encode(pcm_bytes) + enc.flush()
    return io.BytesIO(mp3_data)

@app.route("/")
def index():
    return render_template('index.html')


def llm_clean(transcript_raw):
    print("Cleaning....")
    llm_client = OpenAI(base_url=LLM_URL, api_key=API_KEY)

    prompt = (
        "Turn the following speech-to-text output into polished text. "
        "Remove disfluencies, remove filler words, and process backtracking, "
        "including commands to start over, or delete the last sentence."
        f" \"{transcript_raw}\""
    )

    try:
        print(prompt)
        resp = llm_client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            extra_body={
                "chat_template_kwargs": {"enable_thinking": False},
            }
        )
        print("Finished cleaning")
        if resp.choices is None:
            # TODO: Hard time reliably reproducing this case!!
            return
        else:
            # return resp.choices[0].message.content
            result = resp.choices[0].message.content
            return result
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print(e)


@sock.route("/clean")
def clean(ws):
    print(f"[+] LLM socket connected: {request.remote_addr}")
    while True:
        msg = ws.receive()
        if msg is None:
            break
        ctrl = json.loads(msg)
        if ctrl.get("type") == "clean":
            cleaned_text = llm_clean(ctrl["text"])
            ws.send(json.dumps({"type": "transcriptWorking", "text": cleaned_text}))
    print(f"[-] LLM socket disconnected: {request.remote_addr}")


@sock.route("/audio")
def audio(ws):
    raw_text = ""
    cleaned_text = ""

    asr_client = OpenAI(base_url=ASR_URL, api_key=API_KEY)

    chunks: list[bytes] = []
    recording = False
    started = 0.0

    print(f"[+] Audio socket connected: {request.remote_addr}")
    try:
        while True:
            msg = ws.receive()
            if msg is None:
                break
            if isinstance(msg, str):
                ctrl = json.loads(msg)
                if ctrl.get("type") == "start":
                    chunks = []
                    recording = True
                    started = time.time()
                    print(f"    ▶ stream started")
                elif ctrl.get("type") == "stop":
                    recording = False
                    pcm = b"".join(chunks)
                    mp3 = pcm_to_mp3(pcm)
                    with open("test2.mp3", "wb") as f:
                        f.write(mp3.getvalue())


                    resp = asr_client.audio.transcriptions.create(
                        model=ASR_MODEL_NAME,
                        file=mp3,
                        temperature=0,
                        response_format="json"
                    )

                    ws.send(json.dumps({"type": "transcriptRaw", "text": resp.text}))

            elif recording:
                chunks.append(msg)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print(e)
    finally:
        print(f"[-] Audio socket disconnected: {request.remote_addr}")

if __name__ == "__main__":
    # threaded=True handles the page + WS nicely for dev use.
    # For production put it behind gunicorn/uvicorn instead.
    app.debug = True
    app.run(host="0.0.0.0", port=8080, threaded=True)

