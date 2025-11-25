#!/usr/bin/env python3
"""
Reddit Scraper - Extract trending/popular posts with content, upvotes, and downvotes
This scraper dynamically discovers the top 20 trending subreddits on any given day
and fetches posts from those communities. Filters out NSFW content to ensure 
family-friendly/PG results only.
"""

import requests
import json
import time
import csv
from datetime import datetime
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedditScraper:
    """Reddit scraper using the public JSON API (no authentication required)"""
    
    def __init__(self):
        self.base_url = "https://www.reddit.com"
        self.headers = {
            'User-Agent': 'RedditScraper/1.0 (Educational Purpose)'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_subreddit_posts(self, subreddit: str, sort_by: str = "hot", limit: int = 25) -> List[Dict]:
        """
        Get posts from a specific subreddit
        
        Args:
            subreddit: Subreddit name (without r/)
            sort_by: Sort method (hot, new, top, rising)
            limit: Number of posts to fetch (max 100)
        
        Returns:
            List of post dictionaries
        """
        url = f"{self.base_url}/r/{subreddit}/{sort_by}.json"
        params = {'limit': limit}
        
        try:
            logger.info(f"Fetching posts from r/{subreddit} sorted by {sort_by}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            for item in data['data']['children']:
                post = item['data']
                
                # Skip NSFW content
                if post.get('over_18', False):
                    continue
                
                # Skip stickied posts (often rules, announcements, etc.)
                if post.get('stickied', False):
                    continue
                
                # Skip rules posts based on title patterns
                if self._is_rules_post(post):
                    continue
                
                # Skip video or photo-only posts
                if self._is_media_only_post(post):
                    continue
                
                # Extract relevant information
                post_info = {
                    'id': post.get('id'),
                    'title': post.get('title'),
                    'subreddit': post.get('subreddit'),
                    'selftext': post.get('selftext', ''),
                    'permalink': f"https://www.reddit.com{post.get('permalink')}",
                    'upvotes': post.get('ups', 0),
                    'downvotes': post.get('downs', 0),
                    'score': post.get('score', 0),
                    'upvote_ratio': post.get('upvote_ratio', 0),
                    'num_comments': post.get('num_comments', 0),
                    'created_datetime': datetime.fromtimestamp(post.get('created_utc', 0)).isoformat(),
                    'flair_text': post.get('link_flair_text', ''),
                }
                posts.append(post_info)
            
            logger.info(f"Successfully fetched {len(posts)} posts from r/{subreddit}")
            return posts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching posts from r/{subreddit}: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response from r/{subreddit}: {e}")
            return []
    
    def get_popular_posts(self, sort_by: str = "hot", limit: int = 25) -> List[Dict]:
        """
        Get posts from r/popular
        
        Args:
            sort_by: Sort method (hot, new, top, rising)
            limit: Number of posts to fetch
        
        Returns:
            List of post dictionaries
        """
        url = f"{self.base_url}/r/popular/{sort_by}.json"
        params = {'limit': limit}
        
        try:
            logger.info(f"Fetching popular posts sorted by {sort_by}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            for item in data['data']['children']:
                post = item['data']
                
                # Skip NSFW content
                if post.get('over_18', False):
                    continue
                
                # Skip stickied posts (often rules, announcements, etc.)
                if post.get('stickied', False):
                    continue
                
                # Skip rules posts based on title patterns
                if self._is_rules_post(post):
                    continue
                
                # Skip video or photo-only posts
                if self._is_media_only_post(post):
                    continue
                
                post_info = {
                    'id': post.get('id'),
                    'title': post.get('title'),
                    'subreddit': post.get('subreddit'),
                    'selftext': post.get('selftext', ''),
                    'permalink': f"https://www.reddit.com{post.get('permalink')}",
                    'upvotes': post.get('ups', 0),
                    'downvotes': post.get('downs', 0),
                    'score': post.get('score', 0),
                    'upvote_ratio': post.get('upvote_ratio', 0),
                    'num_comments': post.get('num_comments', 0),
                    'created_datetime': datetime.fromtimestamp(post.get('created_utc', 0)).isoformat(),
                    'flair_text': post.get('link_flair_text', ''),
                }
                posts.append(post_info)
            
            logger.info(f"Successfully fetched {len(posts)} popular posts")
            return posts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching popular posts: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response for popular posts: {e}")
            return []
    
    def get_dynamic_trending_subreddits(self, limit: int = 20) -> List[str]:
        """
        Dynamically discover trending subreddits by analyzing r/popular posts
        
        Args:
            limit: Maximum number of trending subreddits to return
        
        Returns:
            List of trending subreddit names (PG-filtered)
        """
        try:
            logger.info("Discovering trending subreddits from popular posts...")
            
            # Fetch a large number of popular posts to analyze subreddit distribution
            url = f"{self.base_url}/r/popular/hot.json"
            params = {'limit': 100}  # Get more posts for better analysis
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Count subreddit occurrences
            subreddit_counts = {}
            
            for item in data['data']['children']:
                post = item['data']
                
                # Skip NSFW content
                if post.get('over_18', False):
                    continue
                    
                subreddit = post.get('subreddit')
                if subreddit:
                    # Filter out known problematic subreddits even if not marked NSFW
                    if self._is_family_friendly_subreddit(subreddit):
                        subreddit_counts[subreddit] = subreddit_counts.get(subreddit, 0) + 1
            
            # Sort by popularity and return top subreddits
            trending_subreddits = sorted(
                subreddit_counts.keys(), 
                key=lambda x: subreddit_counts[x], 
                reverse=True
            )[:limit]
            
            logger.info(f"Discovered {len(trending_subreddits)} trending subreddits: {trending_subreddits[:10]}")
            
            # If we don't have enough, supplement with static list
            if len(trending_subreddits) < 10:
                logger.info("Supplementing with static subreddit list...")
                static_subreddits = self.get_static_subreddits()
                for subreddit in static_subreddits:
                    if subreddit not in trending_subreddits:
                        trending_subreddits.append(subreddit)
                        if len(trending_subreddits) >= limit:
                            break
            
            return trending_subreddits
            
        except Exception as e:
            logger.error(f"Error discovering trending subreddits: {e}")
            logger.info("Falling back to static subreddit list...")
            return self.get_static_subreddits()[:limit]
    
    def _is_family_friendly_subreddit(self, subreddit: str) -> bool:
        """
        Check if a subreddit is family-friendly based on name patterns
        
        Args:
            subreddit: Subreddit name to check
            
        Returns:
            True if subreddit appears to be family-friendly
        """
        # Convert to lowercase for checking
        sub_lower = subreddit.lower()
        
        # Known problematic keywords/patterns to avoid
        nsfw_keywords = [
            'nsfw', 'porn', 'sex', 'nude', 'naked', 'xxx', 'gonewild', 
            'boobs', 'ass', 'dick', 'cock', 'pussy', 'fetish', 'bdsm',
            'lesbian', 'gay', 'anal', 'milf', 'teen', 'amateur',
            'cumshot', 'blowjob', 'threesome', 'orgy', 'strip',
            'onlyfans', 'camgirl', 'escort', 'hookup', 'tinder',
            'slutty', 'kinky', 'dirty', 'erotic', 'adult'
        ]
        
        # Check for problematic keywords
        for keyword in nsfw_keywords:
            if keyword in sub_lower:
                return False
        
        # Additional patterns that might indicate NSFW content
        if sub_lower.endswith('porn') or sub_lower.endswith('nsfw'):
            return False
            
        if 'r4r' in sub_lower or 'hookup' in sub_lower:
            return False
        
        return True
    
    def _is_rules_post(self, post: Dict) -> bool:
        """
        Check if a post is likely a rules/announcement post based on title and content
        
        Args:
            post: Reddit post data dictionary
            
        Returns:
            True if post appears to be a rules/announcement post
        """
        title = post.get('title', '').lower()
        selftext = post.get('selftext', '').lower()
        flair = post.get('flair_text', '').lower()
        author = post.get('author', '').lower()
        
        # Common rules/announcement keywords in titles
        rules_keywords = [
            'rules', 'rule', 'subreddit rules', 'community rules',
            'guidelines', 'guideline', 'posting guidelines',
            'announcement', 'mod post', 'moderator post',
            'sticky', 'pinned', 'important', 'notice',
            'welcome', 'read this first', 'before posting',
            'new users', 'getting started', 'how to post',
            'community guidelines', 'posting rules',
            'submission guidelines', 'content policy',
            'meta', 'modmail', 'banned', 'warning'
        ]
        
        # Check title for rules keywords
        for keyword in rules_keywords:
            if keyword in title:
                return True
        
        # Check if posted by moderators/bots
        if 'automod' in author or 'bot' in author or author.startswith('mod'):
            return True
        
        # Check flair for rules/announcement indicators
        flair_keywords = ['rule', 'announcement', 'mod', 'sticky', 'pinned', 'meta']
        for keyword in flair_keywords:
            if keyword in flair:
                return True
        
        # Check if it's a long text post that might be rules
        if len(selftext) > 500 and any(word in selftext for word in ['rule', 'guideline', 'moderator', 'violation']):
            return True
        
        return False
    
    def _is_media_only_post(self, post: Dict) -> bool:
        """
        Check if a post is video or photo-only with minimal text content
        
        Args:
            post: Reddit post data dictionary
            
        Returns:
            True if post appears to be media-only without meaningful text discussion
        """
        title = post.get('title', '').strip()
        selftext = post.get('selftext', '').strip()
        url = post.get('url', '')
        domain = post.get('domain', '').lower()
        is_video = post.get('is_video', False)
        is_self = post.get('is_self', False)
        
        # Skip direct video posts
        if is_video:
            return True
        
        # Skip posts that are just links to images/videos with no text content
        if not is_self and not selftext:
            # Common image/video hosting domains
            media_domains = [
                'i.redd.it', 'v.redd.it', 'reddit.com/gallery',
                'imgur.com', 'i.imgur.com', 'gfycat.com', 
                'youtube.com', 'youtu.be', 'twitch.tv',
                'instagram.com', 'tiktok.com', 'twitter.com',
                'streamable.com', 'giphy.com', 'tenor.com'
            ]
            
            for media_domain in media_domains:
                if media_domain in domain or media_domain in url:
                    return True
        
        # Check for image file extensions in URL
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        video_extensions = ['.mp4', '.webm', '.mov', '.avi', '.mkv', '.m4v']
        
        url_lower = url.lower()
        for ext in image_extensions + video_extensions:
            if url_lower.endswith(ext):
                return True
        
        # Skip posts with very short titles that are likely just media descriptions
        # But allow if there's substantial selftext content
        if len(title) < 10 and len(selftext) < 50:
            return True
        
        # Skip posts that are just single word titles or emoji-only
        if len(title.split()) <= 2 and not selftext:
            return True
        
        # Allow posts with substantial text content even if they have media
        if len(selftext) >= 100:  # Substantial text content
            return False
        
        # Check for common photo/video post patterns in titles
        media_title_patterns = [
            'check out this', 'look at this', 'found this', 'saw this',
            'my reaction when', 'mfw', 'mrw', 'me irl', 'meirl',
            'this is', 'here is', 'heres', 'behold',
            'feast your eyes', 'take a look'
        ]
        
        title_lower = title.lower()
        for pattern in media_title_patterns:
            if pattern in title_lower and len(selftext) < 50:
                return True
        
        return False
    
    def get_static_subreddits(self) -> List[str]:
        """
        Get a static list of known family-friendly subreddit names
        Used as fallback when dynamic discovery fails
        """
        # Popular/trending subreddits across different categories (PG content only)
        trending_subreddits = [
            # News & Current Events
            'worldnews', 'news', 'UpliftingNews',
            
            # Technology & Science
            'technology', 'science', 'space', 'futurology',
            
            # Educational
            'todayilearned', 'explainlikeimfive', 'YouShouldKnow', 'LifeProTips',
            
            # Entertainment (family-friendly)
            'movies', 'television', 'books', 'Music', 'wholesome',
            
            # Gaming (general)
            'gaming', 'nintendo', 'PatientGamers',
            
            # Animals & Nature
            'aww', 'NatureIsFuckingLit', 'rarepuppers', 'cats', 'dogs',
            
            # Art & Creativity
            'Art', 'pics', 'EarthPorn', 'food', 'FoodPorn',
            
            # Humor (clean)
            'funny', 'wholesomememes', 'MadeMeSmile', 'ContagiousLaughter',
            
            # Sports
            'sports', 'olympics',
            
            # General Discussion
            'AskReddit', 'CasualConversation', 'mildlyinteresting'
        ]
        
        return trending_subreddits
    
    def scrape_all_categories(self, posts_per_subreddit: int = 10) -> Dict[str, List[Dict]]:
        """
        Scrape posts from multiple categories/subreddits
        
        Args:
            posts_per_subreddit: Number of posts to fetch per subreddit
        
        Returns:
            Dictionary with category names as keys and lists of posts as values
        """
        all_data = {}
        
        # Get popular posts
        logger.info("Fetching popular posts...")
        popular_posts = self.get_popular_posts(limit=posts_per_subreddit)
        all_data['popular'] = popular_posts
        
        # Get posts from dynamically discovered trending subreddits
        trending_subreddits = self.get_dynamic_trending_subreddits(limit=50)
        
        for subreddit in trending_subreddits:
            time.sleep(1)  # Rate limiting - be respectful to Reddit's servers
            posts = self.get_subreddit_posts(subreddit, limit=posts_per_subreddit)
            if posts:
                all_data[f"r/{subreddit}"] = posts
        
        return all_data
    
    def save_to_json(self, data: Dict, filename: Optional[str] = None) -> str:
        """Save scraped data to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reddit_data_{timestamp}.json"
        
        filepath = f"c:\\Programming\\cos482-final-project\\{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Data saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return ""
    
    def save_to_csv(self, data: Dict, filename: Optional[str] = None) -> str:
        """Save scraped data to CSV file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reddit_data_{timestamp}.csv"
        
        filepath = f"c:\\Programming\\cos482-final-project\\{filename}"
        
        try:
            # Flatten all posts into a single list
            all_posts = []
            for category, posts in data.items():
                for post in posts:
                    post_copy = post.copy()
                    post_copy['category'] = category
                    all_posts.append(post_copy)
            
            if not all_posts:
                logger.warning("No posts to save to CSV")
                return ""
            
            # Get all unique field names
            fieldnames = set()
            for post in all_posts:
                fieldnames.update(post.keys())
            fieldnames = sorted(list(fieldnames))
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_posts)
            
            logger.info(f"Data saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            return ""

def main():
    """Main function to demonstrate the Reddit scraper"""
    print("Reddit Scraper - Dynamically discovering top 20 trending subreddits (PG content only)")
    print("=" * 80)
    
    scraper = RedditScraper()
    
    # Scrape data from all categories
    print("Starting to scrape Reddit data...")
    print("First discovering trending subreddits from popular posts...")
    all_data = scraper.scrape_all_categories(posts_per_subreddit=100)
    
    # Print summary
    total_posts = sum(len(posts) for posts in all_data.values())
    print(f"\nScraping completed! Total posts collected: {total_posts}")
    
    # Print sample data
    # print("\nSample of scraped data:")
    # for category, posts in all_data.items():
    #     if posts:
    #         print(f"\n{category} ({len(posts)} posts):")
    #         for i, post in enumerate(posts[:3]):  # Show first 3 posts
    #             print(f"  {i+1}. {post['title'][:80]}...")
    #             print(f"     Score: {post['score']} | Upvotes: {post['upvotes']} | Comments: {post['num_comments']}")
    #             if post['selftext']:
    #                 print(f"     Content: {post['selftext'][:100]}...")
            
    #         if len(posts) > 3:
    #             print(f"     ... and {len(posts) - 3} more posts")
    
    # Save data
    json_file = scraper.save_to_json(all_data)
    csv_file = scraper.save_to_csv(all_data)
    
    print(f"\nData saved to:")
    if json_file:
        print(f"  JSON: {json_file}")
    if csv_file:
        print(f"  CSV: {csv_file}")
    
    # Show some statistics
    print(f"\nStatistics:")
    for category, posts in all_data.items():
        if posts:
            total_score = sum(post['score'] for post in posts)
            avg_score = total_score / len(posts) if posts else 0
            max_score = max(post['score'] for post in posts) if posts else 0
            print(f"  {category}: Avg Score: {avg_score:.1f}, Max Score: {max_score}")

if __name__ == "__main__":
    main()