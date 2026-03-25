import os
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
MESSAGE_FILE = BASE_DIR / "demo_src" / "message.txt"


def run() -> None:
    print(f"[demo_target] process started, pid={os.getpid()}")
    i =0
    while True:
        # try:
        #     message = MESSAGE_FILE.read_text(encoding="utf-8").strip()
        # except FileNotFoundError:
        #     message = "<message file not found>"
        # print(f"{time.strftime('%H:%M:%S')} [demo_target] pid={os.getpid()} message={message}")
        i +=1
        print(f"{time.strftime('%H:%M:%S')}  [demo_target] pid={os.getpid()} i={i}")
        time.sleep(1)


if __name__ == "__main__":
    run()
