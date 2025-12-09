from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import sqlite3

nltk.download('vader_lexicon')

def analyze_sentiment(text):
    sia = SentimentIntensityAnalyzer()
    sentiment_scores = sia.polarity_scores(text)
    return sentiment_scores

conn = sqlite3.connect("reddit_data.db")
cursor = conn.cursor()

# Fill Sentiment Analysis Table With Posts
cursor.execute("SELECT * FROM posts")
posts = cursor.fetchall()
for post in posts:
    post_id = post[0]
    post_text = post[2]
    sentiment = analyze_sentiment(post_text)
    cursor.execute("""
        INSERT INTO sentiment_analysis (entity_type, entity_id, negative_score, neutral_score, positive_score, compound_score)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ('post', post_id, sentiment['neg'], sentiment['neu'], sentiment['pos'], sentiment['compound']))
    print(f"Progress: {posts.index(post) + 1}/{len(posts)} posts processed", end='\r')
    
# Fill Sentiment Analysis Table With Comments
cursor.execute("SELECT * FROM comments")
comments = cursor.fetchall()
for comment in comments:
    comment_id = comment[0]
    comment_text = comment[4]
    sentiment = analyze_sentiment(comment_text)
    cursor.execute("""
        INSERT INTO sentiment_analysis (entity_type, entity_id, negative_score, neutral_score, positive_score, compound_score)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ('comment', comment_id, sentiment['neg'], sentiment['neu'], sentiment['pos'], sentiment['compound']))
    print(f"Progress: {comments.index(comment) + 1}/{len(comments)} comments processed", end='\r')
    
conn.commit()
conn.close()