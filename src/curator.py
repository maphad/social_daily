#!/usr/bin/env python3
"""
Local Social Daily Curator
Runs as a single local script for Windows/macOS demo execution.
"""

import html
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

from email_sender import send_digest

load_dotenv()

LOCAL_PREFERENCES_PATH = Path("config") / "user_preferences.json"
LOCAL_SAMPLE_DATA_ROOT = Path("sample_data")
LOCAL_OUTPUT_ROOT = Path("output")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOX_DEVELOPER_TOKEN = os.getenv("BOX_ACCESS_TOKEN")

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")


class BoxStorage:
    """Minimal Box API client using developer token."""

    API_BASE = "https://api.box.com/2.0"
    UPLOAD_BASE = "https://upload.box.com/api/2.0"

    def __init__(self, developer_token: str):
        self.developer_token = developer_token
        self.headers = {
            "Authorization": f"Bearer {self.developer_token}",
        }

    def _normalize_path(self, folder_path: str) -> List[str]:
        cleaned = folder_path.strip("/")
        return [segment for segment in cleaned.split("/") if segment]

    def _list_folder_items(self, folder_id: str) -> List[Dict[str, Any]]:
        url = f"{self.API_BASE}/folders/{folder_id}/items"
        response = requests.get(
            url,
            headers=self.headers,
            params={"limit": 1000, "fields": "name,type"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get("entries", [])

    def get_folder_id_by_path(self, folder_path: str) -> Optional[str]:
        folder_id = "0"
        for segment in self._normalize_path(folder_path):
            items = self._list_folder_items(folder_id)
            match = next(
                (item for item in items if item.get("type") == "folder" and item.get("name") == segment),
                None,
            )
            if match is None:
                return None
            folder_id = match["id"]
        return folder_id

    def create_folder_path(self, folder_path: str) -> str:
        folder_id = "0"
        for segment in self._normalize_path(folder_path):
            items = self._list_folder_items(folder_id)
            existing = next(
                (item for item in items if item.get("type") == "folder" and item.get("name") == segment),
                None,
            )
            if existing:
                folder_id = existing["id"]
                continue
            response = requests.post(
                f"{self.API_BASE}/folders",
                headers={**self.headers, "Content-Type": "application/json"},
                json={"name": segment, "parent": {"id": folder_id}},
                timeout=30,
            )
            response.raise_for_status()
            folder_id = response.json()["id"]
        return folder_id

    def _get_file_id(self, folder_id: str, filename: str) -> Optional[str]:
        items = self._list_folder_items(folder_id)
        match = next(
            (item for item in items if item.get("type") == "file" and item.get("name") == filename),
            None,
        )
        return match["id"] if match else None

    def list_json_files(self, folder_path: str) -> List[str]:
        folder_id = self.get_folder_id_by_path(folder_path)
        if folder_id is None:
            return []
        return [
            item["name"]
            for item in self._list_folder_items(folder_id)
            if item.get("type") == "file" and item.get("name", "").lower().endswith(".json")
        ]

    def download_json_file(self, folder_path: str, filename: str) -> Dict[str, Any]:
        folder_id = self.get_folder_id_by_path(folder_path)
        if folder_id is None:
            raise FileNotFoundError(f"Box folder not found: {folder_path}")

        file_id = self._get_file_id(folder_id, filename)
        if file_id is None:
            raise FileNotFoundError(f"File not found in Box: {filename}")

        response = requests.get(
            f"{self.API_BASE}/files/{file_id}/content",
            headers=self.headers,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def upload_text_file(self, folder_path: str, filename: str, content: str) -> bool:
        folder_id = self.create_folder_path(folder_path)
        file_id = self._get_file_id(folder_id, filename)
        upload_url = (
            f"{self.UPLOAD_BASE}/files/{file_id}/content"
            if file_id
            else f"{self.UPLOAD_BASE}/files/content"
        )

        response = requests.post(
            upload_url,
            headers={"Authorization": f"Bearer {self.developer_token}"},
            data={"parent_id": folder_id} if not file_id else {},
            files={"file": (filename, content.encode("utf-8"))},
            timeout=60,
        )
        response.raise_for_status()
        return True


class LocalBoxSimulator:
    """Local fallback for Box-style file storage."""

    def __init__(self) -> None:
        self.base_path = LOCAL_SAMPLE_DATA_ROOT

    def _folder_path(self, folder_path: str) -> Path:
        return self.base_path / Path(folder_path.strip("/"))

    def list_json_files(self, folder_path: str) -> List[str]:
        folder = self._folder_path(folder_path)
        if not folder.exists() or not folder.is_dir():
            return []
        return [str(path.name) for path in folder.glob("*.json") if path.is_file()]

    def download_json_file(self, folder_path: str, filename: str) -> Dict[str, Any]:
        path = self._folder_path(folder_path) / filename
        if not path.exists():
            raise FileNotFoundError(f"Local fallback file not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def upload_text_file(self, folder_path: str, filename: str, content: str) -> bool:
        target_folder = LOCAL_OUTPUT_ROOT / Path(folder_path.strip("/"))
        target_folder.mkdir(parents=True, exist_ok=True)
        target_path = target_folder / filename
        target_path.write_text(content, encoding="utf-8")
        return True


def load_preferences(path: Path = LOCAL_PREFERENCES_PATH) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Preferences file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_box_client() -> Any:
    if BOX_DEVELOPER_TOKEN:
        try:
            return BoxStorage(BOX_DEVELOPER_TOKEN)
        except Exception as error:
            print(f"⚠️  Box API unavailable, falling back to local files: {error}")
    return LocalBoxSimulator()


def iso_today() -> str:
    return date.today().isoformat()


def choose_candidate_file(platform: str, available_files: List[str]) -> Optional[str]:
    normalized = [name.lower() for name in available_files]
    for candidate in (f"{platform}.json", f"{platform}_trends.json", f"{platform}-trends.json"):
        if candidate in normalized:
            return available_files[normalized.index(candidate)]
    for candidate in available_files:
        if platform in candidate.lower():
            return candidate
    return None


def build_prompt(platform_payloads: Dict[str, List[Dict[str, Any]]], preferences: Dict[str, Any]) -> str:
    active_platforms = [name for name, cfg in preferences.get("platforms", {}).items() if cfg.get("enabled")]
    preferences_summary = json.dumps(
        {name: preferences.get("platforms", {}).get(name, {}) for name in active_platforms},
        indent=2,
    )

    lines = [
        "You are a deterministic content curator for a professional daily digest.",
        "Use the user preferences exactly as provided.",
        "Score each item, select EXACTLY 3 high-signal links per active platform, and output a clean Markdown digest.",
        "Do not output analysis, numbered steps, or JSON. Only return valid Markdown with headings and bullet links.",
        "If a platform has fewer than 3 strong items, choose the best available items to reach 3 selections.",
        "Include title, source/author, score, and a short relevance note for each selected item.",
        "Write platform sections in this order: " + ", ".join(active_platforms).upper() + ".",
        "",
        "USER PREFERENCES:",
        preferences_summary,
        "",
        "PLATFORM ITEM DATA:",
    ]

    for platform, items in platform_payloads.items():
        lines.append(f"== {platform.upper()} ==")
        if not items:
            lines.append("(No raw items available for this platform.)")
            lines.append("")
            continue
        lines.append(json.dumps(items, indent=2)[:1500])
        lines.append("")

    lines.append(
        "For each selected link, ensure the Markdown output is concise, readable, and formatted for a daily email digest."
    )
    lines.append("Use headings for each platform and a bullet list of exactly three links per active platform.")
    return "\n".join(lines)


def query_openai(prompt: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY must be set in your local environment to run the curator.")

    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "You are a precise content curator and digest generator. Output only Markdown and be deterministic.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": 1200,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    }
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def markdown_to_html(markdown_text: str) -> str:
    escaped = html.escape(markdown_text)
    return f"<html><body><pre style='font-family:Arial, sans-serif; white-space:pre-wrap'>{escaped}</pre></body></html>"


def run_curator() -> int:
    today = iso_today()
    raw_folder = f"/daily_raw/{today}"
    digest_folder = f"/digests/{today}"

    preferences = load_preferences()
    box = get_box_client()

    active_platforms = [
        platform
        for platform, cfg in preferences.get("platforms", {}).items()
        if cfg.get("enabled", False)
    ]
    if not active_platforms:
        print("⚠️  No active platforms found in preferences. Set enabled=true for at least one platform.")
        return 1

    available_files = box.list_json_files(raw_folder)
    print(f"Found raw Box files in {raw_folder}: {available_files}")

    raw_payloads: Dict[str, List[Dict[str, Any]]] = {}
    for platform in active_platforms:
        # Check platform subfolder first (e.g., /daily_raw/2026-05-30/instagram/)
        platform_folder = f"{raw_folder}/{platform}"
        platform_files = box.list_json_files(platform_folder)

        # Fall back to the flat folder if no subfolder exists
        if platform_files:
            search_folder = platform_folder
            search_files = platform_files
        else:
            search_folder = raw_folder
            search_files = available_files

        raw_filename = choose_candidate_file(platform, search_files)
        if not raw_filename:
            print(f"⚠️  No raw JSON file found for {platform} in {search_folder}.")
            raw_payloads[platform] = []
            continue
        try:
            raw_payloads[platform] = box.download_json_file(search_folder, raw_filename).get("items", [])
            print(f"✓ Downloaded {raw_filename} for {platform} ({len(raw_payloads[platform])} items)")
            if raw_payloads[platform]:
                print(f"   Sample item keys: {list(raw_payloads[platform][0].keys())}")
        except Exception as error:
            print(f"⚠️  Error downloading {raw_filename}: {error}")
            raw_payloads[platform] = []

    prompt = build_prompt(raw_payloads, preferences)
    markdown_digest = query_openai(prompt)
    print(f"\n📝 Generated digest preview:\n{markdown_digest[:500]}\n")

    box.upload_text_file(digest_folder, "digest.md", markdown_digest)
    print(f"✓ Uploaded digest.md to Box path {digest_folder} (or local output fallback)")

    # Also save locally for easy access
    local_digest_path = LOCAL_OUTPUT_ROOT / digest_folder.strip("/") / "digest.md"
    local_digest_path.parent.mkdir(parents=True, exist_ok=True)
    local_digest_path.write_text(markdown_digest, encoding="utf-8")
    print(f"✓ Saved local copy to {local_digest_path}")

    delivery_config = preferences.get("delivery") or {}
    delivery_channel = delivery_config.get("channel")
    delivery_destination = delivery_config.get("destination")

    delivery_channels: List[str] = []
    if delivery_channel:
        delivery_channels.append(delivery_channel)
    else:
        delivery_channels = preferences.get("user", {}).get("delivery_channels", ["console"])

    if not delivery_channels:
        delivery_channels = ["console"]

    if "email" in delivery_channels and not delivery_destination:
        delivery_destination = preferences.get("user", {}).get("email")
        if not delivery_destination:
            print("⚠️  Email delivery requested but no destination email is configured. Falling back to console.")
            delivery_channels = [channel for channel in delivery_channels if channel != "email"]
            if not delivery_channels:
                delivery_channels = ["console"]

    recipient_email = delivery_destination or preferences.get("user", {}).get("email")
    recipient_name = preferences.get("user", {}).get("name", "Social Daily Reader")
    html_content = markdown_to_html(markdown_digest)

    delivery_status = send_digest(
        recipient_email,
        recipient_name,
        html_content,
        today,
        delivery_channels=delivery_channels,
    )

    print(f"Delivery status: {delivery_status}")
    print("\n✅ Local curator run complete.")
    return 0


def main() -> int:
    try:
        return run_curator()
    except Exception as error:
        print(f"\n❌ Fatal error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
