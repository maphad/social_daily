import json
import requests
from apify_client import ApifyClient

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
    
    # Define the new folder's name and where it should live
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
        # 409 means a folder with this name already exists. 
        # Box returns the existing folder's ID in the error context.
        existing_folder_id = response.json()["context_info"]["conflicts"][0]["id"]
        print(f"ℹ️ Folder '{folder_name}' already exists. Using existing ID: {existing_folder_id}")
        return existing_folder_id
        
    else:
        print(f"❌ Failed to create folder. Status code: {response.status_code}")
        print(f"📋 Details: {response.text}")
        return None

# 1. Initialize the ApifyClient with your personal API token
# (Best practice: use an environment variable or paste your token string directly)

API_TOKEN = "TODO"
BOX_TOKEN = "TODO"
client = ApifyClient(API_TOKEN)

# 2. Configure what you want to scrape
# Adjust the mode to "profile", "hashtag", "postUrl", etc.

# 2. Target profiles
instagram_handles = ["nasa", "natgeo", "nike", "spacex", "starbucks", "airbnb", "google", "playstation", "lego", "nintendo"]
profile_urls = [f"https://www.instagram.com/{handle}/" for handle in instagram_handles]

# 3. Configure the input
# Setting resultsLimit to 1 ensures the browser fetches only the single most recent/top post per account
run_input = {
    "directUrls": profile_urls,
    "resultsType": "posts",
    "resultsLimit": 1, 
    "searchLimit": 1,
}

print(f"🚀 Scraping the single top post from {len(profile_urls)} profiles to find the absolute top 3...")

try:
    # 4. Execute the Actor run
    run = client.actor("apify/instagram-scraper").call(run_input=run_input)
    
    # 5. Extract all returned items
    all_scraped_posts = client.dataset(run.default_dataset_id).list_items().items
    
    # 6. Parse and clean the structures
    cleaned_posts = []
    for item in all_scraped_posts:
        username = item.get("ownerUsername") or item.get("inputUrl", "").strip("/").split("/")[-1]
        cleaned_posts.append({
            "username": f"@{username}",
            "url": item.get("url"),
            "caption": item.get("caption", ""),
            "likes": item.get("likesCount", 0),
            "comments": item.get("commentsCount", 0),
            "timestamp": item.get("timestamp")
        })
        
    # 7. Apply global sorting by popularity metric (e.g., Likes) and slice the top 3
    # Change 'likes' to 'timestamp' if you want strictly chronological across profiles
    global_top_3 = sorted(cleaned_posts, key=lambda x: x["likes"], reverse=True)[:3]
    
    # 8. Display results
    print("\n" + "="*50 + "\n🏆 GLOBAL TOP 3 POSTS ACROSS ALL PROFILES\n" + "="*50)
    for idx, post in enumerate(global_top_3, 1):
        print(f"\n{idx}. 🔥 {post['username']} | ❤️ {post['likes']} Likes")
        print(f"   🔗 URL: {post['url']}")
        print(f"   📝 Text: {post['caption'][:90]}...")

except Exception as e:
    print(f"❌ Operation failed: {e}")

# --- 4. UPLOAD TO BOX VIA NATIVE API ---
# Automatically sets up your destination folder
BOX_FOLDER_ID = create_box_folder("Instagram Top Posts Niche", "0", BOX_TOKEN)

filename = "instagram_global_top_3.json"
print(f"\n📤 Uploading '{filename}' to Box using direct API...")

# Convert our data directly to an in-memory JSON file stream
json_bytes = json.dumps(global_top_3, indent=4).encode('utf-8')
    
# Box API endpoint for uploading files
box_upload_url = "https://upload.box.com/api/2.0/files/content"
    
# Setup Header with your Developer Token
headers = {
    "Authorization": f"Bearer {BOX_TOKEN}"
}
    
# Box requires the attributes (metadata) sent as a JSON string alongside the file binaries
attributes = {
    "name": filename,
    "parent": {"id": BOX_FOLDER_ID}
}
    
payload = {
    "attributes": (None, json.dumps(attributes), "application/json"),
    "file": (filename, json_bytes, "application/octet-stream")
}
    
# Execute the POST request
response = requests.post(box_upload_url, headers=headers, files=payload)
    
if response.status_code == 201:
    response_data = response.json()
    file_id = response_data["entries"][0]["id"]
    print(f"🎉 Success! File uploaded directly to Box.")
    print(f"📦 Box File ID: {file_id}")
elif response.status_code == 409:
    print("🔄 File already exists in Box folder. (To overwrite, delete the old file in Box first or change the filename variable).")
else:
    print(f"❌ Box Upload Failed. Status code: {response.status_code}")
    print(f"📋 Error Details: {response.text}")

