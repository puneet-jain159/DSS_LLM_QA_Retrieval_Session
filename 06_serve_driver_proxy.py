# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # Serving Llama-2-70b-chat-hf with a cluster driver proxy app

# COMMAND ----------

# MAGIC %md
# MAGIC ## Serve with Flask

# COMMAND ----------

from dbruntime.databricks_repl_context import get_context
ctx = get_context()

port = "8880"
driver_proxy_api = f"https://{ctx.browserHostName}/driver-proxy-api/o/0/{ctx.clusterId}/{port}"

print(f"""
driver_proxy_api = '{driver_proxy_api}'
cluster_id = '{ctx.clusterId}'
port = {port}
""")

# COMMAND ----------


import argparse
import json
from typing import Iterable, List

import requests

def clear_line(n: int = 1) -> None:
    LINE_UP = '\033[1A'
    LINE_CLEAR = '\x1b[2K'
    for _ in range(n):
        print(LINE_UP, end=LINE_CLEAR, flush=True)


def post_http_request(prompt: str,
                      api_url: str,
                      token : str,
                      stream: bool = False) -> requests.Response:
    headers = {
        "Content-Type": "application/json",
        "Authentication": f"Bearer {token}"}
    pload = {
        "prompt": prompt,
        "temperature": 0.15,
        "max_tokens": 256,
        "top_p" : 0.6,
        "top_k" : 50,

        "stream": stream,
    }
    response = requests.post(api_url, headers=headers, json=pload, stream=True)
    return response


def get_streaming_response(response: requests.Response) -> Iterable[List[str]]:
    for chunk in response.iter_lines(chunk_size=8192,
                                     decode_unicode=False,
                                     delimiter=b"\0"):
        if chunk:
            data = json.loads(chunk.decode("utf-8"))
            output = data["text"]
            yield output


def get_response(response: requests.Response) -> List[str]:

    data = json.loads(response.content)
    output = data["text"]
    return output

# COMMAND ----------

prompt = "What is PWC?"
token = '<Enter token here>'
api_url = f"{driver_proxy_api}/generate"
stream = False

print(f"Prompt: {prompt!r}\n", flush=True)
response = post_http_request(prompt, api_url,token, stream)
print(response)

if stream:
    num_printed_lines = 0
    for h in get_streaming_response(response):
        clear_line(num_printed_lines)
        num_printed_lines = 0
else:
    output = get_response(response)
    print(f"output {output[0]}", flush=True)

# COMMAND ----------


