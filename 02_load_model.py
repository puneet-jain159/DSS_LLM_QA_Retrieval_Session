# Databricks notebook source
# MAGIC %md 
# MAGIC ### This is the notebook to run the Open LLM's as an Web Service
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC **This notebook is not required if you want to run the OpenAI model**

# COMMAND ----------

if config['model_id'] == "openai":
  raise "Notebook note required , Use this notebook to run on when using open LLM. change the config"

# COMMAND ----------

# MAGIC %pip install torch==2.0.1

# COMMAND ----------

# MAGIC %sh
# MAGIC wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
# MAGIC sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
# MAGIC sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/3bf863cc.pub
# MAGIC sudo add-apt-repository -y "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
# MAGIC sudo apt-get update
# MAGIC
# MAGIC apt-get install -y libcusparse-dev-11-7 libcublas-dev-11-7 libcusolver-dev-11-7

# COMMAND ----------

# MAGIC %sh
# MAGIC # install rust
# MAGIC curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs > tmp.sh
# MAGIC sh tmp.sh -y
# MAGIC source "$HOME/.cargo/env"
# MAGIC
# MAGIC # install protoc
# MAGIC PROTOC_ZIP=protoc-21.12-linux-x86_64.zip
# MAGIC curl -OL https://github.com/protocolbuffers/protobuf/releases/download/v21.12/$PROTOC_ZIP
# MAGIC sudo unzip -o $PROTOC_ZIP -d /usr/local bin/protoc
# MAGIC sudo unzip -o $PROTOC_ZIP -d /usr/local 'include/*'
# MAGIC rm -f $PROTOC_ZIP
# MAGIC
# MAGIC # install text-generation-inference
# MAGIC rm -rf  /local_disk0/tmp/text-generation-inference
# MAGIC cd /local_disk0/tmp && git clone https://github.com/huggingface/text-generation-inference.git  --branch v1.0.0
# MAGIC cd /local_disk0/tmp/text-generation-inference && make install
# MAGIC
# MAGIC # install flash-attention
# MAGIC cd server && make install install-flash-attention  && make install install-flash-attention-v2 && make install-vllm
# MAGIC  
# MAGIC # correct the pip libraries
# MAGIC pip install urllib3==1.25.4
# MAGIC pip install protobuf==3.20.*

# COMMAND ----------

 dbutils.library.restartPython() 

# COMMAND ----------

# MAGIC %run "./util/notebook-config"

# COMMAND ----------

import os 
nodeid = spark.conf.get('spark.databricks.driverNodeTypeId')
if "A100" in nodeid:
  os.environ['sharded'] = 'false'
  os.environ['CUDA_VISIBLE_DEVICES'] = "0"
else:
  os.environ['sharded'] = 'true'
  os.environ['CUDA_VISIBLE_DEVICES'] = "0,1,2,3"


os.environ['HUGGING_FACE_HUB_TOKEN'] = config['HUGGING_FACE_HUB_TOKEN']
os.environ['HUGGINGFACE_HUB_CACHE'] ='/local_disk0/tmp/'
os.environ['CUDA_MEMORY_FRACTION'] = "1"

# get model variables
os.environ['model_id'] = config['model_id']
if "load_in_8bit" in config['model_kwargs']:
  os.environ['quantize'] = "bitsandbytes"
if config['model_id'] != 'meta-llama/Llama-2-70b-chat-hf':
  os.environ['CUDA_MEMORY_FRACTION'] = ".8"


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

# MAGIC %sh
# MAGIC source "$HOME/.cargo/env"
# MAGIC
# MAGIC if [ -z ${quantize} ]; 
# MAGIC     then echo "quantize" && text-generation-launcher --model-id $model_id --port 8880 --trust-remote-code --sharded $sharded --max-input-length 2048 --max-total-tokens 4096 ;
# MAGIC else text-generation-launcher --model-id $model_id --port 8880 --trust-remote-code --sharded $sharded --max-input-length 2048 --max-total-tokens 4096 --quantize bitsandbytes  ;
# MAGIC fi
# MAGIC

# COMMAND ----------

! kill -9  $(ps aux | grep 'text-generation' | awk '{print $2}')

# COMMAND ----------


