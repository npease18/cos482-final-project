import pickle
import sqlite3
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
import re
import sys
import os

class SentimentPostGenerator:
    def __init__(self):
        self.vectorizer = None
        self.model = None
        self.posts_df = None
        
    def preprocess_text(self, text):
        """Clean and preprocess text data"""
        text = str(text).lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def load_data_from_db(self, db_path='reddit_data.db', data_type='posts'):
        """Load Reddit data with sentiment scores from database"""
        try:
            conn = sqlite3.connect(db_path)
            
            if data_type == 'posts':
                query = """
                SELECT 
                    p.id,
                    p.title,
                    p.content,
                    p.score as reddit_score,
                    p.upvotes,
                    p.downvotes,
                    p.num_comments,
                    s.negative_score,
                    s.neutral_score,
                    s.positive_score,
                    s.compound_score
                FROM posts p 
                LEFT JOIN sentiment_analysis s 
                    ON s.entity_type = 'post' AND s.entity_id = p.id
                WHERE p.content IS NOT NULL AND p.content != ''
                """
            else:  # comments
                query = """
                SELECT 
                    c.id,
                    c.content,
                    c.score as reddit_score,
                    s.negative_score,
                    s.neutral_score,
                    s.positive_score,
                    s.compound_score
                FROM comments c 
                LEFT JOIN sentiment_analysis s 
                    ON s.entity_type = 'comment' AND s.entity_id = c.id
                WHERE c.content IS NOT NULL AND c.content != ''
                """
            
            self.posts_df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Filter out rows without sentiment analysis
            initial_count = len(self.posts_df)
            self.posts_df = self.posts_df.dropna(subset=['compound_score'])
            final_count = len(self.posts_df)
            
            print(f"Loaded {final_count} {data_type} with sentiment analysis (filtered from {initial_count} total)")
            return True
        except Exception as e:
            print(f"Error loading data from database: {e}")
            return False
    
    def generate_post_for_sentiment(self, target_sentiment, num_candidates=50, sentiment_column='compound_score'):
        """Generate a post example for a specific sentiment value"""
        if self.posts_df is None:
            return "No training data available"
        
        # Find posts with similar sentiment scores
        sentiment_diff = abs(self.posts_df[sentiment_column] - target_sentiment)
        closest_posts = self.posts_df.loc[sentiment_diff.nsmallest(num_candidates).index]
        
        if len(closest_posts) == 0:
            return "No posts found for the requested sentiment"
        
        # Select a random post from the closest matches
        selected_post = closest_posts.sample(n=1).iloc[0]
        
        # Get text content
        if 'title' in selected_post:
            text_content = f"{selected_post['title']} {selected_post['content']}"
        else:
            text_content = selected_post['content']
        
        return {
            'text_content': text_content,
            'actual_sentiment': selected_post[sentiment_column],
            'requested_sentiment': target_sentiment,
            'difference': abs(selected_post[sentiment_column] - target_sentiment),
            'reddit_score': selected_post.get('reddit_score', 'N/A'),
            'negative_score': selected_post.get('negative_score', 'N/A'),
            'positive_score': selected_post.get('positive_score', 'N/A')
        }
    
    def predict_sentiment(self, text):
        """Predict sentiment score for new text"""
        if self.model is None or self.vectorizer is None:
            return "Model not trained. Please train or load a model first."
        
        # Preprocess text
        processed_text = self.preprocess_text(text)
        
        # Vectorize
        text_vector = self.vectorizer.transform([processed_text])
        
        # Predict
        prediction = self.model.predict(text_vector)[0]
        
        return {
            'original_text': text,
            'predicted_sentiment': prediction,
            'sentiment_label': self.get_sentiment_label(prediction)
        }
    
    def get_sentiment_label(self, score):
        """Convert numeric sentiment score to label"""
        if score >= 0.5:
            return "Very Positive"
        elif score >= 0.1:
            return "Positive"
        elif score >= -0.1:
            return "Neutral"
        elif score >= -0.5:
            return "Negative"
        else:
            return "Very Negative"
    
    def load_model(self, model_path='models/posts_sentiment_model.pkl', vectorizer_path='models/posts_vectorizer.pkl'):
        """Load a pre-trained model and vectorizer"""
        try:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            with open(vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
            print("Model and vectorizer loaded successfully!")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

def main():
    generator = SentimentPostGenerator()
    
    # Load the trained model
    print("Loading trained model...")
    if not generator.load_model():
        print("Failed to load model. Please make sure the model files exist.")
        print("Run '6-train-model.py' first to train the model.")
        return
    
    # Load database data for post generation
    print("\nLoading database data for post generation...")
    generator.load_data_from_db(data_type='posts')
    
    print("\n" + "="*50)
    print("SENTIMENT-BASED POST GENERATOR")
    print("="*50)
    print("Enter a target sentiment value to get example posts")
    print("Sentiment range: -1.0 (very negative) to 1.0 (very positive)")
    print("Or enter text to predict its sentiment")
    print("Type 'quit' to exit")
    print("="*50)
    
    while True:
        choice = input("\nChoose action:\n1. Generate post for sentiment\n2. Predict sentiment of text\n3. Quit\nEnter choice (1/2/3): ").strip()
        
        if choice == '3' or choice.lower() == 'quit':
            print("Goodbye!")
            break
        
        elif choice == '1':
            # Generate post for sentiment
            try:
                target_sentiment = float(input("Enter target sentiment (-1.0 to 1.0): "))
                if target_sentiment < -1.0 or target_sentiment > 1.0:
                    print("Please enter a value between -1.0 and 1.0")
                    continue
                
                print(f"\nFinding posts with sentiment close to {target_sentiment}...")
                result = generator.generate_post_for_sentiment(target_sentiment)
                
                if isinstance(result, dict):
                    print(f"\n✓ Found example post:")
                    print(f"Text: {result['text_content'][:300]}{'...' if len(result['text_content']) > 300 else ''}")
                    print(f"Actual sentiment: {result['actual_sentiment']:.3f}")
                    print(f"Target sentiment: {result['requested_sentiment']:.3f}")
                    print(f"Difference: {result['difference']:.3f}")
                    print(f"Reddit score: {result['reddit_score']}")
                    print(f"Positive score: {result['positive_score']:.3f}" if result['positive_score'] != 'N/A' else "Positive score: N/A")
                    print(f"Negative score: {result['negative_score']:.3f}" if result['negative_score'] != 'N/A' else "Negative score: N/A")
                else:
                    print(f"✗ {result}")
                    
            except ValueError:
                print("Please enter a valid number")
                
        elif choice == '2':
            # Predict sentiment
            text = input("Enter text to analyze: ").strip()
            if text:
                result = generator.predict_sentiment(text)
                if isinstance(result, dict):
                    print(f"\n✓ Sentiment Analysis:")
                    print(f"Text: {result['original_text'][:200]}{'...' if len(result['original_text']) > 200 else ''}")
                    print(f"Predicted sentiment: {result['predicted_sentiment']:.3f}")
                    print(f"Sentiment label: {result['sentiment_label']}")
                else:
                    print(f"✗ {result}")
            else:
                print("Please enter some text to analyze")
        
        else:
            print("Please enter 1, 2, or 3")

if __name__ == "__main__":
    main()