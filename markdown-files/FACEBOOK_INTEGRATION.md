# Facebook Integration for Tunisia Intelligence

This document describes the Facebook integration that allows scraping posts from Tunisian government and institutional Facebook pages using the Meta Graph API.

## Overview

The Facebook integration consists of three main components:

1. **Facebook Extractor** (`extractors/facebook_extractor.py`) - Extracts posts, reactions, and comments from Facebook pages
2. **Facebook Loader** (`facebook_loader.py`) - Loads extracted data into the database
3. **Runner Script** (`run_facebook_scraper.py`) - Main execution script with CLI interface

## Database Schema

The integration uses three new database tables:

### social_media_posts
Stores the main post data:
- `id` - Primary key
- `social_media` - Platform name (always "facebook")
- `account` - Facebook page name
- `content` - Post message/story content
- `publish_date` - When the post was published
- `url` - Permalink to the post
- `content_type` - Type of post (status, photo, video, etc.)
- Other metadata fields

### social_media_post_reactions
Stores reaction counts by type:
- `post_id` - Foreign key to social_media_posts
- `reaction_type` - Type of reaction (like, love, haha, wow, sad, angry, care)
- `count` - Number of reactions of this type

### social_media_comments
Stores post comments:
- `id` - Primary key
- `post_id` - Foreign key to social_media_posts
- `content` - Comment text
- `comment_date` - When the comment was posted

## Setup Instructions

### 1. Install Dependencies

```bash
pip install facebook-sdk>=3.1.0
```

### 2. Configure Facebook App Token

Run the setup script to securely store your Facebook app token:

```bash
python setup_facebook_token.py
```

This will store your token using the existing secret management system.

### 3. Verify Database Tables

Ensure the required database tables exist in your Supabase instance. The tables should be created according to the schema provided in the user request.

### 4. Add Facebook Sources

Add Facebook pages to the `sources` table with:
- `source_type` = "facebook"
- `page_id` = Facebook page ID (from the page URL or API)
- `is_active` = true

## Usage

### Command Line Interface

```bash
# Run with default settings (24 hours back)
python run_facebook_scraper.py

# Specify custom time range
python run_facebook_scraper.py --hours-back 48

# Dry run (extract but don't save to database)
python run_facebook_scraper.py --dry-run

# Verbose logging
python run_facebook_scraper.py --verbose
```

### Programmatic Usage

```python
from facebook_loader import FacebookLoader

# Initialize loader
loader = FacebookLoader()

# Extract and load posts from past 24 hours
result = loader.extract_and_load_posts(hours_back=24)

print(f"Loaded {result['total_posts_loaded']} posts")
```

### Testing

Run the test suite to verify everything is working:

```bash
python test_facebook_integration.py
```

## Facebook Sources

The system is configured to work with the following Tunisian government and institutional Facebook pages:

### Government Institutions
- Présidence de la République (271178572940207)
- Présidence du Gouvernement (213636118651883)
- Parlement (1515094915436499)

### Ministries
- Ministère de la Justice (292899070774121)
- Ministère de la Défense nationale (516083015235303)
- Ministère de l'Intérieur (192600677433983)
- Ministère des Affaires étrangères (171454396234624)
- And many more...

### Regional Governments
- Gouvernorat de l'Ariana (840150059416004)
- Gouvernorat de Tataouine (1709134729325012)
- Gouvernorat de Zaghouan (539354309423084)
- And others...

## API Rate Limits

The Facebook Graph API has rate limits. The extractor includes:
- Delays between API calls (0.1-1 second)
- Error handling for rate limit responses
- Retry logic for failed requests

## Data Processing

### Content Extraction
- Combines post `message` and `story` fields
- Handles different post types (status, photo, video, link, etc.)
- Extracts permalink URLs for reference

### Reactions Processing
- Gets total reaction count
- Breaks down reactions by type (like, love, haha, wow, sad, angry, care)
- Only stores reaction types with count > 0

### Comments Processing
- Extracts comment text and metadata
- Includes comment author information (if available)
- Handles nested replies (limited depth)

## Error Handling

The system includes comprehensive error handling:
- Page-level errors (page not found, access denied)
- Post-level errors (malformed data, API issues)
- Database errors (connection issues, constraint violations)
- Rate limiting and timeout handling

## Monitoring and Logging

All operations are logged with appropriate levels:
- INFO: Normal operations and statistics
- WARNING: Non-critical issues (missing data, rate limits)
- ERROR: Critical failures that prevent processing

Logs are written to both console and `facebook_scraper.log` file.

## Integration with Existing System

The Facebook integration follows the same patterns as the existing RSS scraping system:

1. **Modular Design**: Separate extractor and loader components
2. **Database Integration**: Uses existing DatabaseManager and Supabase client
3. **Secret Management**: Leverages existing secret management system
4. **Logging**: Consistent logging patterns
5. **Error Handling**: Similar error handling and retry logic

## Scheduling

To run the Facebook scraper on a schedule, you can:

1. **Add to existing cron jobs**:
```bash
# Run every 6 hours
0 */6 * * * cd /path/to/tunisia_intelligence && python run_facebook_scraper.py
```

2. **Integrate with existing scheduler**: Add to your existing RSS scraping schedule

3. **Use system scheduler**: Windows Task Scheduler, systemd timers, etc.

## Performance Considerations

- **API Calls**: Each page requires multiple API calls (posts, reactions, comments)
- **Rate Limits**: Facebook limits requests per hour/day
- **Database Load**: Batch operations where possible
- **Memory Usage**: Processes pages sequentially to manage memory

## Troubleshooting

### Common Issues

1. **"Page not found"**: Check page_id in sources table
2. **"Access denied"**: Verify app token has Page Public Content Access
3. **"Rate limited"**: Reduce frequency or add delays
4. **"No sources found"**: Add Facebook sources to database

### Debug Mode

Enable verbose logging for detailed debugging:
```bash
python run_facebook_scraper.py --verbose
```

## Security Considerations

- App token is stored securely using the secret management system
- No user data is collected (only public posts)
- Respects Facebook's terms of service
- Implements rate limiting to be respectful of API limits

## Future Enhancements

Potential improvements:
1. **Sentiment Analysis**: Integrate with existing sentiment analysis
2. **Content Classification**: Categorize posts by topic
3. **Real-time Processing**: WebSocket or webhook integration
4. **Advanced Analytics**: Engagement metrics and trends
5. **Multi-language Support**: Enhanced Arabic/French text processing
