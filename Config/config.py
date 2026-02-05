# config.py

from typing import (
    Optional,
    Dict
)
from dotenv import load_dotenv; load_dotenv()
import random
import ipaddress
import os

# --- API Configuration ---
# You can set these in your environment variables or a .env file 

DATASET_FILES_DIR = "./dataset_files" # important

API_KEYS: Dict[str, Optional[str]] = {
    "NVIDIA": os.environ.get("NVIDIA_API_KEY"),
    "CEREBRAS": os.environ.get("CEREBRAS_API_KEY"),
    "DEEPINFRA": os.environ.get("DEEPINFRA_API_KEY"),
    "SAMBANOVA": os.environ.get("SAMBANOVA_API_KEY"),
}

"""
Contains all the configs for the data generator
"""

# setting up theme
BOLD_BRIGHT_RED     = "\033[1;91m"
BOLD_BRIGHT_GREEN   = "\033[1;92m"
BOLD_BRIGHT_YELLOW  = "\033[1;93m"
BOLD_BRIGHT_MAGENTA = "\033[1;95m"
BOLD_BRIGHT_CYAN    = "\033[1;96m"

RESET = "\033[0m"

FINGERPRINTS = {  
    "accept": [  
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",  
        "application/json, text/plain, */*",  
        "*/*"  
    ],  
    "accept_language": {  
        "US": ["en-US,en;q=0.9"],  
        "GB": ["en-GB,en;q=0.8"],  
        "FR": ["fr-FR,fr;q=0.8,en;q=0.3"],  
        "DE": ["de-DE,de;q=0.8,en;q=0.3"],  
        "ES": ["es-ES,es;q=0.8,en;q=0.3"],  
        "DEFAULT": ["en-US,en;q=0.9"]  
    },  
    "user_agents": {  
        "desktop": [  
            # Chrome / Windows  
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",  
            # Safari / macOS  
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",  
            # Firefox / Linux  
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:119.0) Gecko/20100101 Firefox/119.0",  
            # Edge / Windows  
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"  
        ],  
        "mobile": [  
            # Android Chrome  
            "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",  
            # iPhone Safari  
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"  
        ]  
    },  
    "platforms": {  
        "desktop": ['"Windows"', '"macOS"', '"Linux"'],  
        "mobile": ['"Android"', '"iOS"']  
    }  
}  
  
REFERERS = [  
    "https://www.google.com/",  
    "https://www.bing.com/",  
    "https://twitter.com/",  
    "https://facebook.com/",  
    "https://duckduckgo.com/"  
]  
  
ORIGINS = [  
    "deepinfra.com",  
    "huggingface.co",  
    "openai.com",  
    "google.com",  
    "openrouter.com",
    "localhost:5500",
    "localhost:8173",
    "localhost:5000",
    "localhost:3000"
]  
  
# --- Helpers ---  
def _random_public_ip() -> str:  
    """  
    Generate a random public IPv4 address excluding private/reserved ranges.  
    """  
    # We'll loop until we find a public address outside common reserved blocks.  
    while True:  
        octets = [random.randint(1, 255) for _ in range(4)]  
        ip_str = ".".join(map(str, octets))  
        ip = ipaddress.ip_address(ip_str)  
        if not (ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_multicast or ip.is_link_local):  
            return ip_str  
  
def _choose_region(region: Optional[str]) -> str:  
    if region and region.upper() in FINGERPRINTS["accept_language"]:  
        return region.upper()  
    # pick a weighted region if not provided  
    choices = ["US"] * 6 + ["GB"] * 2 + ["FR"] + ["DE"] + ["ES"]  
    return random.choice(choices)  
  
def _mobile_or_desktop(desktop_ratio: float) -> str:  
    """  
    Return 'desktop' or 'mobile' according to desktop_ratio.  
    desktop_ratio=0.8 means 80% desktop, 20% mobile.  
    """  
    if random.random() < desktop_ratio:  
        return "desktop"  
    return "mobile"  
  
def _sec_ch_ua_from_ua() -> str:  
    # Lightweight heuristic: produce a plausible Sec-CH-UA token (not exhaustive).  
    chromium_version = random.randint(100, 125)  
    return f'"Not A;Brand";v="99", "Chromium";v="{chromium_version}", "Google Chrome";v="{chromium_version}"'  
  
# --- Main function ---  
def generate_dynamic_headers(desktop_ratio: float = 0.8, region: Optional[str] = None, include_optional_client_hints: bool = True) -> dict:  
    """  
    Generate a realistic set of HTTP headers for browser-like requests.  
    - desktop_ratio: fraction of requests that should appear as desktop (0.0..1.0).  
    - region: optional ISO region code (US, GB, FR, DE, ES). If None, region is chosen randomly.  
    - include_optional_client_hints: toggles Sec-CH-* headers.  
    Returns a dictionary of headers.  
      
    IMPORTANT: Use only on systems you own or have explicit permission to test.  
    """  
    region_code = _choose_region(region)  
    device_type = _mobile_or_desktop(desktop_ratio)  
  
    ua = random.choice(FINGERPRINTS["user_agents"][device_type])  
    platform = random.choice(FINGERPRINTS["platforms"][device_type])  
    accept_lang = random.choice(FINGERPRINTS["accept_language"].get(region_code, FINGERPRINTS["accept_language"]["DEFAULT"]))  
  
    headers = {  
        "Accept": random.choice(FINGERPRINTS["accept"]),  
        "Accept-Language": accept_lang,  
        "Content-Type": "application/json",  
        "Cache-Control": "no-cache",  
        "Origin": "https://" + random.choice(ORIGINS),  
        "Pragma": "no-cache",  
        "Referer": random.choice(REFERERS),  
        "Sec-Fetch-Dest": "empty",  
        "Sec-Fetch-Mode": "cors",  
        "Sec-Fetch-Site": "same-site",  
        "User-Agent": ua,  
        # Dynamic identity headers (use carefully; only for testing in permitted environments)  
        "X-Forwarded-For": _random_public_ip(),  
        "Client-IP": _random_public_ip(),  
        "X-Real-IP": _random_public_ip(),  
        # Browser client hints (optional)  
        "Sec-CH-UA-Platform": platform,  
        "Device-Memory": str(random.choice(["4", "8", "16"])),  
        "Viewport-Width": str(random.choice(["360", "720", "1080", "1440"])),  
        "DNT": str(random.choice(["0", "1"])),  
        "Upgrade-Insecure-Requests": str(random.choice(["0", "1"]))  
    }  
  
    if include_optional_client_hints:  
        headers["Sec-CH-UA"] = _sec_ch_ua_from_ua()  
        headers["Sec-CH-UA-Mobile"] = "?1" if device_type == "mobile" else "?0"  
   
    return headers
