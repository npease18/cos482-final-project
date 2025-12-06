-- Schema for Reddit data storage

-- Table for subreddits
CREATE TABLE subreddits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for posts
CREATE TABLE posts (
    id TEXT PRIMARY KEY,  -- Reddit post ID
    subreddit_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    author TEXT,
    score INTEGER DEFAULT 0,
    num_comments INTEGER DEFAULT 0,
    created_utc INTEGER,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subreddit_id) REFERENCES subreddits(id)
);

-- Table for comments
CREATE TABLE comments (
    id TEXT PRIMARY KEY,  -- Reddit comment ID
    post_id TEXT NOT NULL,
    parent_id TEXT,  -- NULL for top-level comments, comment ID for replies
    author TEXT,
    content TEXT NOT NULL,
    score INTEGER DEFAULT 0,
    created_utc INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

-- Indexes for better query performance
CREATE INDEX idx_posts_subreddit ON posts(subreddit_id);
CREATE INDEX idx_posts_created_utc ON posts(created_utc);
CREATE INDEX idx_comments_post ON comments(post_id);
CREATE INDEX idx_comments_parent ON comments(parent_id);
CREATE INDEX idx_comments_created_utc ON comments(created_utc);