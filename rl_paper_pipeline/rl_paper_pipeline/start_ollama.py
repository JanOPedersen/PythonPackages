import subprocess
import os
import time
import requests

def start_ollama():
    print("Starting Ollama server...")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    ) 

def wait_for_ollama(timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            requests.get("http://localhost:11434/api/tags", timeout=1)
            print("Ollama is ready.")
            return True
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Ollama did not start in time")

import subprocess
import time
import requests

def ensure_ollama_running(timeout=30):
    # 1. Check if server is already up
    try:
        requests.get("http://localhost:11434/api/tags", timeout=1)
        print("Ollama already running.")
        return
    except Exception:
        pass

    # 2. Start Ollama
    print("Starting Ollama...")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    )

    # 3. Wait for readiness
    start = time.time()
    while time.time() - start < timeout:
        try:
            requests.get("http://localhost:11434/api/tags", timeout=1)
            print("Ollama is ready.")
            return
        except Exception:
            time.sleep(0.5)

    raise RuntimeError("Ollama did not start in time")
