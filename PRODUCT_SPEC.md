# Social Daily - Product Specification

**Version**: 1.0  
**Date**: May 2026  
**Status**: Specification for Development

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Product Vision](#product-vision)
3. [Core Features](#core-features)
4. [User Workflows](#user-workflows)
5. [System Architecture](#system-architecture)
6. [Data Models](#data-models)
7. [API Specifications](#api-specifications)
8. [Notification Delivery](#notification-delivery)
9. [Storage & Organization](#storage--organization)
10. [Deployment & Operations](#deployment--operations)
11. [Success Metrics](#success-metrics)

---

## Executive Summary

Social Daily is an intelligent content curation agent that delivers personalized daily digests of the most relevant social media content to users. The product solves the "doomscrolling" problem by limiting users to exactly 3 curated posts per social media platform per day, based on their stated preferences and platform trends.

### Problem Statement
- Users spend excessive time scrolling social media without consuming quality content
- Trends and algorithm feeds often don't align with individual interests
- No centralized view across multiple platforms
- Manual curation of multiple platforms is time-consuming

### Solution
- Automated daily digest generation
- AI-powered content selection based on user preferences
- Multi-platform aggregation (LinkedIn, YouTube, Instagram, Twitter)
- Strict finite feed (3 items/platform/day)
- Delivery via preferred channel (email, SMS, WhatsApp)

---

## Product Vision

Social Daily enables professionals and content consumers to stay informed without the time commitment of social media browsing. By delivering a daily curated digest tailored to individual interests, we help users reclaim their time while staying connected to what matters most.

### Key Values
- **Efficiency**: 3 items/day per platform = minimal time commitment
- **Personalization**: Driven by user preferences, not algorithms
- **Accessibility**: Multiple delivery channels
- **Transparency**: Clear curation logic and source attribution
- **Privacy**: User data stored securely, no tracking

---

## Core Features

### 1. Multi-Platform Content Aggregation

**Supported Platforms**:
- LinkedIn (professional content, news, updates from followed users)
- YouTube (trending videos, channel subscriptions, categories)
- Instagram (trending posts, hashtags, followed accounts)
- Twitter/X (trending topics, followed accounts, search queries)
- Future: TikTok, Reddit, Medium, Substack

**Data Collection Method**:
- Apify actors for each platform
- Daily scheduled scraping (12:00 AM UTC recommended)
- Stores raw trend data in Box by date and platform
- Storage format: JSON files with metadata (likes, comments, recency, engagement)

### 2. User Preference Management

**Per-User Profile Structure**:
```
UserProfile:
  - user_id (unique identifier)
  - email
  - phone_number
  - whatsapp_number
  - delivery_preference (email | sms | whatsapp | all)
  - delivery_time (HH:MM in user timezone)
  - timezone
  - platform_preferences (array):
    - platform (linkedin | youtube | instagram | twitter)
    - enabled (boolean)
    - interests (array of keywords/topics)
    - followed_users (array of usernames/accounts)
    - content_types (array: video, article, image, carousel, etc.)
    - keywords_to_include (array)
    - keywords_to_exclude (array)
    - minimum_engagement (threshold for likes/comments)
    - recency_preference (recent_first | trending_first)
```

**Preference Input Methods**:
- Web form/dashboard (future MVP)
- API endpoint for programmatic input
- Configuration file (JSON)
- Interactive onboarding flow

### 3. Daily Digest Generation

**Process Flow**:
1. AWS Lambda triggered by EventBridge at user's delivery time
2. Load user preferences from DynamoDB/Box
3. Fetch daily trend data from Box (date-stamped folders)
4. For each enabled platform:
   - Filter content against user preferences
   - Score content based on:
     - Keyword match (interests/exclusions)
     - Engagement metrics
     - Recency
     - Followed account priority
   - Select top 3 highest-scoring items
5. Generate digest HTML/text
6. Store digest in Box (for archive)
7. Send via user's preferred delivery channel(s)

**Scoring Algorithm**:
```
score = (
  keyword_match_score * 0.4 +
  engagement_score * 0.3 +
  recency_score * 0.2 +
  followed_account_bonus * 0.1
)

where:
  - keyword_match_score: TF-IDF or semantic similarity to user interests
  - engagement_score: normalized (likes + comments + shares)
  - recency_score: 1.0 for <24h, decays over 7 days
  - followed_account_bonus: 1.0 if author in followed list, else 0.0
```

### 4. Content Delivery

**Supported Channels**:
- **Email**: HTML formatted digest using AWS SES
- **SMS**: Text summary via AWS SNS/Twilio
- **WhatsApp**: Formatted message via Twilio API
- **In-App**: Dashboard view (future)

**Digest Format**:
```
Subject: Your Social Daily Digest - May 30, 2026

---

🔗 LINKEDIN (3 items)
1. [Article Title] by @Author
   [2-line excerpt]
   Engagement: 💬 234 ❤️ 567
   Link: [https://...]

2. [Post Title]
   [excerpt]
   Engagement: 💬 45 ❤️ 123
   Link: [https://...]

3. [Content Title]
   [excerpt]
   Link: [https://...]

---

📺 YOUTUBE (3 items)
[Similar format with video thumbnails/links]

---

📸 INSTAGRAM (3 items)
[Similar format]

---

Want to customize? Visit: [dashboard URL]
Sent at: 9:00 AM EDT
Next digest: May 31, 2026
```

### 5. Historical Archive

**Box Folder Structure**:
```
/social-daily/
  /raw-data/
    /2026-05-30/
      /linkedin/
        trends.json (raw scraped data)
      /youtube/
        trends.json
      /instagram/
        trends.json
      /twitter/
        trends.json
  /digests/
    /2026-05-30/
      user-id-001-digest.html
      user-id-002-digest.html
      user-id-003-digest.html
    /2026-05-29/
      ...
```

**Retention Policy**:
- Raw data: 90 days
- Digests: 1 year
- Automatic cleanup via Lambda

---

## User Workflows

### Workflow 1: Initial Setup

```
1. User visits dashboard or receives signup link
2. Enters email, phone, timezone
3. For each platform (LinkedIn, YouTube, Instagram):
   a. Select "interested in" topics (min 1, max 10)
   b. Enter followed accounts/users (optional)
   c. Select content types (optional)
   d. Set engagement threshold (optional)
4. Choose delivery method(s) and time
5. System confirms setup, first digest sent next scheduled time
```

### Workflow 2: Daily Digest Reception

```
1. At scheduled delivery time, Lambda triggers
2. Agent loads user prefs + daily trends
3. Generates personalized digest (3 items/platform)
4. Sends via email/SMS/WhatsApp
5. Stores copy in Box archive
6. Logs delivery success/failure
```

### Workflow 3: Preference Updates

```
1. User logs into dashboard
2. Can modify interests, followed accounts, delivery settings
3. Changes effective for next digest (same day or next day depending on time)
4. Confirmation email sent
```

### Workflow 4: Feedback Loop (Future)

```
1. User clicks "interesting" or "not relevant" on digest items
2. Feedback stored in DynamoDB
3. ML model learns from preferences over time
4. Scoring algorithm refined per user
```

---

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    External Data Sources                         │
│  (LinkedIn, YouTube, Instagram, Twitter APIs/Web Scraping)       │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                  Apify Scraping Pipeline                         │
│  - 4 actors (1 per platform) triggered daily                    │
│  - Output: JSON trend data with metadata                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                  Box Storage (Raw Data)                          │
│  - /raw-data/YYYY-MM-DD/{platform}/trends.json                 │
│  - Organized by date and platform                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
    ┌────────────────────────┼────────────────────────┐
    │                        │                        │
┌───▼──────────┐  ┌──────────▼──────────┐  ┌────────▼────────┐
│  DynamoDB    │  │  AWS Lambda Agent   │  │  Preferences    │
│              │  │                      │  │  (DynamoDB/Box) │
│ - User Prefs │  │ - Load preferences  │  │                 │
│ - Delivery   │  │ - Fetch trends      │  │ - User settings │
│   History    │  │ - Score content     │  │ - Metadata      │
│              │  │ - Generate digest   │  │                 │
└──────────────┘  │ - Send via SNS/SES  │  └─────────────────┘
                  │ - Archive to Box    │
                  └──────────┬──────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐         ┌────▼────┐        ┌────▼──────┐
    │  AWS    │         │  AWS    │        │  Twilio   │
    │  SES    │         │  SNS    │        │  (SMS/WA) │
    │ (Email) │         │  (SMS)  │        │           │
    └────┬────┘         └────┬────┘        └────┬──────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │   User Inbox    │
                    │  (Email/SMS/WA) │
                    └─────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                 Box Storage (Digest Archive)                     │
│  - /digests/YYYY-MM-DD/{user-id}-digest.html                   │
└────────────────────────────────────────────────────────────────┘
```

### AWS Services Required

- **Lambda**: Digest generation and delivery agent
- **EventBridge**: Scheduled triggers for daily digest generation
- **DynamoDB**: User preferences and delivery history
- **SES**: Email delivery
- **SNS**: SMS delivery (or Twilio integration)
- **S3** (optional): Backup storage for digests
- **CloudWatch**: Logging and monitoring
- **IAM**: Access control

### Third-Party Services

- **Apify**: Web scraping platform for trend data
- **Box**: File storage and organization
- **Twilio**: SMS and WhatsApp delivery
- **AWS SES**: Email delivery (or SendGrid alternative)

---

## Data Models

### User Preferences Schema (DynamoDB)

```json
{
  "user_id": "user-123456",
  "email": "john@example.com",
  "phone": "+1234567890",
  "whatsapp": "+1234567890",
  "timezone": "America/New_York",
  "delivery_time": "09:00",
  "delivery_channels": ["email", "sms"],
  "created_at": "2026-05-01T10:00:00Z",
  "updated_at": "2026-05-30T15:30:00Z",
  "platforms": [
    {
      "name": "linkedin",
      "enabled": true,
      "interests": ["technology", "startup", "AI", "cloud computing"],
      "excluded_keywords": ["cryptocurrency", "real estate"],
      "followed_users": ["@satya_nadella", "@timcook", "@elonmusk"],
      "content_types": ["article", "post", "video"],
      "min_engagement": 100,
      "recency_preference": "trending_first"
    },
    {
      "name": "youtube",
      "enabled": true,
      "interests": ["technology", "programming", "startups"],
      "followed_channels": ["TechCrunch", "Stanford Online", "Google Developers"],
      "content_types": ["video"],
      "min_engagement": 50000,
      "recency_preference": "recent_first"
    },
    {
      "name": "instagram",
      "enabled": false,
      "interests": [],
      "followed_users": [],
      "content_types": []
    }
  ],
  "status": "active"
}
```

### Daily Trend Data Schema (Box JSON)

```json
{
  "platform": "linkedin",
  "date": "2026-05-30",
  "scraped_at": "2026-05-30T00:15:00Z",
  "trends": [
    {
      "id": "post-12345",
      "title": "The Future of AI in Enterprise",
      "author": "Jane Smith",
      "author_handle": "@janesmith",
      "excerpt": "New research shows AI adoption in enterprise has increased 300% in the past year...",
      "url": "https://linkedin.com/feed/update/urn:li:12345",
      "content_type": "article",
      "posted_at": "2026-05-30T08:30:00Z",
      "engagement": {
        "likes": 5230,
        "comments": 342,
        "shares": 156
      },
      "thumbnail_url": "https://...",
      "keywords": ["AI", "enterprise", "technology", "digital transformation"]
    },
    {
      "id": "post-12346",
      "title": "Building scalable microservices",
      "author": "Bob Johnson",
      "author_handle": "@bobjohnson",
      "excerpt": "Best practices for microservices architecture...",
      "url": "https://linkedin.com/feed/update/urn:li:12346",
      "content_type": "post",
      "posted_at": "2026-05-30T07:15:00Z",
      "engagement": {
        "likes": 1240,
        "comments": 89,
        "shares": 34
      },
      "keywords": ["microservices", "architecture", "backend", "engineering"]
    }
  ]
}
```

### Generated Digest Schema

```json
{
  "user_id": "user-123456",
  "digest_date": "2026-05-30",
  "generated_at": "2026-05-30T09:00:00Z",
  "delivery_channels": ["email", "sms"],
  "digest": {
    "platforms": [
      {
        "name": "linkedin",
        "platform_emoji": "🔗",
        "items": [
          {
            "rank": 1,
            "title": "The Future of AI in Enterprise",
            "author": "@janesmith",
            "excerpt": "New research shows AI adoption...",
            "url": "https://linkedin.com/feed/update/...",
            "engagement": "💬 342 ❤️ 5230",
            "score": 0.89,
            "matching_interests": ["AI", "technology"]
          },
          {
            "rank": 2,
            "title": "Building Scalable Microservices",
            "author": "@bobjohnson",
            "excerpt": "Best practices for microservices...",
            "url": "https://linkedin.com/feed/update/...",
            "engagement": "💬 89 ❤️ 1240",
            "score": 0.76,
            "matching_interests": ["technology"]
          },
          {
            "rank": 3,
            "title": "Cloud Computing Trends 2026",
            "author": "@techleader",
            "excerpt": "Analysis of emerging trends...",
            "url": "https://linkedin.com/...",
            "engagement": "💬 45 ❤️ 892",
            "score": 0.68,
            "matching_interests": ["cloud computing", "technology"]
          }
        ]
      },
      {
        "name": "youtube",
        "platform_emoji": "📺",
        "items": [
          {
            "rank": 1,
            "title": "Latest Python 3.14 Features",
            "channel": "TechCrunch",
            "excerpt": "Overview of new features...",
            "url": "https://youtube.com/watch?v=...",
            "engagement": "👁️ 245K 👍 12K",
            "video_length": "14:32",
            "score": 0.85
          },
          {
            "rank": 2,
            "title": "AWS Lambda Performance Tips",
            "channel": "Google Developers",
            "excerpt": "How to optimize your functions...",
            "url": "https://youtube.com/watch?v=...",
            "engagement": "👁️ 98K 👍 5K",
            "video_length": "22:15",
            "score": 0.72
          },
          {
            "rank": 3,
            "title": "Building Distributed Systems",
            "channel": "Stanford Online",
            "excerpt": "Engineering fundamentals...",
            "url": "https://youtube.com/watch?v=...",
            "engagement": "👁️ 156K 👍 8.2K",
            "video_length": "45:20",
            "score": 0.68
          }
        ]
      }
    ]
  },
  "delivery_status": {
    "email": "sent",
    "sms": "sent"
  }
}
```

---

## API Specifications

### 1. User Preference Management API

#### GET /api/users/{user_id}/preferences
Retrieve user preferences

```
Response (200):
{
  "user_id": "user-123456",
  "email": "john@example.com",
  "timezone": "America/New_York",
  "delivery_time": "09:00",
  "platforms": [...]
}
```

#### POST /api/users
Create new user

```
Request:
{
  "email": "john@example.com",
  "phone": "+1234567890",
  "timezone": "America/New_York",
  "delivery_time": "09:00",
  "delivery_channels": ["email", "sms"]
}

Response (201):
{
  "user_id": "user-123456",
  "status": "created"
}
```

#### PUT /api/users/{user_id}/preferences
Update user preferences

```
Request:
{
  "platforms": [
    {
      "name": "linkedin",
      "enabled": true,
      "interests": ["AI", "startups", "technology"],
      ...
    }
  ]
}

Response (200):
{
  "user_id": "user-123456",
  "updated_at": "2026-05-30T15:30:00Z",
  "status": "updated"
}
```

### 2. Digest Management API

#### GET /api/digests/{user_id}/{date}
Retrieve digest for specific date

```
Response (200):
{
  "user_id": "user-123456",
  "digest_date": "2026-05-30",
  "platforms": [...]
}
```

#### GET /api/digests/{user_id}
List all digests for user (paginated)

```
Response (200):
{
  "user_id": "user-123456",
  "digests": [
    {
      "date": "2026-05-30",
      "delivery_status": "sent",
      "url": "/api/digests/user-123456/2026-05-30"
    },
    ...
  ],
  "pagination": {
    "total": 45,
    "limit": 10,
    "offset": 0
  }
}
```

### 3. Manual Digest Trigger API

#### POST /api/digests/{user_id}/generate
Manually trigger digest generation (for testing)

```
Response (202):
{
  "user_id": "user-123456",
  "status": "processing",
  "job_id": "job-456789"
}
```

### 4. Admin API

#### GET /api/admin/health
System health check

```
Response (200):
{
  "status": "healthy",
  "box_connected": true,
  "dynamodb_connected": true,
  "apify_connected": true,
  "last_scrape": "2026-05-30T00:15:00Z"
}
```

#### GET /api/admin/daily-trends/{date}/{platform}
Retrieve raw trend data

```
Response (200):
{
  "platform": "linkedin",
  "date": "2026-05-30",
  "item_count": 247,
  "trends": [...]
}
```

---

## Notification Delivery

### Email Delivery

**Provider**: AWS SES or SendGrid  
**Format**: HTML with CSS inline styling  
**Template**: See Digest Format in Core Features section

**Configuration**:
```
AWS_SES_REGION: us-east-1
FROM_EMAIL: noreply@socialdaily.com
REPLY_TO: support@socialdaily.com
UNSUBSCRIBE_HEADER: List-Unsubscribe header included
```

### SMS Delivery

**Provider**: AWS SNS + Twilio  
**Format**: Plain text summary (≤160 chars per message)  
**Example**:
```
Social Daily: 3 LinkedIn posts, 3 YouTube videos, 3 Instagram posts curated for you. View digest: https://digest.socialdaily.com/user-123456/2026-05-30
```

### WhatsApp Delivery

**Provider**: Twilio WhatsApp API  
**Format**: Rich text messages with emojis and links  
**Features**:
- Platform breakdown with item count
- Clickable links to content
- Quick reply buttons for feedback (future)

### Delivery Retry Logic

```
1st attempt: Scheduled time
If failed: 2 retries with exponential backoff
  - 1st retry: +5 minutes
  - 2nd retry: +15 minutes
Log all failures to CloudWatch for monitoring
Alert admin if user has 3 consecutive delivery failures
```

---

## Storage & Organization

### Box Folder Structure

```
/social-daily-root/
├── /raw-data/
│   ├── /2026-05-30/
│   │   ├── /linkedin/
│   │   │   └── trends.json
│   │   ├── /youtube/
│   │   │   └── trends.json
│   │   ├── /instagram/
│   │   │   └── trends.json
│   │   └── /twitter/
│   │       └── trends.json
│   ├── /2026-05-29/
│   │   └── ...
│   └── ...
├── /digests/
│   ├── /2026-05-30/
│   │   ├── user-123456-digest.html
│   │   ├── user-123456-digest.json
│   │   ├── user-789012-digest.html
│   │   └── user-789012-digest.json
│   ├── /2026-05-29/
│   │   └── ...
│   └── ...
├── /config/
│   └── apify-actors.json (metadata about scraping actors)
└── /logs/
    └── /2026-05-30/
        ├── delivery-log.json
        ├── errors.log
        └── generation-log.json
```

### DynamoDB Tables

**Table 1: Users**
- PK: `user_id`
- SK: None (global secondary index on email)
- TTL: None (permanent)

**Table 2: UserPreferences**
- PK: `user_id`
- SK: None
- TTL: None

**Table 3: DeliveryHistory**
- PK: `user_id`
- SK: `digest_date` (sort by date, latest first)
- TTL: 365 days (automatic cleanup)

**Table 4: Feedback** (Future)
- PK: `user_id`
- SK: `digest_date#item_id`
- Stores user feedback on digest items
- TTL: None

### Data Retention Policy

- **Raw trend data**: 90 days (cleanup via Lambda)
- **Digest artifacts**: 1 year (cleanup via Lambda)
- **Delivery logs**: 30 days (CloudWatch retention)
- **User preferences**: Indefinite (until account deletion)
- **DynamoDB TTL**: Configured on DeliveryHistory table

---

## Deployment & Operations

### Prerequisites

- AWS Account with appropriate IAM permissions
- Apify account with actors configured
- Box Enterprise account with API access
- Twilio account for SMS/WhatsApp
- AWS SES verified email

### Environment Variables

```
# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=***
AWS_SECRET_ACCESS_KEY=***

# Database
DYNAMODB_USERS_TABLE=social-daily-users
DYNAMODB_PREFERENCES_TABLE=social-daily-preferences
DYNAMODB_DELIVERY_HISTORY_TABLE=social-daily-delivery-history

# Box
BOX_CLIENT_ID=***
BOX_CLIENT_SECRET=***
BOX_ROOT_FOLDER_ID=***

# Apify
APIFY_API_TOKEN=***

# Email (SES)
AWS_SES_REGION=us-east-1
FROM_EMAIL=noreply@socialdaily.com

# SMS/WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=***
TWILIO_AUTH_TOKEN=***
TWILIO_WHATSAPP_NUMBER=***

# Application
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Deployment Steps

1. **Infrastructure Setup** (via Terraform/CloudFormation)
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

2. **Lambda Functions** (via Serverless Framework or AWS CLI)
   ```bash
   serverless deploy
   # OR
   aws lambda create-function --function-name social-daily-digest ...
   ```

3. **EventBridge Rules**
   ```bash
   # Create rule for daily trigger at 9 AM UTC
   aws events put-rule --name social-daily-daily-trigger \
     --schedule-expression "cron(0 9 * * ? *)"
   ```

4. **DynamoDB Tables**
   ```bash
   aws dynamodb create-table --table-name social-daily-users \
     --attribute-definitions ... --key-schema ...
   ```

5. **Box Folder Structure**
   ```bash
   # Manual setup via Box UI or API
   # Create folder structure as defined above
   ```

### Monitoring & Alerting

**CloudWatch Metrics**:
- Lambda execution time (target: <30s)
- Digest generation success rate (target: >99%)
- Delivery success rate per channel (target: >99%)
- Failed deliveries (alert if >1% per day)

**CloudWatch Alarms**:
- Lambda errors > 5 in 1 hour
- Delivery failures > 10 per day
- Apify scrape failures
- Box API errors

**Logging**:
- All Lambda executions logged
- All delivery attempts logged
- Error traces stored in CloudWatch Logs
- Retention: 30 days standard, 7 days for archived logs

### Scaling Considerations

- **Lambda**: No concurrency limits needed (sequential per user)
- **DynamoDB**: On-demand billing recommended for flexibility
- **Box API**: 100 API calls/min per token, implement exponential backoff
- **SES**: Request production access if >10K emails/day
- **Twilio**: Standard rate limits apply

---

## Success Metrics

### User Engagement
- Daily digest open rate (target: >40%)
- Click-through rate (target: >15%)
- User retention (30-day: >70%)
- Weekly active users

### System Performance
- Digest generation time (target: <30s per user)
- Delivery latency (target: <5min from scheduled time)
- Uptime (target: 99.9%)
- Delivery success rate (target: >99%)

### Content Quality
- User satisfaction score (feedback, 1-5 scale, target: >4.0)
- Irrelevant item rate (user feedback, target: <5%)
- Engagement with curated items vs. platform average

### Business Metrics
- Cost per active user (target: <$0.10/day)
- User acquisition cost
- Churn rate (target: <5% monthly)
- Net Promoter Score (NPS, target: >50)

---

## Future Enhancements

### Phase 2
- Dashboard for preference management
- User feedback loop for ML model improvement
- More social platforms (Reddit, TikTok, Substack, Medium)
- Digest personalization via ML
- In-app digest view with social sharing

### Phase 3
- Mobile app for digest consumption
- Real-time notifications for trending content
- Community/team digests
- Integration with Slack, Teams
- Custom digest scheduling (bi-weekly, weekly, etc.)

### Phase 4
- AI-powered content summarization
- Multi-language support
- Advanced filtering (by sentiment, author influence, etc.)
- Digest A/B testing for optimization

---

## Technical Implementation Notes

### Key Decisions

1. **Serverless Architecture**: Reduces operational overhead, scales automatically
2. **AWS Lambda + EventBridge**: Cost-effective for scheduled, time-bound jobs
3. **Apify for Scraping**: Managed scraping reduces maintenance burden
4. **Box for Storage**: Existing enterprise relationship, good for compliance
5. **Multiple Notification Channels**: Meets diverse user preferences
6. **DynamoDB**: Sufficient for metadata, scales automatically
7. **Strict Item Limit (3/platform)**: Forces discipline, prevents feature creep

### Potential Challenges

1. **Social Media API Changes**: Web scraping more robust than APIs, but requires maintenance
2. **Scraping Detection**: Implement rotation, backoff, user-agent variation
3. **Content Freshness**: Daily schedule may miss real-time trends; consider weekly synthesis
4. **Scoring Accuracy**: Initial algorithm may be imperfect; plan for feedback loop
5. **Delivery Reliability**: Implement robust retry logic and monitoring
6. **Cost Management**: Monitor Box API usage, SES/SNS costs

### Testing Strategy

- Unit tests for scoring algorithm
- Integration tests for Box API interactions
- End-to-end tests with test user accounts
- Load testing for concurrent digest generation
- Delivery channel testing (email, SMS, WhatsApp)

---

## Questions for Development Team

1. Should we support ranked lists per platform, or just show all 3 equally?
2. How should we handle duplicate content across platforms?
3. What should be the preferred retry strategy for failed deliveries?
4. Should users be able to customize the HTML template of their digest?
5. How do we handle content that violates platform ToS or is malicious?
6. Should we implement user feedback immediately or batch it?
7. What's the target cost per user per month?

---

**Document Version**: 1.0  
**Last Updated**: May 30, 2026  
**Status**: Ready for Development
