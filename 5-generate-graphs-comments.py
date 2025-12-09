import sqlite3
import numpy as np
from scipy import stats

import matplotlib.pyplot as plt

class ExtendedComments:
    def __init__(self, comment_from_db):
        self.id = comment_from_db[0]
        self.post_id = comment_from_db[1]
        self.parent_id = comment_from_db[2]
        self.author = comment_from_db[3]
        self.content = comment_from_db[4]
        self.score = comment_from_db[5]
        self.sentiment_analysis_negativescore = comment_from_db[11]
        self.sentiment_analysis_neutralscore = comment_from_db[12]
        self.sentiment_analysis_positivescore = comment_from_db[13]
        self.sentiment_analysis_compoundscore = comment_from_db[14]


# Connect to the database
conn = sqlite3.connect('reddit_data.db')
cursor = conn.cursor()

# Query to get extended comment data
cursor.execute("""
            SELECT * FROM comments
            LEFT JOIN sentiment_analysis
                ON sentiment_analysis.entity_type = "comment"
                AND sentiment_analysis.entity_id = comments.id
""")
data = cursor.fetchall()
conn.close()

comments = [ExtendedComments(row) for row in data]

# Note: Comments don't have upvotes/downvotes separately in Reddit data
# So we'll create a distribution analysis of comment scores instead

scores = [comment.score for comment in comments]
sentiment_compound_scores = [comment.sentiment_analysis_compoundscore for comment in comments]

# Comment Score Distribution
plt.figure(figsize=(10, 6))
plt.hist(scores, bins=50, alpha=0.7)
plt.xlabel('Comment Scores')
plt.ylabel('Frequency')
plt.title('Distribution of Comment Scores')
plt.grid(True)
plt.savefig('graphs/comments/comment_score_distribution.png')

# Reddit Comment Scores vs Sentiment Compound Scores
plt.figure(figsize=(10, 6))
plt.scatter(sentiment_compound_scores, scores, alpha=0.6)

# Add regression line
slope, intercept, r_value, p_value, std_err = stats.linregress(sentiment_compound_scores, scores)
line = slope * np.array(sentiment_compound_scores) + intercept
plt.plot(sentiment_compound_scores, line, 'r', label=f'y={slope:.2f}x+{intercept:.2f}')

plt.xlabel('Sentiment Compound Scores')
plt.ylabel('Reddit Comment Scores')
plt.title('Sentiment Compound Scores vs Reddit Comment Scores')
plt.text(0.05, 0.95, f'r={r_value:.3f}, p={p_value:.3f}', transform=plt.gca().transAxes, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
plt.legend()
plt.grid(True)
plt.savefig('graphs/comments/sentiment_compound_scores_vs_reddit_comment_scores.png')

# Comment Score vs Sentiment Negative Scores
sentiment_negative_scores = [comment.sentiment_analysis_negativescore for comment in comments]
plt.figure(figsize=(10, 6))
plt.scatter(sentiment_negative_scores, scores, alpha=0.6)
plt.xlabel('Sentiment Negative Scores')
plt.ylabel('Comment Scores')
plt.title('Sentiment Negative Scores vs Comment Scores')
plt.grid(True)
plt.savefig('graphs/comments/sentiment_negative_scores_vs_comment_scores.png')

# Comment Score vs Sentiment Positive Scores
sentiment_positive_scores = [comment.sentiment_analysis_positivescore for comment in comments]
plt.figure(figsize=(10, 6))
plt.scatter(sentiment_positive_scores, scores, alpha=0.6)
plt.xlabel('Sentiment Positive Scores')
plt.ylabel('Comment Scores')
plt.title('Sentiment Positive Scores vs Comment Scores')
plt.grid(True)
plt.savefig('graphs/comments/sentiment_positive_scores_vs_comment_scores.png')

# Content Length vs Comment Scores
content_lengths = [len(comment.content) if comment.content else 0 for comment in comments]
plt.figure(figsize=(10, 6))
plt.scatter(content_lengths, scores, alpha=0.6)
plt.xlabel('Comment Length (characters)')
plt.ylabel('Comment Scores')
plt.title('Comment Length vs Comment Scores')
plt.grid(True)
plt.savefig('graphs/comments/comment_length_vs_comment_scores.png')

# Positive Comments vs Scores
positive_comments = [comment for comment in comments if comment.sentiment_analysis_positivescore > 0]
positive_comment_scores = [comment.score for comment in positive_comments]
positive_comment_sentiment_scores = [comment.sentiment_analysis_positivescore for comment in positive_comments]

plt.figure(figsize=(10, 6))
plt.scatter(positive_comment_sentiment_scores, positive_comment_scores, alpha=0.6)
plt.xlabel('Positive Sentiment Scores')
plt.ylabel('Comment Scores')
plt.title('Positive Sentiment vs Comment Scores')
plt.grid(True)
plt.savefig('graphs/comments/positive_sentiment_vs_comment_scores.png')

# Negative Comments vs Scores
negative_comments = [comment for comment in comments if comment.sentiment_analysis_negativescore > 0]
negative_comment_scores = [comment.score for comment in negative_comments]
negative_comment_sentiment_scores = [comment.sentiment_analysis_negativescore for comment in negative_comments]

plt.figure(figsize=(10, 6))
plt.scatter(negative_comment_sentiment_scores, negative_comment_scores, alpha=0.6)
plt.xlabel('Negative Sentiment Scores')
plt.ylabel('Comment Scores')
plt.title('Negative Sentiment vs Comment Scores')
plt.grid(True)
plt.savefig('graphs/comments/negative_sentiment_vs_comment_scores.png')

