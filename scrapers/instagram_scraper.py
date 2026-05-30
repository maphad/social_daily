import json
from apify_client import ApifyClient

# 1. Initialize the ApifyClient with your personal API token
# (Best practice: use an environment variable or paste your token string directly)
API_TOKEN = "{TODO_REPLACE_WITH_YOUR_API_KEY}"
client = ApifyClient(API_TOKEN)

# 2. Configure what you want to scrape
# Adjust the mode to "profile", "hashtag", "postUrl", etc.
run_input = {
    "mode": "profile",
    "usernames": ["natgeo"],  # The Instagram handle you want to target
    "maxPosts": 5,            # Keep it small for your first test run
    "maxComments": 2,         # Set to > 0 if you need comment data
    "includeProfile": True,
}

print("🚀 Starting the Instagram Scraper Actor on Apify cloud...")

# 3. Call the Actor and wait for it to finish
# We use automation-lab's robust wrapper here
run = client.actor("automation-lab/instagram-scraper").call(run_input=run_input)

print(f"📊 Dataset ID: {run.default_dataset_id}")

# 4. Fetch the results from the dataset
print("\n📥 Fetching scraped data back to local machine...\n")
dataset_items = client.dataset(run.default_dataset_id).list_items().items

# 5. Save the data locally to a JSON file
with open("instagram_data.json", "w", encoding="utf-8") as f:
    json.dump(dataset_items, f, indent=4, ensure_ascii=False)

print("💾 Success! Data saved to 'instagram_data.json'. Here is a sample of the structure:")

# Print a preview of the first item found
if dataset_items:
    print(json.dumps(dataset_items[0], indent=2)[:500] + "...\n[Truncated]")
else:
    print("No items found. Double check your target profile is public.")