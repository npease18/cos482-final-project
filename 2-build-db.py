#!/usr/bin/env python3

import json
import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime
import re

class RedditDataLoader:
    def __init__(self, db_path="reddit_data.db"):
        """Initialize the Reddit data loader with database connection."""
        self.db_path = db_path
        self.conn = None
        
    def create_database(self, schema_path="schema.sql"):
        """Create the database and tables using the schema file."""
        try:
            # Connect to database (creates if doesn't exist)
            self.conn = sqlite3.connect(self.db_path)
            print(f"Connected to database: {self.db_path}")
            
            # Read and execute schema
            if not Path(schema_path).exists():
                raise FileNotFoundError(f"Schema file '{schema_path}' not found. Please ensure the schema file exists.")
                
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            # Execute schema statements
            self.conn.executescript(schema)
            self.conn.commit()
            print("Database schema created successfully!")
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise
            

        
    def parse_datetime_to_utc(self, datetime_str):
        """Convert ISO datetime string to UTC timestamp."""
        try:
            if datetime_str:
                # Parse ISO format datetime
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                return int(dt.timestamp())
        except Exception as e:
            print(f"Warning: Could not parse datetime '{datetime_str}': {e}")
        return None
        
    def clean_subreddit_name(self, name):
        """Clean subreddit name by removing 'r/' prefix if present."""
        if name.startswith('r/'):
            return name[2:]
        return name
        
    def insert_subreddit(self, name):
        """Insert subreddit and return its ID."""
        clean_name = self.clean_subreddit_name(name)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO subreddits (name) VALUES (?)",
                (clean_name,)
            )
            
            # Get the subreddit ID
            cursor.execute("SELECT id FROM subreddits WHERE name = ?", (clean_name,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            else:
                raise Exception(f"Failed to get subreddit ID for '{clean_name}'")
                
        except sqlite3.Error as e:
            print(f"Error inserting subreddit '{clean_name}': {e}")
            raise
            
    def insert_post(self, post_data, subreddit_id):
        """Insert a post into the database."""
        try:
            created_utc = self.parse_datetime_to_utc(post_data.get('created_datetime'))
            
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO posts (
                    id, subreddit_id, title, content, author, score, 
                    upvotes, downvotes, num_comments, created_utc, url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                post_data.get('id'),
                subreddit_id,
                post_data.get('title', ''),
                post_data.get('selftext', ''),
                post_data.get('author', ''),
                post_data.get('score', 0),
                post_data.get('upvotes', 0),
                post_data.get('downvotes', 0),
                post_data.get('num_comments', 0),
                created_utc,
                post_data.get('url', '')
            ))
            
        except sqlite3.Error as e:
            print(f"Error inserting post '{post_data.get('id')}': {e}")
            raise
            
    def insert_comment(self, comment_data, post_id):
        """Insert a comment into the database."""
        try:
            created_utc = self.parse_datetime_to_utc(comment_data.get('created_datetime'))
            
            # Clean parent_id - remove Reddit prefixes like 't1_', 't3_'
            parent_id = comment_data.get('parent_id', '')
            if parent_id:
                # Remove Reddit type prefixes (t1_, t3_, etc.)
                parent_id = re.sub(r'^t[0-9]_', '', parent_id)
                # If parent is the post itself, set to NULL
                if parent_id == post_id:
                    parent_id = None
            else:
                parent_id = None
                
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO comments (
                    id, post_id, parent_id, author, content, score, created_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                comment_data.get('id'),
                post_id,
                parent_id,
                comment_data.get('author', ''),
                comment_data.get('body', ''),
                comment_data.get('score', 0),
                created_utc
            ))
            
        except sqlite3.Error as e:
            print(f"Error inserting comment '{comment_data.get('id')}': {e}")
            raise
            
    def load_json_data(self, json_file_path):
        """Load Reddit data from JSON file into the database."""
        try:
            print(f"Loading JSON data from: {json_file_path}")
            
            # Check file size
            file_size = Path(json_file_path).stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            print(f"File size: {file_size_mb:.1f} MB")
            
            # Load JSON data
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            print("JSON data loaded successfully!")
            
            # Counters for progress tracking
            total_subreddits = len(data)
            total_posts = 0
            total_comments = 0
            processed_posts = 0
            
            print(f"Processing {total_subreddits} subreddits...")
            
            # Process each subreddit
            for subreddit_idx, (subreddit_name, posts) in enumerate(data.items(), 1):
                print(f"[{subreddit_idx}/{total_subreddits}] Processing {subreddit_name}...")
                
                # Insert subreddit
                subreddit_id = self.insert_subreddit(subreddit_name)
                
                # Process posts in this subreddit
                for post in posts:
                    # Insert post
                    self.insert_post(post, subreddit_id)
                    total_posts += 1
                    processed_posts += 1
                    
                    # Insert comments for this post
                    comments = post.get('comments', [])
                    for comment in comments:
                        self.insert_comment(comment, post.get('id'))
                        total_comments += 1
                    
                    # Progress indicator
                    if processed_posts % 1000 == 0:
                        print(f"  Processed {processed_posts} posts...")
                
                # Commit after each subreddit
                self.conn.commit()
                
            # Final commit
            self.conn.commit()
            
            return total_subreddits, total_posts, total_comments
            
        except FileNotFoundError:
            print(f"Error: JSON file '{json_file_path}' not found.")
            return None, None, None
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format: {e}")
            return None, None, None
        except Exception as e:
            print(f"Error loading data: {e}")
            return None, None, None
            
    def verify_data(self):
        """Verify the loaded data by counting records."""
        try:
            cursor = self.conn.cursor()
            
            # Count subreddits
            cursor.execute("SELECT COUNT(*) FROM subreddits")
            subreddit_count = cursor.fetchone()[0]
            
            # Count posts
            cursor.execute("SELECT COUNT(*) FROM posts")
            post_count = cursor.fetchone()[0]
            
            # Count comments
            cursor.execute("SELECT COUNT(*) FROM comments")
            comment_count = cursor.fetchone()[0]
            
            return subreddit_count, post_count, comment_count
            
        except sqlite3.Error as e:
            print(f"Error verifying data: {e}")
            return None, None, None
            
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

def main():
    """Main function to execute the JSON to SQLite loading process."""
    
    # Default file paths
    json_file_path = "reddit_data.json"
    db_path = "reddit_data.db"
    schema_path = "schema.sql"
    
    # Command line arguments
    if len(sys.argv) > 1:
        json_file_path = sys.argv[1]
    if len(sys.argv) > 2:
        db_path = sys.argv[2]
        
    # Check if JSON file exists
    if not Path(json_file_path).exists():
        print(f"Error: JSON file '{json_file_path}' does not exist.")
        print("Usage: python3 json_to_sqlite.py [json_file] [database_file]")
        sys.exit(1)
        
    print("=" * 70)
    print("🔄 REDDIT JSON TO SQLITE LOADER")
    print("=" * 70)
    print(f"JSON File: {json_file_path}")
    print(f"Database: {db_path}")
    print(f"Schema: {schema_path}")
    print()
    
    # Initialize loader
    loader = RedditDataLoader(db_path)
    
    try:
        # Create database and schema
        loader.create_database(schema_path)
        
        # Load JSON data
        print("Starting data loading process...")
        loaded_subreddits, loaded_posts, loaded_comments = loader.load_json_data(json_file_path)
        
        if loaded_subreddits is not None:
            # Verify loaded data
            print("\nVerifying loaded data...")
            db_subreddits, db_posts, db_comments = loader.verify_data()
            
            print("\n" + "=" * 70)
            print("📊 LOADING RESULTS")
            print("=" * 70)
            print(f"✅ Subreddits loaded: {loaded_subreddits:,} (verified: {db_subreddits:,})")
            print(f"✅ Posts loaded:      {loaded_posts:,} (verified: {db_posts:,})")
            print(f"✅ Comments loaded:   {loaded_comments:,} (verified: {db_comments:,})")
            print("=" * 70)
            print()
            
            # Additional database info
            db_size = Path(db_path).stat().st_size / (1024 * 1024)
            print(f"📁 Database size: {db_size:.1f} MB")
            print(f"🎉 Data loading completed successfully!")
            
        else:
            print("❌ Data loading failed. Please check the error messages above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error during loading process: {e}")
        sys.exit(1)
    finally:
        loader.close()

if __name__ == "__main__":
    main()