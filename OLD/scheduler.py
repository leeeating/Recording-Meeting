import time
import subprocess

while True:
    try:
        subprocess.run(["pyw", "daemon.py"])
    except Exception as e:
        print(e)
    time.sleep(60)