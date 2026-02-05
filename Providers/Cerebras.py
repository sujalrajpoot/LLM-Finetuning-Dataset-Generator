import os
import json
import requests
from typing import Optional
from Config.config import generate_dynamic_headers, BOLD_BRIGHT_RED, BOLD_BRIGHT_GREEN, BOLD_BRIGHT_YELLOW, BOLD_BRIGHT_CYAN, RESET, API_KEYS

class Cerebras:
    """
    Client to interact with the Cerebras AI API for chat completions.
    """
    AVAILABLE_MODELS = [
        "llama3.1-8b",
        "llama-3.3-70b",
        "qwen-3-32b",
        "qwen-3-235b-a22b-instruct-2507",
        "qwen-3-235b-a22b-thinking-2507",
        "gpt-oss-120b",
        "zai-glm-4.6"
    ]

    def __init__(
        self, 
        cookies_or_api_key: Optional[str] = None,
        max_tokens: int = 2048,
        timeout: int = 30,
        model: str = "llama-3.3-70b",
        temperature: float = 0.75,
        top_p: float = 0.9,
        system_prompt: str = "You are a helpful assistant.",
    ) -> None:
        
        # Try to get API key from config if not passed
        if not cookies_or_api_key:
            cookies_or_api_key = API_KEYS.get("CEREBRAS")
        
        self.cookies_or_api_key = cookies_or_api_key
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.top_p = top_p
        self.model = model
        self.config_dir = os.path.abspath("Config")
        self.config_file_path = os.path.join(self.config_dir, "Cerebras-Config.json")

        self.api_key = None

        # --- Main initialization logic ---
        if self.cookies_or_api_key and self.cookies_or_api_key.startswith('cookieyes-consent'):
            # Priority: Cookies (Demo Mode)
            print(f"{BOLD_BRIGHT_CYAN}Initializing Cerebras client using COOKIES...{RESET}")
            self._init_demo_mode()
        elif self.cookies_or_api_key and (self.cookies_or_api_key.startswith('csk-') or len(self.cookies_or_api_key) > 20):
             # Initialize with API key
            print(f"{BOLD_BRIGHT_CYAN}Initializing Cerebras client using API KEY...{RESET}")
            self.api_key = self.cookies_or_api_key
        else:
             print(f"{BOLD_BRIGHT_YELLOW}No valid Cerebras API Key or Cookie provided. Expecting one in env or arguments.{RESET}")

    def _init_demo_mode(self):
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                
            if not os.path.exists(self.config_file_path):
                # Create config file if missing
                with open(self.config_file_path, 'w') as config_file:
                    json.dump({}, config_file)
                self.refresh_api_key()
            else:
                # Load API key from existing config
                with open(self.config_file_path, 'r') as f:
                    data = json.load(f)
                    self.api_key = data.get("data", {}).get("GetMyDemoApiKey")

                # If key not found in config, refresh it
                if not self.api_key:
                    print(f"{BOLD_BRIGHT_YELLOW}API key not found in config. Refreshing...{RESET}")
                    self.refresh_api_key()

        except Exception as e:
            print(f"{BOLD_BRIGHT_RED}Error encountered while initializing with cookies: {e}{RESET}")
            self.refresh_api_key()

    def refresh_api_key(self) -> None:
        """
        Refreshes the API key by making a request to the Cerebras API endpoint.
        """
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'cookie': self.cookies_or_api_key,
            'dnt': '1',
            'origin': 'https://inference.cerebras.ai',
            'priority': 'u=1, i',
            'referer': 'https://inference.cerebras.ai/',
            'user-agent': generate_dynamic_headers()['User-Agent']
        }
        json_data = {
            'operationName': 'GetMyDemoApiKey',
            'variables': {},
            'query': 'query GetMyDemoApiKey {\n  GetMyDemoApiKey\n}',
        }
        try:
            response = requests.post('https://chat.cerebras.ai/api/graphql', headers=headers, json=json_data)
            response.raise_for_status()
            if response.status_code == 200 and response.ok:
                resp_json = response.json()
                self.api_key = resp_json.get("data", {}).get("GetMyDemoApiKey")
                with open(self.config_file_path, 'w') as json_file:
                    json.dump(resp_json, json_file, indent=4)
                print(f"{BOLD_BRIGHT_YELLOW}API key updated successfully!{RESET}")
            else:
                print(f"{BOLD_BRIGHT_RED}Failed to update API key: {response.status_code}{RESET}")
        except Exception as e:
            print(f"{BOLD_BRIGHT_RED}Refresh API Key failed: {e}{RESET}")
    
    def generate(self, prompt: str) -> str:
        if not self.api_key:
             raise ValueError("API Key is missing. Please provide a valid key or cookie.")
             
        headers = {
            'accept': 'application/json',
            'authorization': f'Bearer {self.api_key}'
        }
        json_data = {
            'messages': [
                {'content': self.system_prompt, 'role': 'system'},
                {'content': prompt, 'role': 'user'},
            ],
            'model': self.model,
            'stream': False,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'max_completion_tokens': self.max_tokens,
        }
        
        try:
            response = requests.post('https://api.cerebras.ai/v1/chat/completions', headers=headers, json=json_data, timeout=self.timeout)
            
            if response.status_code == 401 and self.cookies_or_api_key and self.cookies_or_api_key.startswith('cookieyes'):
                print("🚨 Demo API key expired. Refreshing...")
                self.refresh_api_key()
                # Retry once by recursion? Better to not recurse infinitely. use simple check
                if self.api_key: # check if refresh worked
                     # Re-create headers
                    headers['authorization'] = f'Bearer {self.api_key}'
                    response = requests.post('https://api.cerebras.ai/v1/chat/completions', headers=headers, json=json_data, timeout=self.timeout)
                    response.raise_for_status()
                    return response.json()['choices'][0]['message']['content']

            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            # Raise exception so main loop handles retry
            raise e