
Social Daily 📱❌🔄
The Anti-Doomscroll Media Curator

Social Daily is a personalized media curation engine built to solve the modern crisis of digital fatigue, algorithmic addiction, and endless doomscrolling.

Instead of letting engagement-maximized networks dictate your attention span, Social Daily flips the paradigm. It coordinates targeted platform scrapers to extract high-value content completely in memory, enforcing a strict, non-negotiable budget of exactly 3 high-signal items per platform per day. The system packages this curated selection into a beautifully formatted daily PDF digest and archives it, alongside the filtered raw data payloads, securely inside Box.

🚀 The Core Philosophy
* Finite over Infinite: No infinite scroll mechanics. A hard ceiling of exactly 3 items per platform ensures you stay informed without falling down the rabbit hole.
* Intentional over Algorithmic: You define what matters—specific creators, target topics, or themes—not a third-party retention metric.
* Deterministic Reliability: Built entirely on predictable software mechanics. By utilizing targeted scraping boundaries at the ingestion layer, the pipeline handles input parsing, content mapping, PDF generation, and storage with zero non-deterministic overhead or API token dependencies.
🛠️ System Architecture & Data Flow
Social Daily uses an efficient, decoupled pipeline design that executes major transformations completely in memory before using Box as a centralized system bus. This ensures lightning-fast execution, removes disk-space cleanup overhead, and keeps the application footprint ready to scale to cloud ecosystems (like AWS or Azure) down the road.
┌────────────────────────────────────────────────────────┐
│ 1. Targeted In-Memory Scraping (Apify)                 │
│    Scrapers extract *exactly* the top 3 items per app │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 2. Automated Box Synchronization                       │
│    In the root folder, adds new files per day with date     │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼                                  
┌──────────────────────---------------------------------──┐      
│      Compiles clean layout    │  completely in memory  
└──────────────┬──────---------------------------------───┘       
                                                   │
                                                   ▼
┌────────────────────────────────────────────────────────┐
│ 4. Permanent Cloud Commit                              │
│    Uploads JSON backups & Daily digest pdf to Box      │
└────────────────────────────────────────────────────────┘
📁 Repository Structure
.
├── scrapers/
│   └── multi_platform_scraper.py          # Main execution file (Scraper Orchestrator + PDF Engine + Box I/O)
├── config/
│   └── user_preferences.json  # Blueprint schema for tracking target user interests
└── README.md               # This file

⚙️ Operational Setup

# Clone the repository
git clone https://github.com/maphad/social_daily.git
cd social_daily

# Initialize local environment targets
Edit the python script to add your active APIFY_API_TOKEN and BOX_DEVELOPER_TOKEN

# Install python, apify

#Run it
python scrapers/instagram_scraper_pdf_generator.py

📬 Final Output Artifacts
* Social_Daily_Digest_{MMDDYY}.pdf: A clean, minimal, publication-grade document built dynamically by the Python engine. It presents titles, summaries, and direct links without any visual clutter, ad banners, or algorithmic trapdoors. Read it, close it, and move on with your day.

🏆 Team
Developed during the Cascadia AI Hackathon to reclaim user focus through intentional software engineering.
Cathy Chian, Madhura Phadnis, Soundarya Burton

📜 License
This project is open-source under the MIT License. Defeat the algorithm, protect your time.