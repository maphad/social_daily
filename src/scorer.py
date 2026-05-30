import json
from typing import Dict, List, Tuple
from datetime import datetime

class ContentScorer:
    """Scores and ranks content items based on user preferences"""
    
    def __init__(self, platform_prefs: dict):
        """
        Initialize scorer with platform preferences
        Args:
            platform_prefs: User preferences for this platform from config
        """
        self.interests = platform_prefs.get('interests', [])
        self.excluded_keywords = platform_prefs.get('excluded_keywords', [])
        self.followed_users = platform_prefs.get('followed_users', [])
        self.min_engagement = platform_prefs.get('min_engagement', 0)
        self.recency_preference = platform_prefs.get('recency_preference', 'trending_first')
    
    def score_item(self, item: dict) -> float:
        """
        Calculate relevance score for an item
        
        Scoring formula:
        - Keyword match (40%): TF-IDF style matching against interests
        - Engagement (30%): Normalized engagement metrics
        - Recency (20%): Time decay based on post age
        - Followed account bonus (10%): Author in followed list
        
        Args:
            item: Content item with title, author, keywords, engagement, posted_at
        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0
        
        # 1. Exclusion filter - reject if contains excluded keywords
        item_text = (item.get('title', '') + ' ' + item.get('excerpt', '')).lower()
        for excluded in self.excluded_keywords:
            if excluded.lower() in item_text:
                return 0.0  # Hard reject
        
        # 2. Keyword match score (40%)
        keyword_match = self._calculate_keyword_match(item)
        score += keyword_match * 0.40
        
        # 3. Engagement score (30%) - normalized to 0-1
        engagement_score = self._calculate_engagement_score(item)
        score += engagement_score * 0.30
        
        # 4. Recency score (20%) - time decay
        recency_score = self._calculate_recency_score(item)
        score += recency_score * 0.20
        
        # 5. Followed account bonus (10%)
        followed_bonus = 1.0 if item.get('author_handle') in self.followed_users else 0.0
        score += followed_bonus * 0.10
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_keyword_match(self, item: dict) -> float:
        """
        Calculate keyword match score
        Returns score 0-1 based on how many interests match
        """
        if not self.interests:
            return 0.5  # Neutral if no interests specified
        
        item_keywords = item.get('keywords', [])
        if not item_keywords:
            return 0.0
        
        # Convert to lowercase for comparison
        interests_lower = [i.lower() for i in self.interests]
        item_keywords_lower = [k.lower() for k in item_keywords]
        
        matches = sum(1 for keyword in item_keywords_lower 
                     if any(interest in keyword or keyword in interest 
                           for interest in interests_lower))
        
        match_ratio = matches / max(len(self.interests), 1)
        return min(match_ratio, 1.0)
    
    def _calculate_engagement_score(self, item: dict) -> float:
        """
        Calculate normalized engagement score
        Returns score 0-1 based on engagement metrics
        """
        engagement = item.get('engagement', {})
        
        # Different platforms have different metrics
        if isinstance(engagement, dict):
            likes = engagement.get('likes', 0)
            comments = engagement.get('comments', 0)
            shares = engagement.get('shares', 0)
            views = engagement.get('views', 0)
            
            # Weighted combination
            total_engagement = (likes * 1) + (comments * 3) + (shares * 5) + (views * 0.01)
        else:
            total_engagement = engagement if isinstance(engagement, (int, float)) else 0
        
        # Check minimum threshold
        if total_engagement < self.min_engagement:
            return 0.0
        
        # Normalize using logarithmic scale (accounts for wide range)
        # Log scale prevents one viral post from dominating
        import math
        normalized = math.log(total_engagement + 1) / math.log(10000)  # Assume 10k is "high"
        return min(normalized, 1.0)
    
    def _calculate_recency_score(self, item: dict) -> float:
        """
        Calculate recency score with time decay
        Posts from today get 1.0, decays to 0.0 over 7 days
        """
        posted_at = item.get('posted_at')
        if not posted_at:
            return 0.5  # Neutral if no timestamp
        
        try:
            # Parse ISO timestamp
            from datetime import datetime
            if isinstance(posted_at, str):
                post_time = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
            else:
                post_time = posted_at
            
            now = datetime.now(post_time.tzinfo) if post_time.tzinfo else datetime.now()
            age_days = (now - post_time).days
            
            # Linear decay: 1.0 at day 0, 0.0 at day 7
            recency = max(0.0, 1.0 - (age_days / 7.0))
            return recency
        except:
            return 0.5
    
    def rank_items(self, items: List[dict]) -> List[Tuple[dict, float]]:
        """
        Score and rank all items
        Returns list of (item, score) tuples sorted by score descending
        """
        scored_items = []
        for item in items:
            score = self.score_item(item)
            scored_items.append((item, score))
        
        # Sort by score, then by recency as tiebreaker
        return sorted(scored_items, 
                     key=lambda x: (-x[1], x[0].get('posted_at', '')),
                     reverse=False)
    
    def get_top_n(self, items: List[dict], n: int = 3) -> List[dict]:
        """
        Get top N items by score
        Returns list of top items with scores attached
        """
        ranked = self.rank_items(items)
        top_items = []
        
        for item, score in ranked[:n]:
            item_copy = item.copy()
            item_copy['_score'] = round(score, 2)
            item_copy['_matched_interests'] = self._get_matched_interests(item)
            top_items.append(item_copy)
        
        return top_items
    
    def _get_matched_interests(self, item: dict) -> List[str]:
        """Get list of user interests that matched this item"""
        item_keywords = [k.lower() for k in item.get('keywords', [])]
        interests_lower = [i.lower() for i in self.interests]
        
        matched = [interest for interest in self.interests
                  if any(interest.lower() in keyword or keyword in interest.lower()
                        for keyword in item_keywords)]
        return matched
