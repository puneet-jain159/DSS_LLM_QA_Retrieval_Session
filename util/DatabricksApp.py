import uvicorn
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from dataclasses import dataclass
import gradio as gr
import json

@dataclass
class ProxySettings:
  proxy_url: str
  port: str
  url_base_path: str

from subprocess import Popen, PIPE
import os

import subprocess

def execute(cmd, env):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True,stderr=subprocess.PIPE,env=env)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line 
    for stderr_line in iter(popen.stderr.readline, ""):
      yield stderr_line 
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        print
        raise subprocess.CalledProcessError(return_code, cmd)

def run_streamlit(path, port):
  my_env = os.environ.copy()
  my_env["STREAMLIT_SERVER_PORT"] = f"{port}"
  my_env["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
  my_env["STREAMLIT_SERVER_HEADLESS"] = "true"
  process = subprocess.run(f"kill -9 $(lsof -t -i:{port})", capture_output=True, shell=True) 

  print(f"Deploying streamlit app at path: {path} on port: {port}")
  cmd = ["streamlit",
        "run",
        path,
        "--browser.gatherUsageStats",
        "false"]
  print(f"Running command: {' '.join(cmd)}")
  for path in execute(cmd, my_env):
      print(path, end="")
  
class DatabricksApp:
  
  def __init__(self, port):   
    # self._fastapi_app = self._make_fastapi_app()
    # self._app = data_app
    self._port = port
    import IPython
    self._dbutils = IPython.get_ipython().user_ns["dbutils"]
    self._display_html = IPython.get_ipython().user_ns["displayHTML"]
    self._context = json.loads(self._dbutils.notebook.entry_point.getDbutils().notebook().getContext().toJson())
    # need to do this after the context is set    
    self._cloud = self.get_cloud()
    # create proxy settings after determining the cloud
    self._ps = self.get_proxy_settings()
    self._fastapi_app = self._make_fastapi_app()
    self._streamlit_script = None

    # after everything is set print out the url   

  
  def _make_fastapi_app(self) -> FastAPI:
    fast_api_app = FastAPI(root_path=self._ps.url_base_path)
    # @fast_api_app.get("/")
    # def read_main():
    #     return {
    #         "routes": [
    #             {"method": "GET", "path": "/", "summary": "Landing"},
    #             {"method": "GET", "path": "/status", "summary": "App status"},
    #             {"method": "GET", "path": "/dash", "summary": "Sub-mounted Dash application"},
    #         ]
    #     }
    # @fast_api_app.get("/status")
    # def get_status():
    #     return {"status": "ok"}
    return fast_api_app
    
  def get_proxy_settings(self) -> ProxySettings:
    if self._cloud.lower() not in ["aws", "azure"]:
      raise Exception("only supported in aws or azure")
    prefix_url_settings = {
      "aws": "https://dbc-dp-",
      "azure": "https://adb-dp-",
    }
    suffix_url_settings = {
      "aws": "cloud.databricks.com",
      "azure": "azuredatabricks.net",
    }    
    org_id = self._context["tags"]["orgId"]
    org_shard = ""
    # org_shard doesnt need a suffix of "." for dnsname its handled in building the url
    if self._cloud.lower() == "azure":
      org_shard_id = int(org_id) % 20
      org_shard = f".{org_shard_id}"
    cluster_id = self._context["tags"]["clusterId"]
    url_base_path = f"/driver-proxy/o/{org_id}/{cluster_id}/{self._port}/"
    return ProxySettings(
      proxy_url=f"{prefix_url_settings[self._cloud.lower()]}{org_id}{org_shard}.{suffix_url_settings[self._cloud.lower()]}{url_base_path}",
      port=self._port,
      url_base_path=url_base_path    
    )

  @property
  def app_url_base_path(self):
    return self._ps.url_base_path
  
  @property
  def dash_app_url_base_path(self):
    return self._ps.url_base_path+"dash"

  def mount_dash_app(self, dash_app):
    self._fastapi_app.mount("/dash", WSGIMiddleware(dash_app.server))
    self.display_url(self.get_dash_url())

  def mount_gradio_app(self, gradio_app):
    self._fastapi_app.mount("/gradio", gradio_app)
    # self._fastapi_app = gr.mount_gradio_app(self._fastapi_app, gradio_app, path="/gradio") 
    self.display_url(self.get_gradio_url())
  
  def get_cloud(self):
    if self._context["extraContext"]["api_url"].endswith("azuredatabricks.net"):
      return "azure"
    return "aws"

  def mount_streamlit_app(self, script_path):
    self._streamlit_script = script_path
    # no op prtty much
    self.display_url(self.get_streamlit_url())
  
  def get_streamlit_url(self):
    return f'<a href="{self._ps.proxy_url}">Click to go to Streamlit App!</a>'

  def get_dash_url(self):
    return f'<a href="{self._ps.proxy_url}dash">Click to go to Dash App!</a>'
  
  def get_gradio_url(self):
    return f'<a href="{self._ps.proxy_url}gradio/">Click to go to Gradio App!</a>'

  def display_url(self, url):
    self._display_html(url)
      
  def run(self):
    if self._streamlit_script is not None:
      run_streamlit(self._streamlit_script, self._port)
    else:
      uvicorn.run(self._fastapi_app, host="0.0.0.0", port=self._port)