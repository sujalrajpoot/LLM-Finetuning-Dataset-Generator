import requests
from typing import Optional
from Config.config import BOLD_BRIGHT_RED, RESET, API_KEYS

class Nvidia:
    """
    A class to interact with the Nvidia API.
    """
    AVAILABLE_MODELS = [
        "meta/llama3-70b-instruct",
        "meta/llama3-8b-instruct",
        "nvidia/llama-3.1-nemotron-70b-instruct",
    ]
 
    def __init__(
        self,
        api_key: Optional[str] = None,
        max_tokens: int = 4096,
        timeout: int = 30,
        model: str = "meta/llama3-70b-instruct",
        temperature: float = 0.75,
        top_p: float = 0.9,
        system_prompt: str = "You are a helpful assistant.",
    ):
        
        if not api_key:
            api_key = API_KEYS.get("NVIDIA")

        if not api_key:
            raise ValueError("Please provide the Nvidia API Key in config or arguments.")
        
        self.api_key = api_key
        self.api_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.top_p = top_p
        self.model = model

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt.strip()}
            ],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stream": False
        }
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=self.timeout)
            response.raise_for_status() 
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise e