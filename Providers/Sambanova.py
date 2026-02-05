import requests 
from typing import Union, Any, Generator, Optional
from Config.config import BOLD_BRIGHT_RED, RESET, API_KEYS

class Sambanova:
    """
    A class to interact with the Sambanova API.
    """
    AVAILABLE_MODELS = [
        "Meta-Llama-3.1-8B-Instruct",
        "Meta-Llama-3.1-70B-Instruct",
        "Meta-Llama-3.1-405B-Instruct",
        # ...
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_tokens: int = 4096,
        timeout: int = 30,
        model: str = "Meta-Llama-3.3-70B-Instruct",
        temperature: float = 0.75,
        top_p: float = 0.9,
        system_prompt: str = "You are a helpful AI assistant.",
    ):
        
        if not api_key:
            api_key = API_KEYS.get("SAMBANOVA")
            
        if not api_key:
            raise ValueError("Please provide the Sambanova API Key in config or arguments.")

        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.top_p = top_p

        self.base_url = "https://api.sambanova.ai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stream": False
        }
        try:
            response = requests.post(
                self.base_url, 
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            raise e