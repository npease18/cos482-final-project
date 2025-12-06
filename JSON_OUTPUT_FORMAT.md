# Reddit Scraper JSON Output Format Documentation

## 📋 Overview

This document describes the complete JSON output format for the Enhanced Reddit Scraper, which collects posts and their associated comments from the top 1000 trending subreddits over the past week.

## 🏗️ Top-Level Structure

The JSON file contains a dictionary where:
- **Keys**: Subreddit names (e.g., `"r/technology"`, `"r/worldnews"`)
- **Values**: Arrays of post objects

```json
{
  "r/subreddit_name": [
    {post_object_1},
    {post_object_2},
    ...
  ],
  "r/another_subreddit": [
    {post_object_3},
    ...
  ]
}
```

## 📝 Post Object Structure

Each post object contains the following fields:

### **Core Post Information**
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Reddit post ID | `"1pdvin3"` |
| `title` | string | Post title | `"TIL about machine learning"` |
| `subreddit` | string | Subreddit name (without r/) | `"todayilearned"` |
| `selftext` | string | Post content text | `"Today I learned that..."` |
| `permalink` | string | Full Reddit URL to the post | `"https://www.reddit.com/r/todayilearned/..."` |
| `author` | string | Reddit username of post author | `"example_user"` |
| `url` | string | External URL (if link post) | `"https://example.com/article"` |

### **Engagement Metrics**
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `upvotes` | integer | Calculated upvote count | `4230` |
| `downvotes` | integer | Calculated downvote count | `677` |
| `score` | integer | Net score (upvotes - downvotes) | `3553` |
| `upvote_ratio` | float | Ratio of upvotes (0.0-1.0) | `0.84` |
| `num_comments` | integer | Total comment count | `143` |

### **Metadata**
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `created_datetime` | string | ISO format creation timestamp | `"2025-12-04T09:15:51"` |
| `flair_text` | string | Post flair/tag | `"Economics"` |
| `is_video` | boolean | Whether post is a video | `false` |
| `over_18` | boolean | NSFW flag (always false due to filtering) | `false` |

### **Comments Data**
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `comments` | array | Array of comment objects | `[{comment1}, {comment2}]` |
| `comments_fetched` | integer | Number of comments actually retrieved | `25` |

## 💬 Comment Object Structure

Each comment object in the `comments` array contains:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Reddit comment ID | `"abc123"` |
| `author` | string | Comment author username | `"commenter_user"` |
| `body` | string | Comment text content | `"Great article! I learned..."` |
| `score` | integer | Comment score (net upvotes) | `42` |
| `created_datetime` | string | ISO format creation timestamp | `"2025-12-04T10:30:15"` |
| `parent_id` | string | ID of parent comment/post | `"t1_xyz789"` |
| `depth` | integer | Nesting level (0=top-level, 1=reply, etc.) | `1` |
| `is_submitter` | boolean | Whether commenter is the post author | `false` |
| `stickied` | boolean | Whether comment is pinned by moderators | `false` |
| `edited` | boolean | Whether comment has been edited | `true` |

## 📊 Complete Example

```json
{
  "r/technology": [
    {
      "id": "1pdvin3",
      "title": "Breakthrough in quantum computing announced by researchers",
      "subreddit": "technology", 
      "selftext": "Scientists at MIT have achieved a major breakthrough in quantum error correction...",
      "permalink": "https://www.reddit.com/r/technology/comments/1pdvin3/breakthrough_in_quantum_computing/",
      "upvotes": 4230,
      "downvotes": 677,
      "score": 3553,
      "upvote_ratio": 0.84,
      "num_comments": 143,
      "created_datetime": "2025-12-04T09:15:51",
      "flair_text": "Research",
      "author": "science_enthusiast",
      "url": "https://news.mit.edu/quantum-breakthrough",
      "is_video": false,
      "over_18": false,
      "comments": [
        {
          "id": "abc123",
          "author": "quantum_expert",
          "body": "This is huge! The implications for cryptography are massive.",
          "score": 89,
          "created_datetime": "2025-12-04T09:45:22",
          "parent_id": "t3_1pdvin3",
          "depth": 0,
          "is_submitter": false,
          "stickied": false,
          "edited": false
        },
        {
          "id": "def456", 
          "author": "crypto_analyst",
          "body": "Agreed! This could make current encryption obsolete within a decade.",
          "score": 34,
          "created_datetime": "2025-12-04T10:12:05",
          "parent_id": "t1_abc123",
          "depth": 1,
          "is_submitter": false,
          "stickied": false,
          "edited": true
        }
      ],
      "comments_fetched": 2
    }
  ],
  "r/worldnews": [
    {
      "id": "2efghi9",
      "title": "Major climate summit reaches historic agreement",
      "subreddit": "worldnews",
      "selftext": "",
      "permalink": "https://www.reddit.com/r/worldnews/comments/2efghi9/climate_summit_agreement/",
      "upvotes": 8945,
      "downvotes": 1203,
      "score": 7742,
      "upvote_ratio": 0.88,
      "num_comments": 567,
      "created_datetime": "2025-12-03T14:22:18",
      "flair_text": "Climate",
      "author": "news_reporter",
      "url": "https://reuters.com/climate-summit-2025",
      "is_video": false,
      "over_18": false,
      "comments": [
        {
          "id": "ghi789",
          "author": "climate_scientist",
          "body": "Finally, some real progress on carbon reduction targets!",
          "score": 156,
          "created_datetime": "2025-12-03T15:05:33",
          "parent_id": "t3_2efghi9",
          "depth": 0,
          "is_submitter": false,
          "stickied": false,
          "edited": false
        }
      ],
      "comments_fetched": 1
    }
  ]
}
```

## 🔧 Technical Details

### **Date Filtering**
- All posts are from the past 7 days relative to when the script was run
- Timestamps are in ISO 8601 format (UTC timezone)

### **Content Filtering**
- NSFW content is completely excluded (`over_18` will always be `false`)
- Stickied/pinned posts are filtered out
- Rules and announcement posts are excluded
- Media-only posts with minimal text are filtered out

### **Comment Limitations**
- Maximum comment depth: 3 levels (to prevent excessive nesting)
- Deleted comments and AutoModerator comments are excluded
- Comments are fetched with rate limiting to respect Reddit's API

### **Rate Limiting Impact**
- Due to rate limiting, not all comments may be fetched for posts with many comments
- The `comments_fetched` count shows actual retrieved comments vs `num_comments` (total available)

### **File Naming Convention**
```
reddit_trending_1000_past_week_YYYYMMDD_HHMMSS.json
```

Example: `reddit_trending_1000_past_week_20251204_143025.json`

## 📈 Statistics

When the scraper completes, it provides:
- **Total subreddits processed**: Number of subreddits with posts found
- **Total posts from past week**: Number of individual posts collected
- **Total comments fetched**: Total number of comments retrieved across all posts

This comprehensive dataset provides both the original post content and community discussion, making it ideal for analysis of Reddit trends, sentiment, and engagement patterns.