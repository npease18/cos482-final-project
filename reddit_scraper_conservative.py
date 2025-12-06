#!/usr/bin/env python3
"""
Conservative Reddit Scraper - Sample version for top trending subreddits
This version focuses on getting high-quality results from fewer subreddits
to avoid rate limiting while demonstrating the functionality.
"""

import requests
import json
import time
import os
from datetime import datetime, date, timezone, timedelta
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConservativeRedditScraper:
    """Conservative Reddit scraper that respects rate limits"""
    
    def __init__(self):
        self.base_url = "https://www.reddit.com"
        self.headers = {
            'User-Agent': 'ConservativeRedditScraper/1.0 (Educational Purpose)'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Get today's date range (December 4, 2025)
        self.today = date(2025, 12, 4)
        self.today_start = datetime.combine(self.today, datetime.min.time()).replace(tzinfo=timezone.utc)
        self.today_end = datetime.combine(self.today, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        logger.info(f"Filtering posts from: {self.today_start} to {self.today_end}")
    
    def get_top_subreddits_sample(self, limit: int = 50) -> List[str]:
        """
        Get a sample of trending subreddits to demonstrate the concept
        In a real implementation, this would discover 1000 subreddits
        """
        logger.info(f"Getting sample of {limit} trending subreddits...")
        
        # Use a curated list of popular, safe subreddits for demonstration
        trending_subreddits = [
            'technology', 'science', 'worldnews', 'news', 'todayilearned',
            'AskReddit', 'explainlikeimfive', 'LifeProTips', 'YouShouldKnow',
            'mildlyinteresting', 'interestingasfuck', 'Damnthatsinteresting',
            'pics', 'EarthPorn', 'NatureIsFuckingLit', 'BeAmazed',
            'aww', 'cats', 'dogs', 'rarepuppers', 'AnimalsBeingBros',
            'funny', 'wholesomememes', 'MadeMeSmile', 'ContagiousLaughter',
            'gaming', 'pcgaming', 'nintendo', 'playstation',
            'movies', 'television', 'books', 'Music',
            'programming', 'Python', 'MachineLearning', 'artificial',
            'DIY', 'woodworking', 'gardening', 'cooking', 'food',
            'photography', 'Art', 'oddlysatisfying', 'toptalent',
            'sports', 'fitness', 'running', 'bodybuilding',
            'personalfinance', 'investing', 'entrepreneur', 'jobs',
            'UpliftingNews', 'HumansBeingBros', 'MadeMeSmile'
        ]
        
        return trending_subreddits[:limit]
    
    def _is_family_friendly_subreddit(self, subreddit: str) -> bool:
        """Enhanced family-friendly subreddit checking"""
        if not subreddit:
            return False
            
        sub_lower = subreddit.lower()
        
        # Comprehensive list of NSFW keywords to avoid
        nsfw_keywords = [
            'nsfw', 'porn', 'sex', 'nude', 'xxx', 'gonewild', 'hookup', 
            'fetish', 'bdsm', 'escort', 'kinky', 'dirty', 'erotic', 'adult',
            'milf', 'teen', 'amateur', 'cum', 'cock', 'pussy', 'tits',
            'boobs', 'ass', 'butt', 'anal', 'oral', 'blow', 'fuck',
            'slut', 'whore', 'horny', 'sexy', 'hot', 'thick', 'curvy',
            'leaked', 'onlyfans', 'snapchat', 'kik', 'cam', 'webcam',
            'strip', 'naked', 'boob', 'nipple', 'panties', 'lingerie'
        ]
        
        # Check for problematic keywords and patterns
        for keyword in nsfw_keywords:
            if keyword in sub_lower:
                return False
        
        # Additional pattern checks
        if (sub_lower.endswith('porn') or 
            sub_lower.endswith('nsfw') or 
            'r4r' in sub_lower or
            'tribute' in sub_lower or
            ('rate' in sub_lower and 'me' in sub_lower)):
            return False
        
        return True
    
    def _is_post_from_today(self, post: Dict) -> bool:
        """Check if a post was created today"""
        created_utc = post.get('created_utc', 0)
        if created_utc == 0:
            return False
        
        post_date = datetime.fromtimestamp(created_utc, tz=timezone.utc)
        return self.today_start <= post_date <= self.today_end
    
    def _should_skip_post(self, post: Dict) -> bool:
        """Enhanced post filtering"""
        return (post.get('over_18', False) or 
                post.get('stickied', False) or 
                not self._is_post_from_today(post) or
                self._is_rules_post(post))
    
    def _is_rules_post(self, post: Dict) -> bool:
        """Check if a post is likely a rules/announcement post"""
        title = post.get('title', '')
        author = post.get('author', '')
        flair = post.get('link_flair_text', '')
        
        # Handle None values
        if title is None:
            title = ''
        if author is None:
            author = ''
        if flair is None:
            flair = ''
            
        title = title.lower()
        author = author.lower()
        flair = flair.lower()
        
        rules_keywords = [
            'rules', 'rule', 'subreddit rules', 'community rules',
            'guidelines', 'guideline', 'posting guidelines',
            'announcement', 'mod post', 'moderator post',
            'sticky', 'pinned', 'important', 'notice',
            'welcome', 'read this first', 'before posting'
        ]
        
        # Check title and author
        if any(keyword in title for keyword in rules_keywords):
            return True
        
        if 'automod' in author or 'bot' in author or author.startswith('mod'):
            return True
            
        if any(keyword in flair for keyword in ['rule', 'announcement', 'mod']):
            return True
        
        return False
    
    def get_subreddit_posts(self, subreddit: str, limit: int = 25) -> List[Dict]:
        """Get today's posts from a specific subreddit"""
        posts = []
        
        # Only use 'hot' to minimize API calls and avoid rate limits
        url = f"{self.base_url}/r/{subreddit}/hot.json"
        params = {'limit': limit}
        
        children = self._fetch_reddit_data(url, params)
        
        for item in children:
            post = item['data']
            if not self._should_skip_post(post):
                post_info = self._extract_post_info(post)
                posts.append(post_info)
        
        logger.info(f"r/{subreddit}: Found {len(posts)} posts from today")
        return posts
    
    def _extract_post_info(self, post: Dict) -> Dict:
        """Extract the specific information format requested"""
        # Handle division by zero for upvote calculations
        upvote_ratio = post.get('upvote_ratio', 0)
        score = post.get('score', 0)
        
        if upvote_ratio > 0:
            upvotes = round(score / upvote_ratio, 0)
            downvotes = round(upvotes - score, 0)
        else:
            upvotes = 0
            downvotes = 0
        
        info = {
            'id': post.get('id'),
            'title': post.get('title'),
            'subreddit': post.get('subreddit'),
            'selftext': post.get('selftext', ''),
            'permalink': f"https://www.reddit.com{post.get('permalink')}",
            'upvotes': int(upvotes) if upvotes >= 0 else 0,
            'downvotes': int(downvotes) if downvotes >= 0 else 0,
            'score': score,
            'upvote_ratio': upvote_ratio,
            'num_comments': post.get('num_comments', 0),
            'created_datetime': datetime.fromtimestamp(post.get('created_utc', 0)).isoformat(),
            'flair_text': post.get('link_flair_text', ''),
        }
        return info
    
    def _fetch_reddit_data(self, url: str, params: Dict) -> List[Dict]:
        """Fetch and parse Reddit JSON data with error handling and retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=15)
                
                if response.status_code == 429:  # Rate limit
                    logger.warning(f"Rate limited. Waiting {retry_delay * (attempt + 1)} seconds...")
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                    
                response.raise_for_status()
                data = response.json()
                return data['data']['children']
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error(f"All attempts failed for {url}")
                    return []
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"JSON parsing error for {url}: {e}")
                return []
        
        return []
    
    def scrape_sample_subreddits(self, target_subreddits: int = 50) -> Dict[str, List[Dict]]:
        """
        Sample scraping function for demonstration
        """
        logger.info(f"Starting to scrape {target_subreddits} sample subreddits for today's posts")
        
        # Get sample subreddits
        sample_subreddits = self.get_top_subreddits_sample(target_subreddits)
        
        all_data = {}
        processed = 0
        total_posts = 0
        
        for subreddit in sample_subreddits:
            try:
                posts = self.get_subreddit_posts(subreddit, 25)
                
                if posts:
                    all_data[f"r/{subreddit}"] = posts
                    total_posts += len(posts)
                
                processed += 1
                
                if processed % 10 == 0:
                    logger.info(f"Processed {processed}/{len(sample_subreddits)} subreddits. Total posts: {total_posts}")
                
                # Rate limiting - be respectful to Reddit's servers
                time.sleep(2.0)  # Conservative 2-second delay
                
            except Exception as e:
                logger.error(f"Error processing r/{subreddit}: {e}")
                continue
        
        logger.info(f"Scraping completed! Processed {processed} subreddits, collected {total_posts} posts from today")
        return all_data
    
    def save_to_json(self, data: Dict, filename: Optional[str] = None) -> str:
        """Save scraped data to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reddit_sample_today_{timestamp}.json"
        
        # Save to current directory
        filepath = os.path.abspath(filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Data saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return ""

def main():
    """Main function to run the conservative Reddit scraper"""
    print("Conservative Reddit Scraper - Sample Implementation")
    print("=" * 60)
    print(f"Target Date: December 4, 2025")
    print("Filtering: NSFW content excluded, today's posts only")
    print("Note: This is a conservative sample to demonstrate functionality")
    print()
    
    scraper = ConservativeRedditScraper()
    
    # Scrape data from sample subreddits
    print("Starting conservative Reddit scraping...")
    all_data = scraper.scrape_sample_subreddits(target_subreddits=25)  # Start with just 25 for testing
    
    # Calculate statistics
    total_posts = sum(len(posts) for posts in all_data.values())
    total_subreddits = len(all_data)
    
    print(f"\nScraping Results:")
    print(f"  Total subreddits processed: {total_subreddits}")
    print(f"  Total posts from today: {total_posts}")
    
    if total_posts > 0:
        # Show sample of collected data
        print(f"\nSample of collected posts:")
        sample_count = 0
        for subreddit, posts in all_data.items():
            if sample_count >= 5:  # Show first 5 subreddits
                break
            if posts:
                print(f"\n{subreddit} ({len(posts)} posts):")
                for i, post in enumerate(posts[:3]):  # Show first 3 posts per subreddit
                    print(f"  {i+1}. {post['title'][:60]}...")
                    print(f"     Score: {post['score']} | Comments: {post['num_comments']}")
                    print(f"     Created: {post['created_datetime']}")
                sample_count += 1
        
        # Save data
        json_file = scraper.save_to_json(all_data)
        
        if json_file:
            print(f"\nData successfully saved to: {json_file}")
            
            # Show file size
            try:
                file_size = os.path.getsize(json_file)
                print(f"File size: {file_size / 1024:.2f} KB")
            except:
                pass
                
            # Show structure example
            print("\nExample of extracted data structure:")
            if all_data:
                first_subreddit = list(all_data.keys())[0]
                first_posts = all_data[first_subreddit]
                if first_posts:
                    example_post = first_posts[0]
                    print(json.dumps(example_post, indent=2))
        else:
            print("\nError: Failed to save data to file")
    else:
        print("\nNo posts found from today matching the criteria.")
        print("This could be because:")
        print("- Posts were made on a different date")
        print("- Rate limiting prevented data collection")
        print("- All posts were filtered out due to NSFW or rules filters")

if __name__ == "__main__":
    main()