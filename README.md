# DIY QA LLM BOT
This a repo to create a QA Retrieval Bot using both Open LLM as well as OpenAI in Databricks.\n
To get started please change the configuration notebook in util/notebook-config.py. 

Please look at the documentation Below on configuration for specific LLM's

## LLM's Supported
Currently the code supports the following version 
- [Open AI](#runnig-the-code-using-open-ai)
- [MPT-30b Chat version](#runnig-the-code-using-mosiac-mpt-models)
- [Llama-2-13b HF-chat version](#runnig-the-code-using-llama-2-models)
- [Llama-2-7-b HF-chat version with 8-bit Quantization](#runnig-the-code-using-llama-2-models)

## Runtime Tested
The following code is tested on ML DBR GPU 13.2 Runtime

## Cluster Configurations
It Code to run open LLMS has been tested on the below single node cluster configurations:
- AWS : g5-12xlarge
- Azure : NC24Ads_A100_v4

## Coverting PDF to txt
There are two ways to convert the PDF to TXT

- **Using Azure Form Recognizer**
To use form recognizer you need to add 
```
config['use_azure_formrecognizer'] = True
and add the URL and KEY from the Azure portal 
config['formendpoint'] 
config['formkey']
```
- Using Langchain PDF converter
set
```
config['use_azure_formrecognizer'] = False
```
## Runnig the code using Open AI
You can use any cluster to run the OpenAI model and need to set the following configs
```
config['model_id'] == 'openai'
os.environ['OPENAI_API_KEY'] = '<your open AI API Key>'
```
Note : **when using OpenAI you do not need to run the 02_load_model Notebook**

## Runnig the code using LLAMA-2 Models:
To use LLAMA-2 models, you need to agree to the terms and condition of HuggingFace and provide an API key to download the models
Refer to these steps to download the key : https://huggingface.co/docs/api-inference/quicktour#get-your-api-token and set the below parameters
```
config['model_id'] == 'meta-llama/Llama-2-XXb-chat-hf'
config['HUGGING_FACE_HUB_TOKEN'] = '<your HF AI API Key>'
```
Note : to need to keep 02_load_model Notebook running to have the API running


## Runnig the code using Mosiac MPT models:
you need to set the below config
```
config['model_id'] == 'mosaicml/mpt-30b-chat'
```
Note : to need to keep 02_load_model Notebook running to have the API running

## Embedding Model
The current notebook use the following the embedding models
- For openAI : text-embedding-ada-002
- All open LLM's : intfloat/e5-large-v2

The open LLM embedding can be changed by over-riding the Dictionary in utils/notebook-config.py
