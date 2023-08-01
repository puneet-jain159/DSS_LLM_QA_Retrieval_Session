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
# config['model_id'] = 'meta-llama/Llama-2-70b-chat-hf'
config['model_id'] = 'meta-llama/Llama-2-13b-chat-hf'
# config['model_id'] = 'mosaicml/mpt-30b-chat'
username = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().apply('user')
config['use_azure_formrecognizer'] = True

# COMMAND ----------

# DBTITLE 1,Create database
config['database_name'] = 'qabot'

# create database if not exists
_ = spark.sql(f"create database if not exists {config['database_name']}")

# set current datebase context
_ = spark.catalog.setCurrentDatabase(config['database_name'])

# COMMAND ----------

# DBTITLE 1,Set Environmental Variables for tokens
import os

if config['model_id'] == 'openai':
  os.environ['OPENAI_API_KEY'] = 'xxxxxxxx'

if "LLAMA-2" in config['model_id']:
  config['HUGGING_FACE_HUB_TOKEN'] = 'xxxxxxxx'

# COMMAND ----------

# DBTITLE 1,Set document path
config['loc'] = f"/dbfs/FileStore/insurance_policy_doc/"
config['vector_store_path'] = f"/dbfs/{username}/qabot/vector_store/{config['model_id']}/{config['use-case']}" # /dbfs/... is a local file system representation

# COMMAND ----------

if config['use_azure_formrecognizer'] == True:
  config['formendpoint'] = 'xxxxxx'
  config['formkey'] = 'xxxxxxx'

# COMMAND ----------

# DBTITLE 1,mlflow settings
import mlflow
config['registered_model_name'] = f"{config['use-case']}"
config['model_uri'] = f"models:/{config['registered_model_name']}/production"
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
  config['embedding_model'] = 'intfloat/e5-large-v2'

  # Model parameters
  config['model_kwargs'] = {}
  config['pipeline_kwargs']={"temperature":  0.10,
                            "max_new_tokens": 256}
  
  config['template'] = """<|im_start|>system\n-You are a helpful assistant chatbot trained by MosaicML. You are good at helping to answer a question based on the context provided, the context is a document. \n-If the question doesn't form a complete sentence, just say I don't know.\n-If the context is irrelevant to the question, just say I don't know.,\n-If there is a good answer from the context, try to summarize the answer to the question. \n<|im_end|>\n<|im_start|>user\n Given the context: {context}. Answer the question {question} <|im_end|><|im_start|>assistant\n""".strip()

elif config['model_id'] == 'meta-llama/Llama-2-13b-chat-hf' :
  # Setup prompt template ####
  config['embedding_model'] = 'intfloat/e5-large-v2'
  config['model_kwargs'] = {}
  
  # Model parameters
  config['pipeline_kwargs']={"temperature":  0.10,
                            "max_new_tokens": 256}
  
  config['template'] = """<s>[INST] <<SYS>>
    You are a assistant built to answer policy related questions based on the context provided, the context is a document and use no other information.
    <</SYS>> Given the context: {context}. Answer the question {question} \n
     If the context does not provide enough relevant information to determine the answer, just say I don't know. If the context is irrelevant to the question, just say I don't know. If you did not find a good answer from the context, just say I don't know. If the query doesn't form a complete question, just say I don't know. only answer the question asked
    [/INST]""".strip()

elif config['model_id'] == 'meta-llama/Llama-2-70b-chat-hf' :
  # Setup prompt template ####
  config['embedding_model'] = 'intfloat/e5-large-v2'
  
  config['model_kwargs'] = {"load_in_8bit" : True}

  # Model parameters
  config['pipeline_kwargs']={"temperature":  0.10,
                            "max_new_tokens": 256}
  
  config['template'] = """<s>[INST] <<SYS>>
    You are a assistant built to answer policy related questions based on the context provided, the context is a document and use no other information.
    <</SYS>> Given the context: {context}. Answer the question {question} \n
     If the context does not provide enough relevant information to determine the answer, just say I don't know. If the context is irrelevant to the question, just say I don't know. If the query doesn't form a complete question, just say I don't know.
    [/INST]""".strip()





# COMMAND ----------

# DBTITLE 1,Set evaluation config
# config["eval_dataset_path"]= "./data/eval_data.tsv"
