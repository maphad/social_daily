import json
import os
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def load_user_preferences(config_path=None):
    """
    Load user preferences from the config file.
    Falls back to config/user_preferences.json relative to the project root.
    """
    if config_path is None:
        project_root = Path(__file__).resolve().parent.parent
        config_path = project_root / "config" / "user_preferences.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_instagram_handles(preferences):
    """
    Extract Instagram handles from user preferences.
    Returns a list of handles (without @ prefix).
    """
    instagram_config = preferences.get("platforms", {}).get("instagram", {})
    followed_users = instagram_config.get("followed_users", [])

    if not followed_users:
        print("⚠️  No Instagram handles found in user_preferences.json.")
        print("   Add handles to platforms.instagram.followed_users in config/user_preferences.json")
        return []

    # Strip @ prefix if present
    return [handle.lstrip("@") for handle in followed_users]


def filter_posts_last_24_hours(posts):
    """
    Filter posts to only include those from the last 24 hours.
    Posts without a valid timestamp are excluded.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_posts = []

    for post in posts:
        timestamp_str = post.get("timestamp")
        if not timestamp_str:
            continue

        try:
            # Apify typically returns ISO 8601 timestamps
            post_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            if post_time >= cutoff:
                recent_posts.append(post)
        except (ValueError, TypeError):
            # Skip posts with unparseable timestamps
            continue

    return recent_posts


def create_box_folder(folder_name, parent_folder_id="0", developer_token=""):
    """
    Creates a folder in Box and returns its new Folder ID.
    parent_folder_id defaults to "0" (the root folder).
    """
    box_api_url = "https://api.box.com/2.0/folders"

    headers = {
        "Authorization": f"Bearer {developer_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": folder_name,
        "parent": {
            "id": parent_folder_id
        }
    }

    response = requests.post(box_api_url, headers=headers, json=payload)

    if response.status_code == 201:
        folder_data = response.json()
        new_folder_id = folder_data["id"]
        print(f"📁 Successfully created folder '{folder_name}'!")
        print(f"🆔 New Box Folder ID: {new_folder_id}")
        return new_folder_id

    elif response.status_code == 409:
        existing_folder_id = response.json()["context_info"]["conflicts"][0]["id"]
        print(f"ℹ️ Folder '{folder_name}' already exists. Using existing ID: {existing_folder_id}")
        return existing_folder_id

    else:
        print(f"❌ Failed to create folder. Status code: {response.status_code}")
        print(f"📋 Details: {response.text}")
        return None


def scrape_instagram(handles, api_token, results_limit=5):
    """
    Scrape recent posts from the given Instagram handles.
    
    Args:
        handles: List of Instagram usernames (without @)
        api_token: Apify API token
        results_limit: Max posts to fetch per profile (fetch more to allow filtering)
    
    Returns:
        List of cleaned post dicts, filtered to last 24 hours
    """
    if not handles:
        return []

    client = ApifyClient(api_token)
    profile_urls = [f"https://www.instagram.com/{handle}/" for handle in handles]

    # Fetch more posts per profile since we'll filter by recency afterward
    # onlyPostsNewerThan is a best-effort server-side hint (known to be unreliable)
    # so we still apply client-side filtering as a safety net
    run_input = {
        "directUrls": profile_urls,
        "resultsType": "posts",
        "resultsLimit": results_limit,
        "searchLimit": 1,
        "onlyPostsNewerThan": "1 day",
    }

    print(f"🚀 Scraping up to {results_limit} recent posts from {len(handles)} profiles...")
    print(f"   Profiles: {', '.join(handles)}")

    run = client.actor("apify/instagram-scraper").call(run_input=run_input)
    all_scraped_posts = client.dataset(run.default_dataset_id).list_items().items

    # Parse and clean
    cleaned_posts = []
    for item in all_scraped_posts:
        username = item.get("ownerUsername") or item.get("inputUrl", "").strip("/").split("/")[-1]
        cleaned_posts.append({
            "username": f"@{username}",
            "url": item.get("url"),
            "caption": item.get("caption", ""),
            "likes": item.get("likesCount", 0),
            "comments": item.get("commentsCount", 0),
            "timestamp": item.get("timestamp"),
        })

    # Filter to last 24 hours only
    recent_posts = filter_posts_last_24_hours(cleaned_posts)
    print(f"📅 Found {len(recent_posts)} posts from the last 24 hours (out of {len(cleaned_posts)} total)")

    return recent_posts


def select_top_posts(posts, top_n=3):
    """Select the top N posts by likes."""
    return sorted(posts, key=lambda x: x["likes"], reverse=True)[:top_n]


def upload_to_box(data, filename, box_token, folder_path=None):
    """Upload JSON data to Box in a date-stamped folder structure."""
    if folder_path is None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        folder_path = f"daily_raw/{today}/instagram"

    # Create nested folder path
    folder_id = "0"
    for segment in folder_path.split("/"):
        folder_id = create_box_folder(segment, folder_id, box_token)
        if not folder_id:
            print("❌ Could not create/find Box folder. Skipping upload.")
            return

    print(f"\n📤 Uploading '{filename}' to Box...")

    json_bytes = json.dumps(data, indent=4).encode("utf-8")
    box_upload_url = "https://upload.box.com/api/2.0/files/content"

    headers = {"Authorization": f"Bearer {box_token}"}
    attributes = {
        "name": filename,
        "parent": {"id": folder_id}
    }
    payload = {
        "attributes": (None, json.dumps(attributes), "application/json"),
        "file": (filename, json_bytes, "application/octet-stream")
    }

    response = requests.post(box_upload_url, headers=headers, files=payload)

    if response.status_code == 201:
        file_id = response.json()["entries"][0]["id"]
        print(f"🎉 Success! File uploaded to Box. File ID: {file_id}")
    elif response.status_code == 409:
        print("🔄 File already exists in Box. Delete the old file or change the filename to overwrite.")
    else:
        print(f"❌ Box upload failed. Status: {response.status_code}")
        print(f"📋 Details: {response.text}")


# --- Main execution ---
if __name__ == "__main__":
    # Load tokens from environment (fall back to placeholders for dev)
    API_TOKEN = os.environ.get("APIFY_API_TOKEN", "TODO")
    BOX_TOKEN = os.environ.get("BOX_ACCESS_TOKEN", "TODO")

    # Load user preferences and extract Instagram handles
    preferences = load_user_preferences()
    instagram_handles = get_instagram_handles(preferences)

    if not instagram_handles:
        print("❌ No handles to scrape. Update config/user_preferences.json with your target profiles.")
        exit(1)

    print(f"👤 Loaded {len(instagram_handles)} profiles from user preferences")

    try:
        # Scrape and filter to last 24 hours
        recent_posts = scrape_instagram(instagram_handles, API_TOKEN, results_limit=5)

        if not recent_posts:
            print("\n⚠️  No posts found from the last 24 hours. The digest will be empty for Instagram today.")
            exit(0)

        # Select top 3
        top_posts = select_top_posts(recent_posts, top_n=3)

        # Display results
        print("\n" + "=" * 50)
        print("🏆 TOP 3 INSTAGRAM POSTS (Last 24 Hours)")
        print("=" * 50)
        for idx, post in enumerate(top_posts, 1):
            print(f"\n{idx}. 🔥 {post['username']} | ❤️ {post['likes']} Likes")
            print(f"   � URL: {post['url']}")
            print(f"   📝 Text: {post['caption'][:90]}...")
            print(f"   🕐 Posted: {post['timestamp']}")

        # Upload to Box
        upload_to_box({"items": top_posts}, "instagram_trends.json", BOX_TOKEN)

    except Exception as e:
        print(f"❌ Operation failed: {e}")
