import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import pickle
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import sqlite3

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class SentimentPostGenerator:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
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
    
    def train_model(self, target_column='compound_score'):
        """Train the sentiment prediction model"""
        if self.posts_df is None:
            print("No data loaded. Please load data first.")
            return False
            
        # Combine title and content for posts, or just use content for comments
        if 'title' in self.posts_df.columns:
            # For posts: combine title and content
            text_data = (self.posts_df['title'].fillna('') + ' ' + 
                        self.posts_df['content'].fillna('')).apply(self.preprocess_text)
        else:
            # For comments: just use content
            text_data = self.posts_df['content'].fillna('').apply(self.preprocess_text)
        
        # Remove empty texts
        valid_indices = text_data.str.len() > 0
        text_data = text_data[valid_indices]
        target_data = self.posts_df[target_column][valid_indices]
        
        print(f"Training on {len(text_data)} samples")
        
        # Vectorize text
        X = self.vectorizer.fit_transform(text_data)
        y = target_data
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"Model trained successfully!")
        print(f"MSE: {mse:.4f}")
        print(f"R² Score: {r2:.4f}")
        print(f"Target range: {y.min():.3f} to {y.max():.3f}")
        
        return True
    
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

    def save_model(self, model_path='sentiment_model.pkl', vectorizer_path='vectorizer.pkl'):
        """Save the trained model and vectorizer"""
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        with open(vectorizer_path, 'wb') as f:
            pickle.dump(self.vectorizer, f)
        print("Model and vectorizer saved successfully!")
    
    def load_model(self, model_path='sentiment_model.pkl', vectorizer_path='vectorizer.pkl'):
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

# Example usage
if __name__ == "__main__":
    generator = SentimentPostGenerator()
    
    # Load data from database
    print("Loading posts data from database...")
    if generator.load_data_from_db(data_type='posts'):
        # Train the model
        print("\nTraining model on posts data...")
        if generator.train_model():
            # Save the model
            generator.save_model('posts_sentiment_model.pkl', 'posts_vectorizer.pkl')
            
            # Generate example for different sentiment levels
            print("\n=== Example Posts for Different Sentiment Levels ===")
            for sentiment_level, description in [(0.8, "Very Positive"), (0.2, "Slightly Positive"), 
                                                (0.0, "Neutral"), (-0.2, "Slightly Negative"), 
                                                (-0.8, "Very Negative")]:
                result = generator.generate_post_for_sentiment(sentiment_level)
                print(f"\n{description} (target: {sentiment_level}):")
                if isinstance(result, dict):
                    print(f"Text: {result['text_content'][:200]}...")
                    print(f"Actual sentiment: {result['actual_sentiment']:.3f}")
                    print(f"Reddit score: {result['reddit_score']}")
                else:
                    print(result)
    
    # Also train on comments data
    print("\n" + "="*50)
    print("Loading comments data from database...")
    generator_comments = SentimentPostGenerator()
    if generator_comments.load_data_from_db(data_type='comments'):
        print("\nTraining model on comments data...")
        if generator_comments.train_model():
            generator_comments.save_model('comments_sentiment_model.pkl', 'comments_vectorizer.pkl')
            
            # Generate example comments
            print("\n=== Example Comments for Different Sentiment Levels ===")
            result = generator_comments.generate_post_for_sentiment(0.6)
            print(f"Positive comment example:")
            if isinstance(result, dict):
                print(f"Text: {result['text_content'][:200]}...")
                print(f"Actual sentiment: {result['actual_sentiment']:.3f}")
            else:
                print(result)