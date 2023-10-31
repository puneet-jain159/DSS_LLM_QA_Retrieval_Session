# Databricks notebook source
import torch

# COMMAND ----------

if 'config' not in locals():
  config = {}

# COMMAND ----------

# DBTITLE 1,Use Case
config['use-case']="insurance_qa_bot"

# COMMAND ----------

# Define the model we would like to use
# config['model_id'] = 'openai'
config['model_id'] = 'meta-llama/Llama-2-13b-chat-hf'
# config['model_id'] = 'meta-llama/Llama-2-13b-chat-hf'
# config['model_id'] = 'mosaicml/mpt-30b-chat'
username = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().apply('user')
config['use_azure_formrecognizer'] = True
config['use_vllm'] = True

# COMMAND ----------

# DBTITLE 1,Create database
config['database_name'] = 'qabot'
config['catalog_name'] = 'mlops_pj'

# create database if not exists
_ = spark.sql(f"use catalog {config['catalog_name']}")

# create database if not exists
_ = spark.sql(f"create database if not exists {config['database_name']}")

# set current datebase context
_ = spark.catalog.setCurrentDatabase(config['database_name'])

# COMMAND ----------

# DBTITLE 1,Set Environmental Variables for tokens
import os

if config['model_id'] == 'openai':
  os.environ['OPENAI_API_KEY'] = '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'

if "Llama-2" in config['model_id']:
  config['HUGGING_FACE_HUB_TOKEN'] = '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'

# COMMAND ----------

# DBTITLE 1,Set document path
config['loc'] = f"/dbfs/FileStore/insurance_policy_doc/"
config['vector_store_path'] = f"/Volumes/mlops_pj/qabot/chroma_index/{config['model_id']}/{config['use-case']}" # /dbfs/... is a local file system representation

# COMMAND ----------

if config['use_azure_formrecognizer'] == True:
  config['formendpoint'] = 'https://howden-test.cognitiveservices.azure.com/'
  config['formkey'] = 'bdbca92002404c2588c729a8a33c6e10'

# COMMAND ----------

# DBTITLE 1,mlflow settings
import mlflow
config['registered_model_name'] = f"{config['use-case']}"
# config['model_uri'] = f"models:/{config['registered_model_name']}/production"
_ = mlflow.set_experiment('/Users/{}/{}'.format(username, config['registered_model_name']))

# COMMAND ----------

# DBTITLE 1,Set model configs
if config['model_id'] == "openai":
  # Set the embedding vector and model  ####
  config['embedding_model'] = 'text-embedding-ada-002'
  config['openai_chat_model'] = "gpt-3.5-turbo"
  # Setup prompt template ####
  config['template'] = """You are a helpful assistant built by Databricks, you are good at helping to answer a question based on the context provided, the context is a document. If the context does not provide enough relevant information to determine the answer, just say I don't know. If the context is irrelevant to the question, just say I don't know. If you did not find a good answer from the context, just say I don't know. If the query doesn't form a complete question, just say I don't know. If there is a good answer from the context, try to summarize the context to answer the question.
  Given the context: {context}. Answer the question {question}."""
  config['temperature'] = 0.15

elif config['model_id'] == 'mosaicml/mpt-30b-chat' :
  # Setup prompt template ####
  config['embedding_model'] = 'BAAI/bge-large-en'

  # Model parameters
  config['model_kwargs'] = {}
  config['pipeline_kwargs']={"temperature":  0.10,
                            "max_new_tokens": 256}
  
  config['template'] = """<|im_start|>system\n- You are a assistant built to answer policy related questions based on the context provided, the context is a document and use no other information.If the context does not provide enough relevant information to determine the answer, just say I don't know. If the context is irrelevant to the question, just say I don't know. If the query doesn't form a complete question, just say I don't know.Only answer the question asked and do not repeat the question. \n<|im_end|>\n<|im_start|>user\n Given the context: {context}. Answer the question {question} <|im_end|><|im_start|>assistant\n""".strip()

elif config['model_id'] == 'meta-llama/Llama-2-13b-chat-hf' :
  # Setup prompt template ####
  config['embedding_model'] = 'BAAI/bge-large-en'
  config['model_kwargs'] = {}
  
  # Model parameters
  config['pipeline_kwargs']={"temperature":  0.05,
                             "top_p": 0.9,
                            "max_new_tokens": 256}
  
  config['template'] = """<s><<SYS>>
  You are a assistant built to answer policy related questions based on the context provided, the context is a document and use no other information.If the context does not provide enough relevant information to determine the answer, just say I don't know. If the context is irrelevant to the question, just say I don't know. If the query doesn't form a complete question, just say I don't know.Only answer the question asked and do not repeat the question
  <</SYS>>[INST] Given the context: {context}. Answer the question {question} ?\n
  [/INST]""".strip()

elif config['model_id'] == 'meta-llama/Llama-2-70b-chat-hf' :
  # Setup prompt template ####
  config['embedding_model'] = 'BAAI/bge-large-en'
  
  config['model_kwargs'] = {"load_in_8bit" : True}

  # Model parameters
  config['pipeline_kwargs']={"temperature":  0.10,
                            "max_new_tokens": 256}
  
  config['template'] = """<s><<SYS>>
  You are a assistant built to answer policy related questions based on the context provided, the context is a document and use no other information.If the context does not provide enough relevant information to determine the answer, just say I don't know. If the context is irrelevant to the question, just say I don't know. If the query doesn't form a complete question, just say I don't know.Only answer the question asked and do not repeat the question
  <</SYS>>[INST] Given the context: {context}. Answer the question {question} ?\n
  [/INST]""".strip()

# COMMAND ----------

# DBTITLE 1,Set evaluation config
config["ui_logs"]= "/Volumes/mlops_pj/qabot/ui_logs"
