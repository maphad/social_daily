# Social Daily

A personalized social media curation agent that generates a daily digest of the top 3 most relevant posts from each of your social media platforms based on your interests and preferences.

## Overview

Social Daily solves the doomscrolling problem by delivering a curated, finite feed of the most relevant content from multiple social media platforms (LinkedIn, YouTube, Instagram, and more) directly to your inbox. Instead of spending hours browsing, you get a daily digest with just the best content tailored to your interests.

## Features

- **Multi-Platform Support**: Aggregate content from LinkedIn, YouTube, Instagram, Twitter, and more
- **Preference-Based Curation**: Customize what you want to see based on:
  - Topics/areas of interest
  - Specific people you follow
  - Content types and formats
  - Engagement levels and recency
- **Daily Digest Delivery**: Automatic email/SMS/WhatsApp delivery of your personalized feed
- **Doomscroll Prevention**: Strict limit of 3 items per platform per day
- **Cloud-Native Architecture**: Built on AWS with scalable, serverless components
- **Content Storage**: All digests archived in Box for historical reference
- **Intelligent Aggregation**: Uses trend data + user preferences to select top content

## Architecture

**Hackathon MVP** (Apify + Box + Python Curator):
```
┌─────────────────────────────────────────────────────────────┐
│                Apify Actors (Cron Scheduled)                 │
│     Scrapes LinkedIn, YouTube, Instagram daily              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│          Box Storage (Raw Trend Data)                        │
│   /raw-data/YYYY-MM-DD/{platform}/trends.json              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│        Python Curator (Runs on Schedule)                     │
│    1. Load user preferences                                  │
│    2. Fetch daily trends from Box                            │
│    3. Score & rank content (top 3 per platform)              │
│    4. Generate digest                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
   │  Email  │   │   SMS   │   │ WhatsApp│
   └─────────┘   └─────────┘   └─────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│        Box Storage (Digest Archive)                          │
│    /digests/YYYY-MM-DD/{user-id}-digest.html               │
└──────────────────────────────────────────────────────────────┘
```

**Key Components**:
- **Apify**: Scheduled web scraping (handles the hard part)
- **Box**: Centralized storage for trends and digests
- **Curator**: Intelligent content ranking and delivery
- **User Preferences**: Configurable interests, exclusions, followed accounts

## Technology Stack

- **Web Scraping**: [Apify](https://apify.com) (serverless web scraping actors)
- **File Storage**: [Box](https://box.com) (cloud storage for trends & digests)
- **Curation Engine**: Python 3.9+ (scoring algorithm, personalization)
- **Notifications**: Email (SMTP), SMS (Twilio), WhatsApp (Twilio)
- **Task Scheduling**: Apify cron + Optional AWS Lambda
- **Templating**: Jinja2 (HTML email generation)
- **Preferences**: JSON config (easily extensible to database)

## Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/maphad/social_daily.git
cd social_daily
pip install -r requirements.txt
```

### 2. Run Demo (30 seconds)
```bash
python src/curator.py
```

This generates:
- JSON digest in `output/`
- HTML email in `output/`
- Console summary of curated content

### 3. View Generated Digest
```bash
open output/*_digest.html
```

**See [QUICKSTART.md](./QUICKSTART.md) for detailed walkthrough and customization.**

## Production Setup

### Prerequisites
- Apify Account (for web scraping)
- Box Enterprise Account (for file storage)
- AWS Account (optional: for Lambda scheduler)
- SMTP credentials (for email delivery)

### Configuration
```bash
# Set up environment
cp .env.example .env
# Edit .env with your Apify and Box credentials
```

See [PRODUCT_SPEC.md](./PRODUCT_SPEC.md) for complete deployment guide and technical specifications.

## Documentation

- [Product Specification](./PRODUCT_SPEC.md) - Complete feature specification and technical requirements
- [Architecture Guide](./docs/ARCHITECTURE.md) - Detailed system design
- [API Documentation](./docs/API.md) - REST API endpoints for user management

## Contributing

This is a hackathon project. Feel free to open issues and submit pull requests!

## Team

Developed during the Cascadia AI Hackathon

## License

MIT 
