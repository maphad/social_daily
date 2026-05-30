import json
import io
import os
from datetime import datetime
import requests
from apify_client import ApifyClient

# ReportLab imports for the pretty PDF layout
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# --- 1. CONFIGURATION & API TOKENS ---
API_TOKEN = ""
BOX_TOKEN = ""  # Make sure to refresh this token!
client = ApifyClient(API_TOKEN)

# --- 2. AUXILIARY FUNCTIONS ---

def create_box_folder(folder_name, parent_folder_id="0", developer_token=""):
    """Creates a folder in Box and returns its new Folder ID."""
    box_api_url = "https://api.box.com/2.0/folders"
    headers = {
        "Authorization": f"Bearer {developer_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": folder_name,
        "parent": {"id": parent_folder_id}
    }
    
    response = requests.post(box_api_url, headers=headers, json=payload)
    if response.status_code == 201:
        folder_data = response.json()
        print(f"📁 Successfully created folder '{folder_name}'!")
        return folder_data["id"]
    elif response.status_code == 409:
        existing_folder_id = response.json()["context_info"]["conflicts"][0]["id"]
        print(f"ℹ️ Folder '{folder_name}' already exists. Using existing ID: {existing_folder_id}")
        return existing_folder_id
    else:
        print(f"❌ Failed to create Box folder: {response.status_code} - {response.text}")
        return None

def fetch_image(url):
    """Fetches image from direct URL, falls back to a clean placeholder if blocked."""
    placeholder_url = "https://placehold.co/150x150/f3f4f6/374151.png?text=No+Image"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        if url:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
                return Image(io.BytesIO(response.content), width=1.2*inch, height=1.2*inch)
    except Exception as e:
        print(f"   ⚠️ Could not fetch thumbnail image from stream: {e}")
        
    try:
        res = requests.get(placeholder_url)
        return Image(io.BytesIO(res.content), width=1.2*inch, height=1.2*inch)
    except:
        return Paragraph("<b>[No Image]</b>", getSampleStyleSheet()['Normal'])

def generate_pdf_buffer(posts_data):
    """Generates the pretty PDF completely in-memory and returns a BytesIO buffer."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
    )
    story = []
    
    styles = getSampleStyleSheet()
    primary_color = colors.HexColor("#1e1b4b")  # Deep Navy
    text_muted = colors.HexColor("#4b5563")     # Charcoal Muted Gray
    bg_light = colors.HexColor("#f8fafc")       # Soft Card BG
    
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold',
        fontSize=24, leading=28, textColor=primary_color, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'], fontName='Helvetica',
        fontSize=10, textColor=text_muted, spaceAfter=20
    )
    username_style = ParagraphStyle(
        'MetaUsername', fontName='Helvetica-Bold', fontSize=12, textColor=primary_color, spaceAfter=3
    )
    caption_style = ParagraphStyle(
        'MetaCaption', fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor("#1f2937")
    )
    stats_style = ParagraphStyle(
        'MetaStats', fontName='Helvetica-Oblique', fontSize=9, textColor=text_muted
    )

    # Document Header Elements
    story.append(Paragraph("Instagram Niche Report", title_style))
    current_date = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(f"Generated on {current_date} • Global Top 3 Performance Analytics", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Process each post into a beautiful UI row
    for item in posts_data:
        try:
            dt = datetime.strptime(item['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ")
            formatted_date = dt.strftime("%b %d, %Y at %I:%M %p")
        except:
            formatted_date = item['timestamp']

        # Pass the newly explicit thumbnail_url field into the renderer
        img_flowable = fetch_image(item.get("thumbnail_url"))
        
        text_details = [
            Paragraph(f"{item['username']}", username_style),
            Paragraph(f"<i>Posted on {formatted_date}</i>", stats_style),
            Spacer(1, 6),
            Paragraph(item['caption'] if item['caption'] else "[No Caption]", caption_style),
            Spacer(1, 8),
            Paragraph(f"❤️ {item['likes']:,} Likes &nbsp;&nbsp;&nbsp;&nbsp; 💬 {item['comments']:,} Comments", stats_style)
        ]
        
        card_table = Table([[img_flowable, text_details]], colWidths=[1.4*inch, 5.6*inch])
        card_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BACKGROUND', (0,0), (-1,-1), bg_light),
            ('TOPPADDING', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ]))
        
        story.append(card_table)
        story.append(Spacer(1, 15))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --- 3. MAIN WORKFLOW EXECUTION ---

instagram_handles = ["nasa", "natgeo", "nike", "spacex", "starbucks", "airbnb", "google", "playstation", "lego", "nintendo"]
profile_urls = [f"https://www.instagram.com/{handle}/" for handle in instagram_handles]

run_input = {
    "directUrls": profile_urls,
    "resultsType": "posts",
    "resultsLimit": 1, 
    "searchLimit": 1,
}

print(f"🚀 Scraping the single top post from {len(profile_urls)} profiles...")

try:
    # Execute Apify Actor
    run = client.actor("apify/instagram-scraper").call(run_input=run_input)
    all_scraped_posts = client.dataset(run.default_dataset_id).list_items().items
    
    cleaned_posts = []
    for item in all_scraped_posts:
        username = item.get("ownerUsername") or item.get("inputUrl", "").strip("/").split("/")[-1]
        
        # Explicitly capturing the media thumbnail url mapping
        img_url = item.get("displayUrl") or item.get("thumbnailUrl") or ""
        
        cleaned_posts.append({
            "username": f"@{username}",
            "url": item.get("url"),
            "caption": item.get("caption", ""),
            "likes": item.get("likesCount", 0),
            "comments": item.get("commentsCount", 0),
            "timestamp": item.get("timestamp"),
            "thumbnail_url": img_url  # Added explicitly here!
        })
        
    # Sort and slice out global top 3
    global_top_3 = sorted(cleaned_posts, key=lambda x: x["likes"], reverse=True)[:3]
    
    print("\n🏆 GLOBAL TOP 3 POSTS IDENTIFIED")
    for idx, post in enumerate(global_top_3, 1):
        print(f"  {idx}. {post['username']} | ❤️ {post['likes']:,} Likes")
        print(f"     🖼️ Thumbnail URL: {post['thumbnail_url']}")

    # --- 4. GENERATE THE PRETTY PDF ---
    print("\n🎨 Designing and generating the Analytics PDF...")
    pdf_buffer = generate_pdf_buffer(global_top_3)

    # --- 5. UPLOAD TO BOX ---
    BOX_FOLDER_ID = create_box_folder("Instagram Top Posts Niche", "0", BOX_TOKEN)
    
    if BOX_FOLDER_ID:
        filename = f"instagram_top_3_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        print(f"📤 Uploading presentation PDF '{filename}' to Box...")
        
        box_upload_url = "https://upload.box.com/api/2.0/files/content"
        headers = {"Authorization": f"Bearer {BOX_TOKEN}"}
        
        attributes = {
            "name": filename,
            "parent": {"id": BOX_FOLDER_ID}
        }
        
        payload = {
            "attributes": (None, json.dumps(attributes), "application/json"),
            "file": (filename, pdf_buffer, "application/pdf")
        }
        
        response = requests.post(box_upload_url, headers=headers, files=payload)
        
        if response.status_code == 201:
            file_id = response.json()["entries"][0]["id"]
            print(f"🎉 Success! Beautiful analytics PDF saved directly to Box. ID: {file_id}")
        elif response.status_code == 409:
            print("🔄 A report with today's date already exists in your Box destination folder.")
        else:
            print(f"❌ Box Upload Failed. Status: {response.status_code}\n{response.text}")

except Exception as e:
    print(f"❌ Operation encountered a terminal error: {e}")