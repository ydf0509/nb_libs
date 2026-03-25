import sys
import threading
import time
from pathlib import Path


PROJECT_ROOT = r'D:\codes\nb_libs\nb_libs'
# if str(PROJECT_ROOT) not in sys.path:
#     sys.path.insert(0, str(PROJECT_ROOT))

from nb_libs.tools.nb_reload_restart import CommandAutoReloader  # noqa: E402


BASE_DIR = Path(__file__).resolve().parent
WATCH_DIR = BASE_DIR / "demo_src"
TARGET_SCRIPT = BASE_DIR / "demo_target.py"
MESSAGE_FILE = WATCH_DIR / "message.txt"


def simulate_changes() -> None:
    time.sleep(2)
    for idx in range(1, 4):
        content = f"change-{idx}, ts={time.time()}\n"
        MESSAGE_FILE.write_text(content, encoding="utf-8")
        print(f"[run_demo] wrote message file, round={idx}")
        time.sleep(3)


def main() -> None:
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    MESSAGE_FILE.write_text("initial-message\n", encoding="utf-8")
    threading.Thread(target=simulate_changes, daemon=True).start()

    reloader = CommandAutoReloader(
        command=[sys.executable, str(TARGET_SCRIPT)],
        watch_dirs=[str(BASE_DIR )],  # directory glob
        # watch_files=[str(BASE_DIR / "demo_src/**/*.txt")],  # file glob
        include_globs=["*.py", 
                    #    "**/*.py", 
                       ],
        # watch_files=[str(BASE_DIR /"**/*.py")],
        debounce_seconds=5,
        restart_delay=5,
        cwd=PROJECT_ROOT,
        recursive=True,
    )
    reloader.run(
        # max_runtime_seconds=14
    )


if __name__ == "__main__":
    main()
