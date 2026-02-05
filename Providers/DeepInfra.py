from Config.config import generate_dynamic_headers, BOLD_BRIGHT_RED, BOLD_BRIGHT_GREEN, BOLD_BRIGHT_CYAN, RESET, API_KEYS
import requests
from typing import Optional

class DeepInfra:
    """Client for interacting with the DeepInfra Chat Completions API."""
    AVAILABLE_MODELS = [
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "deepseek-ai/DeepSeek-R1",
        "deepseek-ai/DeepSeek-V3",
        # Add more if needed
    ]
 
    def __init__(
        self,
        api_key: Optional[str] = None,
        max_tokens: int = 2048,
        timeout: int = 30,
        model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        temperature: float = 0.75,
        top_p: float = 0.9,
        system_prompt: str = "You are a helpful assistant.",
    ) -> None:
        
        if not api_key:
            api_key = API_KEYS.get("DEEPINFRA")

        if api_key:
            print(f"{BOLD_BRIGHT_GREEN}Initialized the DeepInfra API Client using API Key.{RESET}")
            self.headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
        else:
            print(f"{BOLD_BRIGHT_GREEN}Initialized the DeepInfra API Client without API Key (Dynamic Headers).{RESET}")
            self.headers = generate_dynamic_headers()

        self.api_url = "https://api.deepinfra.com/v1/openai/chat/completions"
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.top_p = top_p
        self.model = model
        self.session = requests.Session()

    def generate(self, prompt: str) -> str:
        if not prompt or not prompt.strip():
            return ""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt.strip()},
            ],
            "stream": False,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }

        try:
            response = self.session.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                return ""
            message = choices[0].get("message") or {}
            return message.get("content", "") or ""
        except Exception as err:
            raise err