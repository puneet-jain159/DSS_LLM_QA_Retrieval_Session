import os
import pandas as pd
from langchain.docstore.document import Document
from langchain.document_loaders import PyPDFDirectoryLoader
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential


def preprocess_using_langchain(config):
  '''
  Returns a Dataframe with PDF converted txt in a pandas DF
  '''
  pdf_loader = PyPDFDirectoryLoader(config['loc'])
  docs = pdf_loader.load()
  len(docs)

  import pandas as pd
  df = pd.DataFrame.from_dict({'full_text' : [doc.page_content for doc in docs] ,
                              'source' :[doc.metadata['source'] for doc in docs],
                              'page' :[doc.metadata['page']  for doc in docs]  })
  return df



def preprocess_using_formrecognizer(config):
  '''
  Returns a Dataframe with PDF converted txt in a pandas DF using Azure form recognizer
  '''
  key  = AzureKeyCredential(config["formkey"])
  document_analysis_client = DocumentAnalysisClient(config["formendpoint"],
                                                    key)
  Doc_collection = []

  for subdir, dirs, files in os.walk(config['loc']):
      for file in files:
        with open(os.path.join(config['loc'],file), "rb") as fd:
          document = fd.read()

        poller = document_analysis_client.begin_analyze_document("prebuilt-layout", document)
        result = poller.result()
        print(generate_doc(result))
        Doc_collection.append({
          "full_text" : generate_doc(result),
          "source" : os.path.join(config['loc'],file)
        })
  return pd.DataFrame(Doc_collection)

def generate_doc(result):
  doc = ''
  headers = {}
  t = []
  for table_idx, table in enumerate(result.tables):
      for cell in table.cells:
          t.append(cell.content.replace(":selected:","").replace(":unselected:","").replace("\n","").strip())

  if len(result.paragraphs) > 0:
      for paragraph in result.paragraphs:
          paragraph.content = paragraph.content.replace(":selected:","").replace(":unselected:","").replace("\n","").strip()
          if  (paragraph.content not in t) and (paragraph.role not in ['pageNumber','pageFooter']):
              doc += paragraph.content +'\n'

  for table_idx, table in enumerate(result.tables):
      doc += "Below is a Table:" + "\n"
      for cell in table.cells:
          cell.content = cell.content.replace(":selected:","").replace(":unselected:","")
          if cell.kind != 'content':
              if cell.kind == 'columnHeader':
                headers[cell.column_index] = cell.content

              doc += f"Cell[{cell.row_index}][{cell.column_index}] as {cell.kind} has text '{cell.content}'" + "\n" 
          else:
              if cell.column_index not in headers:
                doc += f"Cell[{cell.row_index}][{cell.column_index}] has text '{cell.content}'" +"\n"
              else:
                doc += f"Cell[{cell.row_index}][{cell.column_index}] with column heading '{headers[cell.column_index]}' has text '{cell.content}'" +"\n"
  return doc