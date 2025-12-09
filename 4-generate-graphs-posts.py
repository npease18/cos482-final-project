import sqlite3
import numpy as np
from scipy import stats

import matplotlib.pyplot as plt

class ExtendedPosts:
    def __init__(self, post_from_db):
        self.id = post_from_db[0]
        self.subreddit_id = post_from_db[1]
        self.title = post_from_db[2]
        self.content = post_from_db[3]
        self.author = post_from_db[4]
        self.score = post_from_db[5]
        self.upvotes = post_from_db[6]
        self.downvotes = post_from_db[7]
        self.num_comments = post_from_db[8]
        self.sentiment_analysis_negativescore = post_from_db[15]
        self.sentiment_analysis_neutralscore = post_from_db[16]
        self.sentiment_analysis_positivescore = post_from_db[17]
        self.sentiment_analysis_compoundscore = post_from_db[18]


# Connect to the database
conn = sqlite3.connect('reddit_data.db')
cursor = conn.cursor()

# Query to get extended post data
cursor.execute("""
            SELECT * FROM posts
            LEFT JOIN sentiment_analysis
                ON sentiment_analysis.entity_type = "post"
                AND sentiment_analysis.entity_id = posts.id
""")
data = cursor.fetchall()
conn.close()

posts = [ExtendedPosts(row) for row in data]

upvotes = [post.upvotes for post in posts]
downvotes = [post.downvotes for post in posts]

# Plot upvotes vs downvotes
plt.figure(figsize=(10, 6))
plt.scatter(upvotes, downvotes, alpha=0.6)

# Add regression line
slope, intercept, r_value, p_value, std_err = stats.linregress(upvotes, downvotes)
line = slope * np.array(upvotes) + intercept
plt.plot(upvotes, line, 'r', label=f'y={slope:.2f}x+{intercept:.2f}')

plt.xlabel('Upvotes')
plt.ylabel('Downvotes')
plt.title('Upvotes vs Downvotes')
plt.text(0.05, 0.95, f'r={r_value:.3f}, p={p_value}, std_err={std_err}', transform=plt.gca().transAxes, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
plt.legend()
plt.grid(True)
plt.savefig('graphs/posts/upvotes_vs_downvotes.png')


# Reddit Post Scores vs Sentiment Compound Scores
scores = [post.score for post in posts]
sentiment_compound_scores = [post.sentiment_analysis_compoundscore for post in posts]

plt.figure(figsize=(10, 6))
plt.scatter(sentiment_compound_scores, scores, alpha=0.6)

plt.xlabel('Sentiment Compound Scores')
plt.ylabel('Reddit Post Scores')
plt.title('Sentiment Compound Scores vs Reddit Post Scores')
plt.legend()
plt.grid(True)
plt.savefig('graphs/posts/sentiment_compound_scores_vs_reddit_post_scores.png')

# Downvotes vs Sentiment Negative Scores
sentiment_negative_scores = [post.sentiment_analysis_negativescore for post in posts]
plt.figure(figsize=(10, 6))
plt.scatter(sentiment_negative_scores, downvotes, alpha=0.6)
plt.xlabel('Sentiment Negative Scores')
plt.ylabel('Downvotes')
plt.title('Sentiment Negative Scores vs Downvotes')
plt.legend()
plt.grid(True)
plt.savefig('graphs/posts/sentiment_negative_scores_vs_downvotes.png')

# Upvotes vs Sentiment Positive Scores
sentiment_positive_scores = [post.sentiment_analysis_positivescore for post in posts]
plt.figure(figsize=(10, 6))
plt.scatter(sentiment_positive_scores, upvotes, alpha=0.6)
plt.xlabel('Sentiment Positive Scores')
plt.ylabel('Upvotes')
plt.title('Sentiment Positive Scores vs Upvotes')
plt.legend()
plt.grid(True)
plt.savefig('graphs/posts/sentiment_positive_scores_vs_upvotes.png')

# Reddit Post Scores vs Number of Comments
num_comments = [post.num_comments for post in posts]
plt.figure(figsize=(10, 6))
plt.scatter(num_comments, scores, alpha=0.6)
plt.xlabel('Number of Comments')
plt.ylabel('Reddit Post Scores')
plt.title('Number of Comments vs Reddit Post Scores')
plt.legend()
plt.grid(True)
plt.savefig('graphs/posts/number_of_comments_vs_reddit_post_scores.png')

# Positive Posts vs Upvotes
positive_posts = [post for post in posts if post.sentiment_analysis_positivescore > post.sentiment_analysis_negativescore]
positive_upvotes = [post.upvotes for post in positive_posts]
positive_posts_sentiment_scores = [post.sentiment_analysis_positivescore for post in positive_posts]

plt.figure(figsize=(10, 6))
plt.scatter(positive_posts_sentiment_scores, positive_upvotes, alpha=0.6)
plt.xlabel('Positive Posts')
plt.ylabel('Upvotes')
plt.title('Positive Posts vs Upvotes')
plt.legend()
plt.grid(True)
plt.savefig('graphs/posts/positive_posts_vs_upvotes.png')

# Negative Posts vs Downvotes
negative_posts = [post for post in posts if post.sentiment_analysis_negativescore >  post.sentiment_analysis_positivescore]
negative_downvotes = [post.downvotes for post in negative_posts]
negative_posts_sentiment_scores = [post.sentiment_analysis_negativescore for post in negative_posts]

plt.figure(figsize=(10, 6))
plt.scatter(negative_posts_sentiment_scores, negative_downvotes, alpha=0.6)
plt.xlabel('Negative Posts')
plt.ylabel('Downvotes')
plt.title('Negative Posts vs Downvotes')
plt.legend()
plt.grid(True)
plt.savefig('graphs/posts/negative_posts_vs_downvotes.png')

# Combined Sentiment vs Post Score
plt.figure(figsize=(12, 8))

# Create negative sentiment scores as negative values for left side
negative_sentiment_for_plot = [-score for score in sentiment_negative_scores]

# Get neutral sentiment scores
sentiment_neutral_scores = [post.sentiment_analysis_neutralscore for post in posts]

# Plot negative sentiment on left side
plt.scatter(negative_sentiment_for_plot, scores, alpha=0.6, color='red', label='Negative Sentiment')

# Plot positive sentiment on right side
plt.scatter(sentiment_positive_scores, scores, alpha=0.6, color='green', label='Positive Sentiment')

# Plot neutral sentiment at center (x=0)
neutral_x_values = [0] * len(sentiment_neutral_scores)
plt.scatter(neutral_x_values, scores, alpha=0.6, color='orange', label='Neutral Sentiment')

plt.xlabel('Sentiment Scores (Negative ← → Positive)')
plt.ylabel('Post Scores')
plt.title('Negative, Neutral, and Positive Sentiment vs Post Scores')
plt.axvline(x=0, color='black', linestyle='-', alpha=0.3)
plt.legend()
plt.grid(True)
plt.savefig('graphs/posts/combined_sentiment_vs_post_scores.png')
