import json
import re
import importlib.util
import time
import ollama


def load_prompt_module(path):
    module_name = "custom_prompt_module"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OllamaLLM_helper:
    """Local LLM helper using Ollama (RTX 5080 GPU accelerated)."""

    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host
        self.model = "llama3.1:8b"
        self.num_ctx = 32768          # 32K default – safe for RTX 5080 16GB (~9GB total VRAM)
        # trust_env=False + proxy=None: bypass corporate proxy for local Ollama
        self.client = ollama.Client(host=host, trust_env=False, proxy=None)

    def set_up(self, model: str = "llama3.1:8b", num_ctx: int = 32768):
        self.model = model
        self.num_ctx = num_ctx
        self.client = ollama.Client(host=self.host, trust_env=False, proxy=None)
        print(f"[OllamaLLM] Using model: {self.model} | num_ctx: {self.num_ctx} | host: {self.host}")

    def _chat(self, system_content: str, user_content: str) -> tuple[str, dict]:
        """Returns (text_content, token_stats_dict)."""
        t0 = time.perf_counter()
        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user",   "content": user_content},
            ],
            options={
                "temperature": 0.7,
                "top_p": 0.9,
                "num_ctx": self.num_ctx,   # input context window
                "num_predict": 8000     # max output tokens
            },
        )
        elapsed = round(time.perf_counter() - t0, 1)
        prompt_tok  = response.get("prompt_eval_count") or 0
        output_tok  = response.get("eval_count") or 0
        tokens_per_sec = round(output_tok / elapsed, 1) if elapsed > 0 and output_tok else "—"
        token_stats = {
            "backend":         "ollama",
            "model":           self.model,
            "num_ctx":         self.num_ctx,
            "prompt_tokens":   prompt_tok  or "—",
            "output_tokens":   output_tok  or "—",
            "total_tokens":    (prompt_tok + output_tok) or "—",
            "ctx_used_pct": (
                round((prompt_tok + output_tok) / self.num_ctx * 100, 1)
                if self.num_ctx else "—"
            ),
            "elapsed_sec":     elapsed,
            "tokens_per_sec":  tokens_per_sec,
        }
        return response["message"]["content"], token_stats

    def analyze_log_sandbox(self, system_content: str, log=None):
        user_content = f"logs: {log}\n"
        print(f"[OllamaLLM] analyze_log_sandbox | model={self.model}")
        try:
            raw_output, token_stats = self._chat(system_content, user_content)
            print(f"[OllamaLLM] tokens — prompt:{token_stats['prompt_tokens']} "
                  f"output:{token_stats['output_tokens']} "
                  f"ctx_used:{token_stats['ctx_used_pct']}%")
            json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                print("[OllamaLLM] json output:", type(result), result)
                return result, token_stats
            else:
                print("[OllamaLLM] raw output:", raw_output)
                return raw_output, token_stats
        except Exception as e:
            print(f"[OllamaLLM] Error: {e}")
            return {}, {}

    def analyze_log(self, prompt_path: str, log=None):
        prompt = load_prompt_module(prompt_path)
        system_content = prompt.SYS_PROMPT
        user_content = f"logs: {log}\n"
        print(f"[OllamaLLM] analyze_log | model={self.model}")
        try:
            raw_output, token_stats = self._chat(system_content, user_content)
            json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                print("[OllamaLLM] json output:", type(result), result)
                return result, token_stats
            else:
                print("[OllamaLLM] raw output:", raw_output)
                return raw_output, token_stats
        except Exception as e:
            print(f"[OllamaLLM] Error: {e}")
            return {}, {}


def get_available_ollama_models(host: str = "http://localhost:11434") -> list[str]:
    """Return list of model names currently pulled in Ollama."""
    try:
        # trust_env=False + proxy=None: bypass corporate proxy for local Ollama
        client = ollama.Client(host=host, trust_env=False, proxy=None)
        result = client.list()
        return [m["model"] for m in result.get("models", [])]
    except Exception as e:
        print(f"[OllamaLLM] Could not fetch model list: {e}")
        return []
