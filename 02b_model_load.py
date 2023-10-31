# Databricks notebook source
# MAGIC %run "./util/notebook-config"

# COMMAND ----------

# MAGIC %md
# MAGIC **This notebook is not required if you want to run the OpenAI model**

# COMMAND ----------

if config['model_id'] == "openai":
  raise "Notebook note required , Use this notebook to run on when using open LLM. change the config"

# COMMAND ----------

# MAGIC %md
# MAGIC **Install vllm Dependencies**

# COMMAND ----------

# MAGIC %pip install vllm torch==2.0.1 safetensors==0.3.1 accelerate==0.20.3 ray[default]

# COMMAND ----------

# import os 
nodeid = spark.conf.get('spark.databricks.driverNodeTypeId')
if "A100" in nodeid:
  os.environ['sharded'] = 'false'
  os.environ['CUDA_VISIBLE_DEVICES'] = "0"
else:
  os.environ['sharded'] = 'true'
  os.environ['CUDA_VISIBLE_DEVICES'] = "0,1,2,3"

if "Llama-2" in config['model_id']: 
  os.environ['HUGGING_FACE_HUB_TOKEN'] = config['HUGGING_FACE_HUB_TOKEN']
os.environ['HUGGINGFACE_HUB_CACHE'] ='/local_disk0/tmp/'
os.environ['CUDA_MEMORY_FRACTION'] = "0.95"

# get model variables
os.environ['model_id'] = config['model_id']
if "load_in_8bit" in config['model_kwargs']:
  os.environ['quantize'] = "bitsandbytes"
if config['model_id'] != 'meta-llama/Llama-2-70b-chat-hf':
  os.environ['CUDA_MEMORY_FRACTION'] = ".9"


# COMMAND ----------

# MAGIC %sh
# MAGIC if [ -z ${quantize} ]; 
# MAGIC     then  python -m vllm.entrypoints.api_server --model $model_id --port 8880 --gpu-memory-utilization $CUDA_MEMORY_FRACTION ;
# MAGIC else echo "quantize" && python -m vllm.entrypoints.api_server --model $model_id --port 8880 --gpu-memory-utilization $CUDA_MEMORY_FRACTION -q awq ;
# MAGIC fi
# MAGIC

# COMMAND ----------


