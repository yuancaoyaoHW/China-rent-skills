#!/usr/bin/env python3
import argparse
import json
import subprocess
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable


PREFERENCES_FILE = "rental_preferences.json"
VALID_PREFS = {"", "like", "dislike"}


class BadRequest(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def empty_preferences() -> dict:
    return {"version": 1, "updated_at": None, "preferences": {}}


def read_preferences(repo_root: Path) -> dict:
    path = repo_root / PREFERENCES_FILE
    if not path.exists():
        return empty_preferences()
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data.get("preferences"), dict):
        data["preferences"] = {}
    data.setdefault("version", 1)
    data.setdefault("updated_at", None)
    return data


def write_preferences(repo_root: Path, data: dict) -> None:
    path = repo_root / PREFERENCES_FILE
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def save_preference(repo_root: Path, payload: dict) -> dict:
    url = str(payload.get("url") or "").strip()
    pref = str(payload.get("pref") or "").strip()
    if not url:
        raise BadRequest("Missing listing url")
    if pref not in VALID_PREFS:
        raise BadRequest("Preference must be like, dislike, or empty")

    data = read_preferences(repo_root)
    preferences = data["preferences"]
    now = utc_now()

    if pref:
        listing = payload.get("listing") if isinstance(payload.get("listing"), dict) else {}
        preferences[url] = {
            "pref": pref,
            "updated_at": now,
            "url": url,
            "rank": listing.get("rank"),
            "title": listing.get("title"),
            "community": listing.get("community"),
            "rent": listing.get("rent"),
            "layout": listing.get("layout"),
            "area_m2": listing.get("area_m2"),
            "platform": listing.get("platform"),
        }
    else:
        preferences.pop(url, None)

    data["updated_at"] = now
    write_preferences(repo_root, data)
    return {"status": "saved", "updated_at": now, "preference_count": len(preferences)}


def preference_record(url: str, pref: str, listing: dict, updated_at: str) -> dict:
    return {
        "pref": pref,
        "updated_at": updated_at,
        "url": url,
        "rank": listing.get("rank"),
        "title": listing.get("title"),
        "community": listing.get("community"),
        "rent": listing.get("rent"),
        "layout": listing.get("layout"),
        "area_m2": listing.get("area_m2"),
        "platform": listing.get("platform"),
    }


def save_preferences_bulk(repo_root: Path, payload: dict) -> dict:
    entries = payload.get("preferences")
    if not isinstance(entries, list):
        raise BadRequest("preferences must be a list")

    data = read_preferences(repo_root)
    preferences = data["preferences"]
    now = utc_now()

    for entry in entries:
        if not isinstance(entry, dict):
            raise BadRequest("Each preference entry must be an object")
        url = str(entry.get("url") or "").strip()
        pref = str(entry.get("pref") or "").strip()
        if not url:
            raise BadRequest("Missing listing url")
        if pref not in VALID_PREFS:
            raise BadRequest("Preference must be like, dislike, or empty")
        if pref:
            listing = entry.get("listing") if isinstance(entry.get("listing"), dict) else entry
            preferences[url] = preference_record(url, pref, listing, now)
        else:
            preferences.pop(url, None)

    data["updated_at"] = now
    write_preferences(repo_root, data)
    return {"status": "saved", "updated_at": now, "preference_count": len(preferences)}


def run_command(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(cwd), text=True, capture_output=True, check=False)


def require_success(result: subprocess.CompletedProcess, action: str) -> None:
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"{action} failed: {detail}")


def git_commit_and_push(
    repo_root: Path,
    message: str,
    runner: Callable[[list[str], Path], subprocess.CompletedProcess] = run_command,
    push: bool = True,
) -> dict:
    status = runner(["git", "status", "--porcelain", "--", PREFERENCES_FILE], repo_root)
    require_success(status, "git status")
    if not status.stdout.strip():
        return {"status": "unchanged", "pushed": False}

    add = runner(["git", "add", PREFERENCES_FILE], repo_root)
    require_success(add, "git add")
    commit = runner(["git", "commit", "-m", message], repo_root)
    require_success(commit, "git commit")

    if not push:
        return {"status": "committed", "pushed": False}

    branch = runner(["git", "branch", "--show-current"], repo_root)
    require_success(branch, "git branch")
    branch_name = branch.stdout.strip()
    if not branch_name:
        raise RuntimeError("Cannot push from a detached HEAD")

    push_result = runner(["git", "push", "origin", branch_name], repo_root)
    require_success(push_result, "git push")
    return {"status": "pushed", "pushed": True, "branch": branch_name}


class RentalPreferenceHandler(SimpleHTTPRequestHandler):
    repo_root: Path
    auto_push: bool

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] == "/api/preferences":
            self.send_json(read_preferences(self.repo_root))
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if path not in {"/api/preferences", "/api/preferences/bulk"}:
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown API endpoint")
            return
        try:
            payload = self.read_json_body()
            if path == "/api/preferences/bulk":
                saved = save_preferences_bulk(self.repo_root, payload)
            else:
                saved = save_preference(self.repo_root, payload)
            git_result = git_commit_and_push(
                self.repo_root,
                "Update rental preferences",
                push=self.auto_push,
            )
            self.send_json({"ok": True, "save": saved, "git": git_result})
        except BadRequest as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise BadRequest("Invalid JSON body") from exc
        if not isinstance(payload, dict):
            raise BadRequest("JSON body must be an object")
        return payload

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def make_handler(repo_root: Path, auto_push: bool) -> type[RentalPreferenceHandler]:
    class ConfiguredRentalPreferenceHandler(RentalPreferenceHandler):
        pass

    ConfiguredRentalPreferenceHandler.repo_root = repo_root
    ConfiguredRentalPreferenceHandler.auto_push = auto_push

    def handler(*args, **kwargs):
        return ConfiguredRentalPreferenceHandler(*args, directory=str(repo_root), **kwargs)

    return handler


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve rental HTML and sync preferences to git.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--push", action="store_true", help="Push preference commits to origin/current-branch.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    handler = make_handler(repo_root, args.push)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving {repo_root} on http://{args.host}:{args.port} (auto_push={args.push})", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
