import sqlite3
import json

connection = sqlite3.connect('reddit_store.db')
cursor = connection.cursor()

# {
#     "id": "1p6cx7f",
#     "title": "White House Declares All of Trump’s Orders to Military Are Legal",
#     "subreddit": "law",
#     "selftext": "",
#     "permalink": "https://www.reddit.com/r/law/comments/1p6cx7f/white_house_declares_all_of_trumps_orders_to/",
#     "upvotes": 13592,
#     "downvotes": 0,
#     "score": 13592,
#     "upvote_ratio": 0.94,
#     "num_comments": 2583,
#     "created_datetime": "2025-11-25T08:50:03",
#     "flair_text": "Executive Branch (Trump)"
# },

cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id TEXT PRIMARY KEY,
        title TEXT,
        subreddit TEXT,
        selftext TEXT,
        permalink TEXT,
        upvotes INTEGER,
        downvotes INTEGER,
        score INTEGER,
        upvote_ratio REAL,
        num_comments INTEGER,
        created_datetime TEXT,
        flair_text TEXT
    )''')

with open('reddit_data_20251125_145301.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

for subreddit in data:
    print("Loading Subreddit: " + subreddit)
    for post in data[subreddit]:
        cursor.execute('''
            INSERT INTO posts (
                id, title, subreddit, selftext, permalink,
                upvotes, downvotes, score, upvote_ratio,
                num_comments, created_datetime, flair_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        
        ''', (
            post['id'],
            post['title'],
            post['subreddit'],
            post['selftext'],
            post['permalink'],
            post['upvotes'],
            post['downvotes'],
            post['score'],
            post['upvote_ratio'],
            post['num_comments'],
            post['created_datetime'],
            post.get('flair_text', None)
        ))

connection.commit()
connection.close()
