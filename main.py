import os
import json
import time
import random
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from Config.config import (
    BOLD_BRIGHT_CYAN,
    BOLD_BRIGHT_GREEN,
    BOLD_BRIGHT_MAGENTA,
    BOLD_BRIGHT_RED,
    BOLD_BRIGHT_YELLOW,
    RESET,
    DATASET_FILES_DIR
)
from Providers import Nvidia, Cerebras, DeepInfra, Sambanova

# --- Provider Mapping ---
PROVIDERS = {
    "nvidia": Nvidia,
    "cerebras": Cerebras,
    "deepinfra": DeepInfra,
    "sambanova": Sambanova
}

# --- File I/O ---
def load_data(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"{BOLD_BRIGHT_RED}❌ Error decoding JSON from {filepath}{RESET}")
        return []

def save_data(filepath, data):
    temp_path = filepath + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    os.replace(temp_path, filepath)  # atomic write

# --- Output Generation ---
def generate_output(item, model_provider):
    """
    Generates model output for a single item with retry logic.
    Runs safely inside threads.
    """
    instruction = item.get("instruction", "")
    input_text = item.get("input", "")
    prompt = f"Instruction: {instruction}\nInput: {input_text}" if input_text else instruction

    retries = 0
    max_retries = 10  # Prevent infinite loops on hard failures

    while retries < max_retries:
        try:
            output = model_provider.generate(prompt=prompt)

            if output and isinstance(output, str) and output.strip():
                return output.strip()
            else:
                print(f"{BOLD_BRIGHT_RED}⚠️ Empty output received. Retrying...{RESET}")
        except Exception as e:
            print(f"{BOLD_BRIGHT_RED}❌ Error while generating output: {e}{RESET}")

        retries += 1
        wait = random.uniform(2, 5)
        print(f"{BOLD_BRIGHT_RED}⏳ Retrying in {wait:.1f} seconds... (Attempt {retries}/{max_retries}){RESET}")
        time.sleep(wait)
    
    print(f"{BOLD_BRIGHT_RED}❌ Failed to generate output after {max_retries} attempts.{RESET}")
    return None

# --- Main Processing ---
def process_file(filepath, model_provider, batch_size=3):
    print(f"{BOLD_BRIGHT_MAGENTA}Processing dataset file: {filepath}{RESET}")
    data = load_data(filepath)
    if not data:
        print(f"{BOLD_BRIGHT_RED}Skipping empty or invalid file.{RESET}")
        return

    total = len(data)
    for i in range(0, total, batch_size):
        batch = data[i:i + batch_size]

        # Skip batch if all already have output
        if all("output" in item and item["output"] for item in batch):
            continue

        print(f"{BOLD_BRIGHT_YELLOW}\n🔹 Processing items {i+1} to {min(i+batch_size, total)} / {total}{RESET}")

        # --- Run batch concurrently ---
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # We pass model_provider to the worker function. 
            # Note: Provider instances should be thread-safe (requests.Session is thread-safe).
            futures = {executor.submit(generate_output, item, model_provider): idx for idx, item in enumerate(batch)}

            # Collect results in the same order
            results = [None] * len(batch)
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    result = future.result()
                    results[idx] = result
                    if result:
                        print(f"{BOLD_BRIGHT_GREEN}✅ Output generated for item {i+idx+1}{RESET}")
                    else:
                         print(f"{BOLD_BRIGHT_RED}❌ No output for item {i+idx+1}{RESET}")
                except Exception as e:
                    print(f"{BOLD_BRIGHT_RED}❌ Failed for item {i+idx+1}: {e}{RESET}")
                    results[idx] = None

        # --- Save results to data safely in order ---
        saved_count = 0
        for j, output in enumerate(results):
            if output:
                data[i + j]["output"] = output
                saved_count += 1
        
        if saved_count > 0:
            save_data(filepath, data)
            print(f"{BOLD_BRIGHT_CYAN}💾 Progress saved after batch {i//batch_size + 1}.{RESET}")

        # Small delay between batches
        time.sleep(2)

    print(f"{BOLD_BRIGHT_GREEN}🎉 All items in {filepath} processed successfully!\n{RESET}")

# --- Run ---
if __name__=="__main__":
    parser = argparse.ArgumentParser(description="LLM Finetuning Dataset Generator")
    parser.add_argument("--provider", type=str, default="nvidia", choices=PROVIDERS.keys(), help="The LLM provider to use.")
    parser.add_argument("--batch-size", type=int, default=3, help="Batch size for concurrent requests.")
    parser.add_argument("--dataset-dir", type=str, default=DATASET_FILES_DIR, help="Directory containing dataset JSON files.")
    
    args = parser.parse_args()
    
    provider_class = PROVIDERS[args.provider.lower()]
    
    try:
        # Instantiate provider. API keys are loaded internally from Config/env
        model_provider = provider_class() 
        print(f"{BOLD_BRIGHT_GREEN}Initialized {args.provider} provider.{RESET}")
    except Exception as e:
        print(f"{BOLD_BRIGHT_RED}Failed to initialize provider {args.provider}: {e}{RESET}")
        print(f"{BOLD_BRIGHT_YELLOW}Please ensure you have set the API Key in environment variables or Config/config.py{RESET}")
        exit(1)

    if not os.path.exists(args.dataset_dir):
         print(f"{BOLD_BRIGHT_RED}Dataset directory {args.dataset_dir} does not exist.{RESET}")
         exit(1)

    for filepath in os.listdir(args.dataset_dir):
        if filepath.endswith(".json"):
            full_filepath = os.path.join(args.dataset_dir, filepath)
            process_file(full_filepath, model_provider, batch_size=args.batch_size)
