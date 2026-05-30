# Getting Started Guide

## Quick Start (Hackathon Demo)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Demo Curator
```bash
python src/curator.py
```

This will:
- Load sample user preferences from `config/user_preferences.json`
- Load pre-scraped trend data from `sample_data/`
- Score and rank content based on user interests
- Generate JSON and HTML digests
- Save outputs to `output/` folder

### 3. View the Generated Digest
```bash
# Open the HTML digest in your browser
open output/demo-user-001_2026-05-30_digest.html
```

## Project Structure

```
social_daily/
├── src/
│   ├── curator.py              # Main orchestration engine
│   ├── box_client.py           # Box API integration
│   ├── scorer.py               # Content scoring algorithm
│   └── email_sender.py         # Notification delivery
├── config/
│   ├── user_preferences.json   # User preferences template
│   └── apify_actors.json       # Apify actor configs
├── templates/
│   └── digest_template.html    # Email digest template
├── sample_data/
│   ├── linkedin_trends.json
│   ├── youtube_trends.json
│   └── instagram_trends.json
└── output/                     # Generated digests (created by curator)
```

## Customization

### Change User Preferences
Edit `config/user_preferences.json`:
```json
{
  "user": {
    "name": "Your Name",
    "email": "your@email.com"
  },
  "platforms": {
    "linkedin": {
      "interests": ["AI", "startup", "technology"],
      "excluded_keywords": ["crypto"],
      "followed_users": ["satya_nadella"]
    }
  }
}
```

### Add Sample Trend Data
Create `sample_data/YYYY-MM-DD/platform_trends.json` files with your own data.

## Next Steps for Full Implementation

### 1. Configure Apify Actors
- Create actors in Apify for [LinkedIn](https://apify.com/marketplace), [YouTube](https://apify.com/marketplace), [Instagram](https://apify.com/marketplace)
- Set output to upload to Box: `/raw-data/{date}/{platform}/trends.json`
- Enable cron scheduling for daily execution at midnight UTC

### 2. Configure Box Integration
- Create Box app token
- Set up folder structure: `/raw-data/`, `/digests/`
- Add credentials to `.env`

### 3. Deploy to AWS Lambda
```bash
serverless deploy
```

### 4. Set Up Email Delivery
- Configure SMTP credentials in `.env`
- Or integrate with AWS SES

## Architecture

```
Apify (Cron)
    ↓
Box Storage (/raw-data/{date}/{platform}/)
    ↓
Python Curator
    ↓
Score & Rank (Top 3 per platform)
    ↓
Generate Digest
    ↓
Deliver (Email/SMS/WhatsApp)
```

## Scoring Algorithm

Content is scored on:
- **Keyword Match (40%)**: How many user interests are mentioned
- **Engagement (30%)**: Likes, comments, views (normalized)
- **Recency (20%)**: Time decay over 7 days
- **Followed Account (10%)**: Bonus if author is in your follow list

Exclusion rules apply first - content with excluded keywords is rejected.

## Testing

### Test Scoring
Edit `sample_data/` JSON files and rerun curator to see different results.

### Test Email (Optional)
```python
from src.email_sender import EmailSender

sender = EmailSender()
sender.send_digest_email(
    "recipient@example.com",
    "John Doe",
    html_content,
    "2026-05-30"
)
```

## Troubleshooting

**Issue**: Import errors
```bash
# Make sure you're in the project root
cd /path/to/social_daily
python -m src.curator  # Use module syntax
```

**Issue**: Jinja2 template not found
```bash
# Ensure you're running from project root
pwd  # Should end with /social_daily
```

**Issue**: Sample data not loading
- Check file paths are correct: `sample_data/platform_trends.json`
- Ensure JSON is valid: `python -m json.tool sample_data/linkedin_trends.json`

## Files Modified/Created for Hackathon

- ✅ `src/curator.py` - Main curation engine
- ✅ `src/box_client.py` - Box API wrapper + LocalBoxSimulator
- ✅ `src/scorer.py` - Content scoring algorithm
- ✅ `src/email_sender.py` - Email delivery (optional)
- ✅ `config/user_preferences.json` - User preference template
- ✅ `config/apify_actors.json` - Apify configuration reference
- ✅ `templates/digest_template.html` - Email HTML template
- ✅ `sample_data/` - Pre-made trend data for testing
- ✅ `.env.example` - Environment variables template
- ✅ `requirements.txt` - Python dependencies

## Demo Tips for Judges

1. **Show the scoring logic** - Modify preferences in config, rerun curator to show personalization
2. **Show the digest** - Open HTML in browser to demonstrate beautiful email format
3. **Highlight content filtering** - Show how excluded keywords work (crypto removed)
4. **Emphasize the 3-item limit** - Key value proposition: prevent doomscrolling
5. **Explain architecture** - Box + Apify integration for production use
6. **Mention team features** - Extensible to support Box integration for real data

## Questions?

See [PRODUCT_SPEC.md](../PRODUCT_SPEC.md) for complete technical documentation.
