#!/usr/bin/env python3

import json
import sys
from pathlib import Path

def count_reddit_data(json_file_path):
    """
    Count totals from the Reddit JSON data file.
    
    Args:
        json_file_path (str): Path to the Reddit JSON data file
        
    Returns:
        tuple: (total_subreddits, total_posts, total_comments)
    """
    try:
        print(f"Loading JSON data from: {json_file_path}")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("JSON data loaded successfully!")
        
        # Count subreddits (top-level keys)
        total_subreddits = len(data)
        
        # Count posts and comments
        total_posts = 0
        total_comments = 0
        
        print("Analyzing data...")
        
        for subreddit_name, posts in data.items():
            # Count posts in this subreddit
            subreddit_posts = len(posts)
            total_posts += subreddit_posts
            
            # Count comments in all posts of this subreddit
            subreddit_comments = 0
            for post in posts:
                if 'comments' in post and isinstance(post['comments'], list):
                    subreddit_comments += len(post['comments'])
            
            total_comments += subreddit_comments
            
            # Progress indicator for large datasets
            if total_posts % 1000 == 0:
                print(f"  Processed {total_posts} posts so far...")
        
        return total_subreddits, total_posts, total_comments
        
    except FileNotFoundError:
        print(f"Error: File '{json_file_path}' not found.")
        return None, None, None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in file '{json_file_path}': {e}")
        return None, None, None
    except Exception as e:
        print(f"Error: Unexpected error occurred: {e}")
        return None, None, None

def main():
    """Main function to execute the counting script."""
    
    # Default JSON file path
    json_file_path = "reddit_data.json"
    
    # Allow command line argument for different file path
    if len(sys.argv) > 1:
        json_file_path = sys.argv[1]
    
    # Check if file exists
    if not Path(json_file_path).exists():
        print(f"Error: File '{json_file_path}' does not exist.")
        print("Usage: python3 count_reddit_data.py [json_file_path]")
        sys.exit(1)
    
    print("=" * 60)
    print("🔍 REDDIT DATA ANALYSIS SCRIPT")
    print("=" * 60)
    print()
    
    # Get file size for reference
    file_size = Path(json_file_path).stat().st_size
    file_size_mb = file_size / (1024 * 1024)
    print(f"File: {json_file_path}")
    print(f"Size: {file_size:,} bytes ({file_size_mb:.1f} MB)")
    print()
    
    # Perform the counting
    total_subreddits, total_posts, total_comments = count_reddit_data(json_file_path)
    
    if total_subreddits is not None:
        print()
        print("=" * 60)
        print("📊 RESULTS SUMMARY")
        print("=" * 60)
        print(f"📁 Total Subreddits:     {total_subreddits:,}")
        print(f"📄 Total Posts:          {total_posts:,}")
        print(f"💬 Total Comments:       {total_comments:,}")
        print("=" * 60)
        print()
        
        # Additional statistics
        if total_subreddits > 0:
            avg_posts_per_subreddit = total_posts / total_subreddits
            print(f"📈 Average posts per subreddit: {avg_posts_per_subreddit:.1f}")
        
        if total_posts > 0:
            avg_comments_per_post = total_comments / total_posts
            print(f"💭 Average comments per post:   {avg_comments_per_post:.1f}")
        
        print()
        print("✅ Analysis completed successfully!")
        
    else:
        print("❌ Analysis failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()