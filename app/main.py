import multiprocessing
import os
import time
from database import get_bot_configs
import subprocess

def run_bot_process(bot_config):
    """Function to run a single bot in its own process."""
    # We use a subprocess to ensure completely clean state and separate event loop
    # We call a specialized script for a single bot
    python_path = "/home/polaglot/polaglot/venv/bin/python"
    script_path = "/home/polaglot/polaglot/app/run_single.py"
    
    # Pass bot info as env vars or args
    env = os.environ.copy()
    env["BOT_ID"] = str(bot_config["id"])
    
    subprocess.run([python_path, script_path], env=env)

if __name__ == "__main__":
    configs = get_bot_configs()
    
    processes = []
    for config in configs:
        p = multiprocessing.Process(target=run_bot_process, args=(config,))
        p.start()
        processes.append(p)
        # Delay to avoid start-up collisions
        time.sleep(5)
        
    for p in processes:
        p.join()
