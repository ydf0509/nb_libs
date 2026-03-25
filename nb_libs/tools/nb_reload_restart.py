# -*- coding: utf-8 -*-
"""
Generic auto-reloader for restarting any command on file changes.

Features:
1) restart any command line (not limited to Flask)
2) watch directories and files
3) support glob patterns in watch targets and include/ignore filters
4) debounce and delayed restart
"""

import argparse
import os
import subprocess
import time
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Union

try:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError as exc:
    raise ImportError("Please install watchdog first: pip install watchdog") from exc

PathLike = Union[str, os.PathLike]
CommandType = Union[str, Sequence[str]]


def _normalize_glob(glob_text: str) -> str:
    return str(glob_text).replace("\\", "/").strip()


def _strip_current_dir_prefix(path_text: str) -> str:
    if path_text.startswith("./"):
        return path_text[2:]
    return path_text


def _has_glob(glob_text: str) -> bool:
    return any(char in glob_text for char in ("*", "?", "["))


def _to_abs_path(path_value: PathLike, cwd: Path) -> Path:
    path_obj = Path(path_value).expanduser()
    if not path_obj.is_absolute():
        path_obj = cwd / path_obj
    return Path(os.path.abspath(str(path_obj)))


def _to_abs_glob(glob_text: str, cwd: Path) -> str:
    normalized = _normalize_glob(glob_text)
    if Path(normalized).is_absolute():
        return normalized
    cleaned = _strip_current_dir_prefix(normalized)
    return (cwd.as_posix().rstrip("/") + "/" + cleaned).replace("//", "/")


def _glob_root(glob_text: str, cwd: Path) -> Path:
    """
    Resolve a safe observer root from a glob expression.
    Example:
      - src/**/*.py -> <cwd>/src
      - **/*.txt    -> <cwd>
    """
    normalized = _normalize_glob(glob_text)
    if Path(normalized).is_absolute():
        if len(normalized) >= 2 and normalized[1] == ":":
            current = Path(normalized[:2] + "/")
            remaining = normalized[2:].lstrip("/")
        else:
            current = Path("/")
            remaining = normalized.lstrip("/")
    else:
        current = cwd
        remaining = _strip_current_dir_prefix(normalized)

    for part in [item for item in remaining.split("/") if item not in ("", ".")]:
        if part == "**" or _has_glob(part):
            break
        current = current / part
    return _to_abs_path(current, cwd)


def _nearest_existing_dir(path_obj: Path) -> Optional[Path]:
    candidate = Path(os.path.abspath(str(path_obj)))
    while True:
        if candidate.exists() and candidate.is_dir():
            return candidate
        if candidate.parent == candidate:
            return None
        candidate = candidate.parent


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


@dataclass
class _WatchRule:
    mode: str  # exact_dir | exact_file | glob
    absolute_path: Optional[Path] = None
    absolute_pattern: str = ""
    relative_pattern: str = ""


class _ReloadEventHandler(FileSystemEventHandler):
    def __init__(self, reloader: "CommandAutoReloader"):
        self.reloader = reloader
        super().__init__()

    def on_any_event(self, event: FileSystemEvent) -> None:
        self.reloader.handle_fs_event(event)


class CommandAutoReloader:
    """
    Restart any command when watched files are changed.

    Args:
        command: command string (shell=True) or argv list (shell=False).
        watch_dirs: watched directories. Supports glob expressions.
        watch_files: watched files. Supports exact path and glob.
        include_globs: file include filters. Default: ['*'].
        ignore_globs: file ignore filters.
        cwd: working directory for subprocess.
        shell: force shell mode. None means:
               - command is str  -> True
               - command is list -> False
        recursive: recursive watching for observer roots.
        debounce_seconds: minimum interval between two restart triggers.
        restart_delay: delay before restart after change is detected.
        restart_on_process_exit: whether to auto-restart when command exits.
        poll_interval: main loop polling interval.
        stop_timeout: graceful terminate timeout before kill.
        case_sensitive: whether glob matching is case sensitive.
        log_prefix: simple prefix for stdout logs.
    """

    def __init__(
        self,
        command: CommandType,
        watch_dirs: Optional[Sequence[PathLike]] = None,
        watch_files: Optional[Sequence[PathLike]] = None,
        include_globs: Optional[Sequence[str]] = None,
        ignore_globs: Optional[Sequence[str]] = None,
        cwd: Optional[PathLike] = None,
        shell: Optional[bool] = None,
        recursive: bool = True,
        debounce_seconds: float = 0.3,
        restart_delay: float = 0.0,
        restart_on_process_exit: bool = False,
        poll_interval: float = 0.2,
        stop_timeout: float = 5.0,
        case_sensitive: bool = False,
        log_prefix: str = "CommandAutoReloader",
    ):
        self.command = command
        self.cwd = _to_abs_path(cwd or os.getcwd(), Path(os.getcwd()))
        self.shell = shell
        self.watch_dirs = list(watch_dirs or [])
        self.watch_files = list(watch_files or [])
        self.recursive = recursive
        self.debounce_seconds = max(0.0, debounce_seconds)
        self.restart_delay = max(0.0, restart_delay)
        self.restart_on_process_exit = restart_on_process_exit
        self.poll_interval = max(0.05, poll_interval)
        self.stop_timeout = max(0.1, stop_timeout)
        self.case_sensitive = case_sensitive
        self.log_prefix = log_prefix

        default_ignores = [
            "*/__pycache__/*",
            "*.pyc",
            "*.pyo",
            "*.swp",
            "*.tmp",
        ]
        self.include_globs = [self._normalize_case(_normalize_glob(p)) for p in (include_globs or ["*"])]
        self.ignore_globs = [self._normalize_case(_normalize_glob(p)) for p in (ignore_globs or default_ignores)]

        self.process: Optional[subprocess.Popen] = None
        self.observer: Optional[Observer] = None
        self._pending_restart_at: Optional[float] = None
        self._last_trigger_at = 0.0
        self._stop_requested = False
        self._process_exit_logged = False
        self._watch_rules: List[_WatchRule] = []
        self._watch_roots: List[Path] = []

        self._prepare_watch_rules()

    def _normalize_case(self, text: str) -> str:
        return text if self.case_sensitive else text.lower()

    def _print(self, message: str) -> None:
        print(f"[{self.log_prefix}] {message}")

    def _add_watch_root(self, path_obj: Optional[Path]) -> None:
        if path_obj is None:
            return
        abs_dir = _to_abs_path(path_obj, self.cwd)
        if abs_dir not in self._watch_roots:
            self._watch_roots.append(abs_dir)

    def _prepare_watch_rules(self) -> None:
        self._append_rules(self.watch_dirs, treat_as_dir=True)
        self._append_rules(self.watch_files, treat_as_dir=False)
        if not self._watch_roots:
            self._watch_roots = [self.cwd]

    def _append_rules(self, targets: Iterable[PathLike], treat_as_dir: bool) -> None:
        for target in targets:
            raw = str(target).strip()
            if not raw:
                continue
            normalized = _normalize_glob(raw)
            if _has_glob(normalized):
                pattern = normalized
                if treat_as_dir:
                    pattern = normalized.rstrip("/") + "/**"
                self._watch_rules.append(
                    _WatchRule(
                        mode="glob",
                        absolute_pattern=self._normalize_case(_to_abs_glob(pattern, self.cwd)),
                        relative_pattern=self._normalize_case(pattern),
                    )
                )
                self._add_watch_root(_nearest_existing_dir(_glob_root(normalized, self.cwd)))
                continue

            abs_target = _to_abs_path(normalized, self.cwd)
            if treat_as_dir:
                if abs_target.exists() and abs_target.is_file():
                    self._watch_rules.append(_WatchRule(mode="exact_file", absolute_path=abs_target))
                    self._add_watch_root(_nearest_existing_dir(abs_target.parent))
                else:
                    self._watch_rules.append(_WatchRule(mode="exact_dir", absolute_path=abs_target))
                    self._add_watch_root(_nearest_existing_dir(abs_target))
            else:
                if abs_target.exists() and abs_target.is_dir():
                    self._watch_rules.append(_WatchRule(mode="exact_dir", absolute_path=abs_target))
                    self._add_watch_root(_nearest_existing_dir(abs_target))
                else:
                    self._watch_rules.append(_WatchRule(mode="exact_file", absolute_path=abs_target))
                    self._add_watch_root(_nearest_existing_dir(abs_target.parent))

    def _relative_posix(self, file_path: Path) -> str:
        try:
            return file_path.relative_to(self.cwd).as_posix()
        except ValueError:
            return file_path.as_posix()

    def _match_glob_list(self, file_path: Path, relative_posix: str, globs: Sequence[str]) -> bool:
        abs_posix = self._normalize_case(file_path.as_posix())
        rel_posix = self._normalize_case(relative_posix)
        name = self._normalize_case(file_path.name)
        for glob_text in globs:
            if fnmatch(abs_posix, glob_text) or fnmatch(rel_posix, glob_text) or fnmatch(name, glob_text):
                return True
        return False

    def _match_watch_rules(self, file_path: Path, relative_posix: str) -> bool:
        if not self._watch_rules:
            return True
        abs_case = self._normalize_case(file_path.as_posix())
        rel_case = self._normalize_case(relative_posix)

        for rule in self._watch_rules:
            if rule.mode == "exact_file":
                if rule.absolute_path == file_path:
                    return True
                continue
            if rule.mode == "exact_dir":
                if rule.absolute_path and _is_relative_to(file_path, rule.absolute_path):
                    return True
                continue
            if fnmatch(abs_case, rule.absolute_pattern) or fnmatch(rel_case, rule.relative_pattern):
                return True
        return False

    def _should_trigger(self, file_path: Path) -> bool:
        relative_posix = self._relative_posix(file_path)
        if not self._match_watch_rules(file_path, relative_posix):
            return False
        if self.ignore_globs and self._match_glob_list(file_path, relative_posix, self.ignore_globs):
            return False
        if self.include_globs and not self._match_glob_list(file_path, relative_posix, self.include_globs):
            return False
        return True

    def _iter_event_paths(self, event: FileSystemEvent) -> List[Path]:
        candidates = [getattr(event, "src_path", None), getattr(event, "dest_path", None)]
        paths = []
        for candidate in candidates:
            if not candidate:
                continue
            paths.append(_to_abs_path(candidate, self.cwd))
        return paths

    def handle_fs_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        matched_path = None
        for path_obj in self._iter_event_paths(event):
            if self._should_trigger(path_obj):
                matched_path = path_obj
                break
        if matched_path is None:
            return

        now = time.monotonic()
        if self.debounce_seconds > 0 and now - self._last_trigger_at < self.debounce_seconds:
            return

        self._last_trigger_at = now
        self._pending_restart_at = now + self.restart_delay
        self._print(f"detected change ({event.event_type}): {matched_path.as_posix()}")

    def _resolve_shell_flag(self) -> bool:
        if self.shell is not None:
            return self.shell
        return isinstance(self.command, str)

    def start_process(self) -> None:
        self.stop_process()
        shell_flag = self._resolve_shell_flag()
        command_to_run: Union[str, List[str]]
        if isinstance(self.command, str):
            command_to_run = self.command
        else:
            command_to_run = [str(item) for item in self.command]
        self._print(f"starting command: {command_to_run}")
        self.process = subprocess.Popen(
            command_to_run,
            shell=shell_flag,
            cwd=str(self.cwd),
        )
        self._process_exit_logged = False

    def stop_process(self) -> None:
        if not self.process:
            return
        if self.process.poll() is None:
            self._print(f"stopping process pid={self.process.pid}")
            self.process.terminate()
            try:
                self.process.wait(timeout=self.stop_timeout)
            except subprocess.TimeoutExpired:
                self._print(f"force killing process pid={self.process.pid}")
                self.process.kill()
                self.process.wait()
        self.process = None

    def restart_process(self) -> None:
        self._print("restarting command...")
        self.start_process()

    def _start_observer(self) -> None:
        if self.observer:
            return
        handler = _ReloadEventHandler(self)
        observer = Observer()
        active_roots = []
        for root in self._watch_roots:
            if root.exists() and root.is_dir():
                observer.schedule(handler, str(root), recursive=self.recursive)
                active_roots.append(root)
                self._print(f"watching root: {root.as_posix()}")
            else:
                self._print(f"skip invalid watch root: {root.as_posix()}")
        if not active_roots:
            observer.schedule(handler, str(self.cwd), recursive=self.recursive)
            active_roots.append(self.cwd)
            self._print(f"fallback watch root: {self.cwd.as_posix()}")
        self.observer = observer
        self.observer.start()

    def request_stop(self) -> None:
        self._stop_requested = True

    def close(self) -> None:
        self.stop_process()
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        self._print("stopped.")

    def run(self, max_runtime_seconds: Optional[float] = None) -> None:
        self._stop_requested = False
        self._start_observer()
        self.start_process()
        start_at = time.monotonic()
        self._print("running... press Ctrl+C to exit.")

        try:
            while not self._stop_requested:
                now = time.monotonic()

                if self._pending_restart_at is not None and now >= self._pending_restart_at:
                    self._pending_restart_at = None
                    self.restart_process()

                if self.process and self.process.poll() is not None:
                    exit_code = self.process.returncode
                    if self.restart_on_process_exit:
                        self._print(f"process exited with code {exit_code}, auto restart enabled.")
                        self.process = None
                        self.start_process()
                    elif not self._process_exit_logged:
                        self._print(f"process exited with code {exit_code}, waiting for file changes.")
                        self._process_exit_logged = True

                if max_runtime_seconds is not None and now - start_at >= max_runtime_seconds:
                    self._print(f"max runtime reached: {max_runtime_seconds}s")
                    break

                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            self._print("received Ctrl+C")
        finally:
            self.close()


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Restart any command when files are changed.")
    parser.add_argument("--cmd", required=True, help='command string, e.g. "python app.py"')
    parser.add_argument("--cwd", default=os.getcwd(), help="working directory for command")
    parser.add_argument("--watch-dir", action="append", default=[], help="watch directory (supports glob)")
    parser.add_argument("--watch-file", action="append", default=[], help="watch file (supports glob)")
    parser.add_argument("--include", action="append", default=None, help="include glob pattern")
    parser.add_argument("--ignore", action="append", default=None, help="ignore glob pattern")
    parser.add_argument("--debounce", type=float, default=0.3, help="debounce seconds")
    parser.add_argument("--delay", type=float, default=0.0, help="restart delay seconds")
    parser.add_argument("--non-recursive", action="store_true", help="disable recursive watch")
    parser.add_argument("--restart-on-exit", action="store_true", help="restart when command exits")
    parser.add_argument("--case-sensitive", action="store_true", help="glob match case sensitive")
    return parser


if __name__ == "__main__":
    args = _build_cli_parser().parse_args()
    reloader = CommandAutoReloader(
        command=args.cmd,
        watch_dirs=args.watch_dir,
        watch_files=args.watch_file,
        include_globs=args.include,
        ignore_globs=args.ignore,
        cwd=args.cwd,
        shell=True,
        recursive=not args.non_recursive,
        debounce_seconds=args.debounce,
        restart_delay=args.delay,
        restart_on_process_exit=args.restart_on_exit,
        case_sensitive=args.case_sensitive,
    )
    reloader.run()
