#!/usr/bin/env python3
"""
Enhanced Reddit Scraper - Extract posts from top 1000 trending subreddits from the past week
This scraper gets the top 1000 trending subreddits and fetches posts created or 
commented on within the past 7 days from when the program is run. Strictly filters out all NSFW content.
"""

import requests
import json
import time
import os
from datetime import datetime, date, timezone, timedelta
from typing import List, Dict, Optional
import logging
import math
import random
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedRedditScraper:
    """Enhanced Reddit scraper for 1000 trending subreddits with past-week filtering"""
    
    def __init__(self):
        self.base_url = "https://www.reddit.com"
        self.headers = {
            'User-Agent': 'EnhancedRedditScraper/2.0 (Educational Purpose)'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Rate limiting configuration
        self.request_times = deque(maxlen=100)  # Track last 100 requests
        self.requests_per_minute = 30  # Conservative rate limit
        self.base_delay = 2.0  # Base delay between requests (seconds)
        self.max_delay = 300  # Maximum delay for exponential backoff (5 minutes)
        self.rate_limit_count = 0  # Track consecutive rate limits
        self.backoff_multiplier = 2  # Exponential backoff multiplier
        
        # Get date range for the past week (7 days from today)
        self.today = datetime.now(timezone.utc).date()
        self.week_ago = self.today - timedelta(days=7)
        self.week_start = datetime.combine(self.week_ago, datetime.min.time()).replace(tzinfo=timezone.utc)
        self.week_end = datetime.combine(self.today, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        logger.info(f"Filtering posts from the past week: {self.week_start.date()} to {self.week_end.date()}")
        logger.info(f"Rate limiting: {self.requests_per_minute} requests/minute with {self.base_delay}s base delay")
    
    def get_top_trending_subreddits(self, target_count: int = 1000) -> List[str]:
        """
        Discover the top trending subreddits by analyzing popular posts across multiple sources
        
        Args:
            target_count: Target number of unique subreddits to discover (1000)
        
        Returns:
            List of subreddit names
        """
        logger.info(f"Discovering top {target_count} trending subreddits...")
        
        subreddit_scores = {}
        discovered_subreddits = set()
        
        # Sources to discover trending subreddits from
        sources = [
            ('popular', 'hot'),
            ('popular', 'top'),
            ('all', 'hot'),
            ('all', 'top'),
            ('all', 'rising'),
        ]
        
        for source_type, sort_method in sources:
            logger.info(f"Scanning r/{source_type} sorted by {sort_method}")
            
            # Get posts from each source
            url = f"{self.base_url}/r/{source_type}/{sort_method}.json"
            
            # Fetch multiple pages to get more subreddits
            for page in range(10):  # Get 10 pages of 100 posts each
                params = {'limit': 100, 'after': None}
                if page > 0:
                    # For subsequent pages, we'd need the 'after' token, but Reddit's JSON API
                    # doesn't always provide it easily. We'll work with what we can get.
                    continue
                
                children = self._fetch_reddit_data(url, params)
                
                for item in children:
                    post = item['data']
                    subreddit = post.get('subreddit')
                    
                    if (subreddit and 
                        not post.get('over_18', False) and 
                        self._is_family_friendly_subreddit(subreddit)):
                        
                        # Score subreddits based on post metrics
                        score = post.get('score', 0) + (post.get('num_comments', 0) * 2)
                        
                        if subreddit in subreddit_scores:
                            subreddit_scores[subreddit] += score
                        else:
                            subreddit_scores[subreddit] = score
                            
                        discovered_subreddits.add(subreddit)
            
            logger.info(f"Found {len(discovered_subreddits)} unique subreddits so far")
            
            if len(discovered_subreddits) >= target_count:
                break
        
        # Sort by score and return top subreddits
        sorted_subreddits = sorted(
            subreddit_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        top_subreddits = [subreddit for subreddit, score in sorted_subreddits[:target_count]]
        
        # If we don't have enough, supplement with static list
        if len(top_subreddits) < target_count:
            logger.info("Supplementing with additional popular subreddits...")
            static_subreddits = self.get_comprehensive_subreddit_list()
            
            for subreddit in static_subreddits:
                if subreddit not in top_subreddits and len(top_subreddits) < target_count:
                    top_subreddits.append(subreddit)
        
        final_count = min(len(top_subreddits), target_count)
        result = top_subreddits[:final_count]
        
        logger.info(f"Final trending subreddits count: {len(result)}")
        
        return result
    
    def get_comprehensive_subreddit_list(self) -> List[str]:
        """Get a comprehensive list of popular, family-friendly subreddits"""
        return [
            # Major news and current events
            'worldnews', 'news', 'politics', 'UpliftingNews', 'nottheonion',
            
            # Technology and science
            'technology', 'science', 'space', 'futurology', 'programming',
            'artificial', 'gadgets', 'DIY', 'InternetIsBeautiful',
            
            # Educational and informative
            'todayilearned', 'explainlikeimfive', 'YouShouldKnow', 'LifeProTips',
            'educationalgifs', 'coolguides', 'dataisbeautiful', 'MapPorn',
            
            # Entertainment
            'movies', 'television', 'netflix', 'books', 'Music', 'spotify',
            'Marvel', 'StarWars', 'harrypotter', 'DunderMifflin',
            
            # Gaming
            'gaming', 'pcgaming', 'nintendo', 'playstation', 'xbox',
            'minecraft', 'pokemon', 'FortNiteBR', 'apexlegends',
            
            # Animals and nature
            'aww', 'NatureIsFuckingLit', 'rarepuppers', 'cats', 'dogs',
            'AnimalsBeingBros', 'NatureIsMetal', 'Eyebleach', 'AnimalsBeingDerps',
            
            # Art and creativity
            'Art', 'pics', 'EarthPorn', 'food', 'FoodPorn', 'oddlysatisfying',
            'mildlyinteresting', 'BeAmazed', 'nextfuckinglevel', 'toptalent',
            
            # Humor and memes
            'funny', 'memes', 'dankmemes', 'wholesomememes', 'MadeMeSmile',
            'ContagiousLaughter', 'facepalm', 'therewasanattempt', 'instant_regret',
            
            # Sports and fitness
            'sports', 'nfl', 'nba', 'soccer', 'fitness', 'bodybuilding',
            'running', 'swimming', 'tennis', 'baseball',
            
            # Lifestyle and advice
            'AskReddit', 'relationship_advice', 'AmItheAsshole', 'LifeAdvice',
            'personalfinance', 'investing', 'frugal', 'BuyItForLife',
            
            # Specific interests
            'cars', 'motorcycles', 'photography', 'architecture', 'design',
            'woodworking', 'gardening', 'houseplants', 'cooking', 'baking',
            
            # Regional and cultural
            'europe', 'canada', 'australia', 'unitedkingdom', 'germany',
            'france', 'italy', 'japan', 'india', 'brasil',
            
            # Professional and career
            'jobs', 'careerguidance', 'entrepreneur', 'smallbusiness',
            'marketing', 'webdev', 'cscareerquestions', 'ITCareerQuestions',
            
            # Health and wellness
            'health', 'nutrition', 'mentalhealth', 'meditation', 'yoga',
            'loseit', 'progresspics', 'getmotivated', 'decidingtobebetter',
            
            # Hobbies and collections
            'woodworking', 'knitting', 'boardgames', 'DnD', 'LEGO',
            'coins', 'stamps', 'vinyl', 'funkopop', 'comics'
        ]
    
    def _is_family_friendly_subreddit(self, subreddit: str) -> bool:
        """Enhanced family-friendly subreddit checking"""
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
            sub_lower.startswith('real') and any(nsfw in sub_lower for nsfw in ['girls', 'women']) or
            'tribute' in sub_lower or
            'rate' in sub_lower and 'me' in sub_lower):
            return False
        
        return True
    
    def _wait_for_rate_limit(self) -> None:
        """Implement intelligent rate limiting with request tracking"""
        current_time = time.time()
        
        # Add current request time
        self.request_times.append(current_time)
        
        # Calculate requests in the last minute
        one_minute_ago = current_time - 60
        recent_requests = sum(1 for req_time in self.request_times if req_time > one_minute_ago)
        
        # If we're approaching the rate limit, wait
        if recent_requests >= self.requests_per_minute:
            # Calculate how long to wait until we can make the next request
            oldest_recent = min(req_time for req_time in self.request_times if req_time > one_minute_ago)
            wait_time = 60 - (current_time - oldest_recent) + 1  # Add 1 second buffer
            
            if wait_time > 0:
                logger.info(f"Rate limit prevention: waiting {wait_time:.1f} seconds")
                time.sleep(wait_time)
        
        # Add base delay with some randomization to avoid thundering herd
        jitter = random.uniform(0.5, 1.5)
        delay = self.base_delay * jitter
        
        # If we've hit rate limits recently, use exponential backoff
        if self.rate_limit_count > 0:
            backoff_delay = min(self.base_delay * (self.backoff_multiplier ** self.rate_limit_count), self.max_delay)
            delay = max(delay, backoff_delay)
            logger.info(f"Exponential backoff active: {backoff_delay:.1f}s delay (rate limit count: {self.rate_limit_count})")
        
        time.sleep(delay)
    
    def _handle_rate_limit_response(self, response: requests.Response) -> bool:
        """Handle rate limit responses and implement backoff strategy"""
        if response.status_code == 429:
            self.rate_limit_count += 1
            
            # Try to extract retry-after header
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                try:
                    wait_time = int(retry_after)
                except ValueError:
                    wait_time = 60  # Default to 1 minute
            else:
                # Use exponential backoff if no retry-after header
                wait_time = min(self.base_delay * (self.backoff_multiplier ** self.rate_limit_count), self.max_delay)
            
            logger.warning(f"Rate limited (429). Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
            return True
        
        # Reset rate limit count on successful request
        if response.status_code == 200:
            self.rate_limit_count = max(0, self.rate_limit_count - 1)
        
        return False
    
    def _is_post_from_past_week(self, post: Dict) -> bool:
        """Check if a post was created within the past week"""
        created_utc = post.get('created_utc', 0)
        if created_utc == 0:
            return False
        
        post_date = datetime.fromtimestamp(created_utc, tz=timezone.utc)
        return self.week_start <= post_date <= self.week_end
    
    def _should_skip_post(self, post: Dict) -> bool:
        """Enhanced post filtering"""
        return (post.get('over_18', False) or 
                post.get('stickied', False) or 
                not self._is_post_from_past_week(post) or
                self._is_rules_post(post) or 
                self._is_media_only_post(post))
    
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
    
    def _is_media_only_post(self, post: Dict) -> bool:
        """Check if a post is video or photo-only with minimal text content"""
        selftext = post.get('selftext', '').strip()
        url = post.get('url', '')
        
        # Allow posts with substantial text content
        if len(selftext) >= 50:
            return False
        
        # Check for direct media posts
        if post.get('is_video', False):
            return True
        
        # Check for media URLs
        media_patterns = ['i.redd.it', 'v.redd.it', 'imgur.com', 'youtube.com', 'youtu.be']
        if any(pattern in url.lower() for pattern in media_patterns):
            return True
        
        return False
    
    def _fetch_post_comments(self, permalink: str, limit: int = 100) -> List[Dict]:
        """Fetch comments from a specific Reddit post"""
        # Reddit API endpoint for post with comments
        url = f"{self.base_url}{permalink}.json"
        params = {'limit': limit, 'depth': 3}  # Limit depth to avoid too much nesting
        
        try:
            # Apply rate limiting
            self._wait_for_rate_limit()
            
            response = self.session.get(url, params=params, timeout=15)
            
            # Handle rate limiting
            if self._handle_rate_limit_response(response):
                return []  # Return empty if rate limited
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch comments from {permalink}: {response.status_code}")
                return []
            
            data = response.json()
            
            # Reddit returns an array: [post_data, comments_data]
            if len(data) < 2 or 'data' not in data[1] or 'children' not in data[1]['data']:
                logger.debug(f"No comments found for {permalink}")
                return []
            
            comments = []
            self._extract_comments_recursive(data[1]['data']['children'], comments)
            
            logger.debug(f"Fetched {len(comments)} comments from {permalink}")
            return comments
            
        except Exception as e:
            logger.error(f"Error fetching comments from {permalink}: {e}")
            return []
    
    def _extract_comments_recursive(self, children: List[Dict], comments: List[Dict], depth: int = 0) -> None:
        """Recursively extract comments from Reddit's nested structure"""
        max_depth = 3  # Limit recursion depth
        
        for child in children:
            if child.get('kind') == 't1':  # t1 = comment
                comment_data = child.get('data', {})
                
                # Skip deleted comments and automoderator
                if (comment_data.get('author') in ['[deleted]', 'AutoModerator'] or
                    comment_data.get('body') in ['[deleted]', '[removed]']):
                    continue
                
                # Extract comment information
                comment_info = {
                    'id': comment_data.get('id'),
                    'author': comment_data.get('author'),
                    'body': comment_data.get('body', ''),
                    'score': comment_data.get('score', 0),
                    'created_datetime': datetime.fromtimestamp(
                        comment_data.get('created_utc', 0)
                    ).isoformat() if comment_data.get('created_utc') else None,
                    'parent_id': comment_data.get('parent_id'),
                    'depth': depth,
                    'is_submitter': comment_data.get('is_submitter', False),
                    'stickied': comment_data.get('stickied', False),
                    'edited': bool(comment_data.get('edited', False))
                }
                
                comments.append(comment_info)
                
                # Process replies if they exist and we haven't hit max depth
                if (depth < max_depth and 
                    comment_data.get('replies') and 
                    isinstance(comment_data['replies'], dict)):
                    
                    replies_data = comment_data['replies'].get('data', {})
                    if 'children' in replies_data:
                        self._extract_comments_recursive(
                            replies_data['children'], 
                            comments, 
                            depth + 1
                        )
    
    def get_subreddit_posts(self, subreddit: str, limit: int = 100, fetch_comments: bool = True) -> List[Dict]:
        """Get posts from the past week from a specific subreddit with rate limiting
        
        Args:
            subreddit: Name of the subreddit
            limit: Maximum number of posts to fetch
            fetch_comments: Whether to fetch comments for each post (default: True)
        """
        posts = []
        
        # Try different sort methods to get more recent posts
        sort_methods = ['hot', 'new', 'rising']
        
        for sort_method in sort_methods:
            url = f"{self.base_url}/r/{subreddit}/{sort_method}.json"
            params = {'limit': min(limit, 100)}  # Reddit API limit is 100
            
            children = self._fetch_reddit_data(url, params)
            
            posts_added = 0
            for item in children:
                post = item['data']
                if not self._should_skip_post(post):
                    post_info = self._extract_post_info(post, fetch_comments)
                    # Check for duplicates based on post ID
                    if not any(p['id'] == post_info['id'] for p in posts):
                        posts.append(post_info)
                        posts_added += 1
            
            logger.debug(f"r/{subreddit}/{sort_method}: Added {posts_added} new posts")
            
            # If we didn't get any new posts from this sort method, skip the remaining ones
            if posts_added == 0 and sort_method != 'hot':
                logger.debug(f"No new posts found in r/{subreddit}/{sort_method}, skipping remaining sort methods")
                break
        
        logger.info(f"r/{subreddit}: Found {len(posts)} posts from the past week")
        return posts
    
    def _extract_post_info(self, post: Dict, fetch_comments: bool = True) -> Dict:
        """Extract the specific information format requested, including comments"""
        # Handle division by zero for upvote calculations
        upvote_ratio = post.get('upvote_ratio', 0)
        score = post.get('score', 0)
        
        if upvote_ratio > 0:
            upvotes = round(score / upvote_ratio, 0)
            downvotes = round(upvotes - score, 0)
        else:
            upvotes = 0
            downvotes = 0
        
        permalink = post.get('permalink', '')
        
        info = {
            'id': post.get('id'),
            'title': post.get('title'),
            'subreddit': post.get('subreddit'),
            'selftext': post.get('selftext', ''),
            'permalink': f"https://www.reddit.com{permalink}",
            'upvotes': int(upvotes),
            'downvotes': int(downvotes),
            'score': score,
            'upvote_ratio': upvote_ratio,
            'num_comments': post.get('num_comments', 0),
            'created_datetime': datetime.fromtimestamp(post.get('created_utc', 0)).isoformat(),
            'flair_text': post.get('link_flair_text', ''),
            'author': post.get('author', ''),
            'url': post.get('url', ''),
            'is_video': post.get('is_video', False),
            'over_18': post.get('over_18', False)
        }
        
        # Fetch comments if requested and post has comments
        if fetch_comments and post.get('num_comments', 0) > 0:
            logger.debug(f"Fetching comments for post {info['id']}")
            comments = self._fetch_post_comments(permalink)
            info['comments'] = comments
            info['comments_fetched'] = len(comments)
        else:
            info['comments'] = []
            info['comments_fetched'] = 0
        
        return info
    
    def _fetch_reddit_data(self, url: str, params: Dict) -> List[Dict]:
        """Fetch and parse Reddit JSON data with comprehensive rate limiting and error handling"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Wait for rate limiting before making request
                self._wait_for_rate_limit()
                
                response = self.session.get(url, params=params, timeout=15)
                
                # Handle rate limiting
                if self._handle_rate_limit_response(response):
                    retry_count += 1
                    continue
                
                # Handle other HTTP errors
                if response.status_code == 403:
                    logger.error(f"Access forbidden (403) for {url}. Skipping...")
                    return []
                elif response.status_code == 404:
                    logger.warning(f"Resource not found (404) for {url}. Skipping...")
                    return []
                elif response.status_code >= 500:
                    logger.warning(f"Server error ({response.status_code}) for {url}. Retrying...")
                    retry_count += 1
                    time.sleep(min(2 ** retry_count, 30))  # Exponential backoff for server errors
                    continue
                
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    data = response.json()
                    if 'data' not in data or 'children' not in data['data']:
                        logger.warning(f"Unexpected JSON structure from {url}")
                        return []
                    
                    logger.debug(f"Successfully fetched {len(data['data']['children'])} items from {url}")
                    return data['data']['children']
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error for {url}: {e}")
                    return []
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout for {url}. Retry {retry_count + 1}/{max_retries}")
                retry_count += 1
                time.sleep(min(2 ** retry_count, 30))
                
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error for {url}. Retry {retry_count + 1}/{max_retries}")
                retry_count += 1
                time.sleep(min(2 ** retry_count, 30))
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error for {url}: {e}")
                retry_count += 1
                time.sleep(min(2 ** retry_count, 30))
                
            except Exception as e:
                logger.error(f"Unexpected error for {url}: {e}")
                return []
        
        logger.error(f"All {max_retries} retry attempts failed for {url}")
        return []
    
    def scrape_trending_subreddits(self, target_subreddits: int = 1000, posts_per_subreddit: int = 50, fetch_comments: bool = True) -> Dict[str, List[Dict]]:
        """
        Main scraping function for top trending subreddits
        
        Args:
            target_subreddits: Number of trending subreddits to scrape (1000)
            posts_per_subreddit: Max posts to get per subreddit
            fetch_comments: Whether to fetch comments for each post (default: True)
        
        Returns:
            Dictionary with subreddit names as keys and lists of posts as values
        """
        comment_status = "with comments" if fetch_comments else "without comments"
        logger.info(f"Starting to scrape {target_subreddits} trending subreddits for posts from the past week ({comment_status})")
        
        # Get trending subreddits
        trending_subreddits = self.get_top_trending_subreddits(target_subreddits)
        
        all_data = {}
        processed = 0
        total_posts = 0
        
        for subreddit in trending_subreddits:
            try:
                posts = self.get_subreddit_posts(subreddit, posts_per_subreddit, fetch_comments)
                
                if posts:
                    all_data[f"r/{subreddit}"] = posts
                    total_posts += len(posts)
                
                processed += 1
                
                if processed % 10 == 0:  # More frequent updates due to longer processing time
                    logger.info(f"Processed {processed}/{len(trending_subreddits)} subreddits. Total posts: {total_posts}")
                    logger.info(f"Rate limit stats - Count: {self.rate_limit_count}, Recent requests: {len([t for t in self.request_times if time.time() - t < 60])}")
                    total_comments = sum(post.get('comments_fetched', 0) for posts in all_data.values() for post in posts)
                    logger.info(f"Total comments fetched so far: {total_comments}")
                
            except Exception as e:
                logger.error(f"Error processing r/{subreddit}: {e}")
                continue
        
        logger.info(f"Scraping completed! Processed {processed} subreddits, collected {total_posts} posts from the past week")
        
        # Calculate comment statistics
        total_comments = sum(post.get('comments_fetched', 0) for posts in all_data.values() for post in posts)
        logger.info(f"Total comments fetched: {total_comments}")
        
        return all_data
    
    def save_to_json(self, data: Dict, filename: Optional[str] = None) -> str:
        """Save scraped data to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reddit_trending_1000_past_week_{timestamp}.json"
        
        # Save to current directory instead of hardcoded Windows path
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
    """Main function to run the enhanced Reddit scraper"""
    current_date = datetime.now().strftime("%B %d, %Y")
    week_ago_date = (datetime.now() - timedelta(days=7)).strftime("%B %d, %Y")
    
    print("Enhanced Reddit Scraper - Top 1000 Trending Subreddits (Past Week's Posts)")
    print("=" * 80)
    print(f"Date Range: {week_ago_date} to {current_date}")
    print("Filtering: NSFW content excluded, posts from past 7 days only")
    print()
    
    scraper = EnhancedRedditScraper()
    
    # Option to disable comment fetching for faster execution
    fetch_comments = True  # Set to False for faster execution without comments
    
    # Scrape data from top 1000 trending subreddits
    print("Starting enhanced Reddit scraping...")
    if not fetch_comments:
        print("Note: Comment fetching is disabled for faster execution")
    
    all_data = scraper.scrape_trending_subreddits(
        target_subreddits=1000, 
        posts_per_subreddit=25,
        fetch_comments=fetch_comments
    )
    
    # Calculate statistics
    total_posts = sum(len(posts) for posts in all_data.values())
    total_subreddits = len(all_data)
    total_comments = sum(post.get('comments_fetched', 0) for posts in all_data.values() for post in posts)
    
    print(f"\nScraping Results:")
    print(f"  Total subreddits processed: {total_subreddits}")
    print(f"  Total posts from past week: {total_posts}")
    print(f"  Total comments fetched: {total_comments}")
    
    if total_posts > 0:
        # Show sample of collected data
        print(f"\nSample of collected posts:")
        sample_count = 0
        for subreddit, posts in all_data.items():
            if sample_count >= 5:  # Show first 5 subreddits
                break
            if posts:
                print(f"\n{subreddit} ({len(posts)} posts):")
                for i, post in enumerate(posts[:2]):  # Show first 2 posts per subreddit
                    print(f"  {i+1}. {post['title'][:60]}...")
                    print(f"     Score: {post['score']} | Comments: {post['num_comments']} | Created: {post['created_datetime']}")
                sample_count += 1
        
        # Save data
        json_file = scraper.save_to_json(all_data)
        
        if json_file:
            print(f"\nData successfully saved to: {json_file}")
            
            # Show file size
            try:
                file_size = os.path.getsize(json_file)
                print(f"File size: {file_size / (1024*1024):.2f} MB")
            except:
                pass
        else:
            print("\nError: Failed to save data to file")
    else:
        print("\nNo posts found from the past week matching the criteria.")

if __name__ == "__main__":
    main()