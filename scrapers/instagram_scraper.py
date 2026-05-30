import json
from apify_client import ApifyClient

# 1. Initialize the ApifyClient with your personal API token
# (Best practice: use an environment variable or paste your token string directly)
API_TOKEN = ""
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