#!/usr/bin/env python3
"""
Social Daily Content Curator
Generates personalized daily digests from social media trends
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from src.box_client import LocalBoxSimulator
from src.scorer import ContentScorer


class SocialDailyCurator:
    """Main curator engine"""
    
    def __init__(self, user_prefs_path: str = 'config/user_preferences.json'):
        """Initialize curator with user preferences"""
        self.user_prefs = self._load_preferences(user_prefs_path)
        self.box = LocalBoxSimulator()
        self.digest_data = {
            'user_id': self.user_prefs['user']['user_id'],
            'digest_date': datetime.now().strftime('%Y-%m-%d'),
            'generated_at': datetime.now().isoformat(),
            'delivery_channels': self.user_prefs['user'].get('delivery_channels', []),
            'platforms': {}
        }
    
    def _load_preferences(self, path: str) -> dict:
        """Load user preferences from JSON file"""
        with open(path) as f:
            return json.load(f)
    
    def curate_daily_digest(self) -> dict:
        """
        Main curation workflow:
        1. Load trends for each enabled platform
        2. Score and rank content
        3. Select top 3 per platform
        4. Generate digest structure
        """
        print("\n" + "="*60)
        print("🎯 SOCIAL DAILY - CONTENT CURATION ENGINE")
        print("="*60)
        
        user_name = self.user_prefs['user']['name']
        print(f"\n👤 User: {user_name}")
        print(f"📅 Date: {self.digest_data['digest_date']}")
        print(f"\n{'Platform':<15} {'Items':<10} {'Selected':<10}")
        print("-"*35)
        
        for platform, config in self.user_prefs['platforms'].items():
            if not config.get('enabled', False):
                print(f"{platform:<15} {'DISABLED':<10} {'—':<10}")
                continue
            
            # Load trends from Box (or sample data)
            trends = self.box.load_trends(platform)
            total_items = len(trends.get('items', []))
            
            # Score and select top 3
            scorer = ContentScorer(config)
            top_items = scorer.get_top_n(
                trends.get('items', []),
                n=3
            )
            
            # Store in digest
            self.digest_data['platforms'][platform] = {
                'name': platform.upper(),
                'emoji': self._get_platform_emoji(platform),
                'total_items_processed': total_items,
                'items_selected': len(top_items),
                'items': top_items
            }
            
            print(f"{platform:<15} {total_items:<10} {len(top_items):<10}")
        
        print("\n✓ Curation complete!")
        return self.digest_data
    
    def _get_platform_emoji(self, platform: str) -> str:
        """Get emoji for platform"""
        emojis = {
            'linkedin': '🔗',
            'youtube': '📺',
            'instagram': '📸',
            'twitter': '𝕏',
            'tiktok': '🎵'
        }
        return emojis.get(platform, '📱')
    
    def save_digest(self) -> bool:
        """Save digest to local storage (simulates Box)"""
        date = self.digest_data['digest_date']
        user_id = self.digest_data['user_id']
        return self.box.save_digest(user_id, date, self.digest_data)
    
    def generate_html_digest(self) -> str:
        """
        Generate HTML version of digest
        """
        from jinja2 import Template
        
        # Load template
        template_path = Path('templates/digest_template.html')
        with open(template_path) as f:
            template_html = f.read()
        
        template = Template(template_html)
        
        # Render with digest data
        html = template.render(
            user_name=self.user_prefs['user']['name'],
            digest_date=self.digest_data['digest_date'],
            platforms=self.digest_data['platforms'],
            user_email=self.user_prefs['user']['email']
        )
        
        return html
    
    def save_html_digest(self, html: str) -> bool:
        """Save HTML digest to file"""
        date = self.digest_data['digest_date']
        user_id = self.digest_data['user_id']
        
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        filename = f"{date}_{user_id}_digest.html"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(html)
        
        print(f"  ✓ HTML digest saved to {filepath}")
        return True
    
    def print_digest_summary(self):
        """Print a text summary of the digest"""
        print("\n" + "="*60)
        print("📬 DAILY DIGEST SUMMARY")
        print("="*60)
        
        for platform, data in self.digest_data['platforms'].items():
            print(f"\n{data['emoji']} {platform.upper()}")
            print("-" * 40)
            
            for idx, item in enumerate(data['items'], 1):
                score = item.get('_score', 0)
                interests = item.get('_matched_interests', [])
                
                print(f"\n  {idx}. {item.get('title', 'Untitled')}")
                print(f"     Author: @{item.get('author_handle', 'unknown')}")
                print(f"     Score: {score:.0%} | Interests: {', '.join(interests)}")
                
                engagement = item.get('engagement', {})
                if isinstance(engagement, dict):
                    likes = engagement.get('likes', 0)
                    comments = engagement.get('comments', 0)
                    print(f"     Engagement: ❤️  {likes} | 💬 {comments}")
                
                url = item.get('url', '#')
                print(f"     Link: {url}")


def main():
    """Main entry point"""
    try:
        # Initialize curator
        curator = SocialDailyCurator()
        
        # Generate digest
        curator.curate_daily_digest()
        
        # Save JSON digest
        curator.save_digest()
        
        # Generate and save HTML
        html = curator.generate_html_digest()
        curator.save_html_digest(html)
        
        # Print summary
        curator.print_digest_summary()
        
        print("\n✅ Daily digest generation complete!")
        print("\nNext steps:")
        print("  1. Check output/ folder for generated digests")
        print("  2. Review HTML in browser for email preview")
        print("  3. Configure Apify actors for real trend data")
        print("  4. Set up Box integration for daily storage")
        print("  5. Deploy to AWS Lambda for production")
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
