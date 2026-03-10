import requests
import json
import re
import time
#from utils import prompt
import urllib3
import importlib.util
import openai
import httpx


access_token = None
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_prompt_module(path):
    module_name = "custom_prompt_module"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class LLM_helper:
    def __init__(self):
        self.proxies = {
            'http': 'http://proxy-dmz.intel.com:912',
            'https': 'http://proxy-dmz.intel.com:912',
        }
        self.client = None
        
    def set_up(self, expertgpt_token, model="gpt-4.1"):
        openai.api_key = expertgpt_token
        self.client = openai.OpenAI(
            api_key=expertgpt_token,
            http_client=httpx.Client(proxy=None, verify=False, trust_env=False),
            base_url="https://expertgpt.intel.com/v1"
        )
        self.model = model

    def analyze_log_sandbox(self, system_content, log=None):
        
        user_content = (
            f"""logs: {log}\n"""
        )
        print("client:", self.client)
        try:
            t0 = time.perf_counter()
            response = self.client.chat.completions.create(
                model=self.model,  
                messages=[
                    {
                        "role": "system",
                        "content": system_content
                    },
                    {
                        "role": "user", 
                        "content": user_content
                    }
                ],
                temperature=0.95,
                top_p=0.85,
                frequency_penalty=0,
                presence_penalty=0,
                max_tokens=8000,
                stop=None
            )
            elapsed = round(time.perf_counter() - t0, 1)
            raw_output = response.choices[0].message.content
            usage = response.usage
            token_stats = {
                "backend":        "expertgpt",
                "model":          self.model,
                "num_ctx":        "—",
                "prompt_tokens":  usage.prompt_tokens if usage else "—",
                "output_tokens":  usage.completion_tokens if usage else "—",
                "total_tokens":   usage.total_tokens if usage else "—",
                "ctx_used_pct":   "—",
                "elapsed_sec":    elapsed,
                "tokens_per_sec": "—",
            }
            json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                print("json output:",type(result), result)
                return result, token_stats
            else:
                print("raw output:", raw_output)
                return raw_output, token_stats
        except requests.exceptions.RequestException as e:
            print(f"Failed to make inference request: {e}")
            return {}, {}

    def analyze_log(self, prompt_path, log=None):
        

        prompt = load_prompt_module(prompt_path)
        
        system_content = (
           prompt.SYS_PROMPT
        )
        user_content = (
            f"""logs: {log}\n"""
        )
        print("client:", self.client)
        try:
            t0 = time.perf_counter()
            response = self.client.chat.completions.create(
                model=self.model,  
                messages=[
                    {
                        "role": "system",
                        "content": system_content
                    },
                    {
                        "role": "user", 
                        "content": user_content
                    }
                ],
                temperature=0.95,
                top_p=0.85,
                frequency_penalty=0,
                presence_penalty=0,
                max_tokens=1200,
                stop=None
            )
            elapsed = round(time.perf_counter() - t0, 1)
            raw_output = response.choices[0].message.content
            usage = response.usage
            token_stats = {
                "backend":        "expertgpt",
                "model":          self.model,
                "num_ctx":        "—",
                "prompt_tokens":  usage.prompt_tokens if usage else "—",
                "output_tokens":  usage.completion_tokens if usage else "—",
                "total_tokens":   usage.total_tokens if usage else "—",
                "ctx_used_pct":   "—",
                "elapsed_sec":    elapsed,
                "tokens_per_sec": "—",
            }
            json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                print("json output:",type(result), result)
                return result, token_stats
            else:
                print("raw output:", raw_output)
                return raw_output, token_stats
        except requests.exceptions.RequestException as e:
            print(f"Failed to make inference request: {e}")
            return {}, {}

#helper = LLM_helper()
#helper.set_up("key")
#print(helper.client)
