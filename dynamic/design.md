# Zhihu Hot Questions Scraper - Design Document

## Overview
This project aims to periodically collect hot questions from Zhihu's creator hot question page (https://www.zhihu.com/creator/hot-question/hot/0/hour) and store them in a local database. It will include a simple frontend to view the collected data.

## Requirements
1. Scrape hot questions from Zhihu's creator dashboard
2. Handle authentication using Playwright with cookies
3. Navigate dynamic loading content (waterfall/infinite scroll)
4. Collect top 20 questions per scraping session
5. Store data with deduplication
6. Provide a simple frontend for data viewing
7. Make key parameters configurable

## System Architecture

### Components
1. **Scraper Module**
   - Uses Playwright for browser automation
   - Handles authentication via cookies
   - Manages page scrolling to load dynamic content
   - Extracts question data

2. **Database Module**
   - Stores scraped questions
   - Handles deduplication
   - Provides data access methods

3. **Config Module**
   - Manages cookies
   - Controls scraping frequency
   - Sets number of questions to collect

4. **Frontend**
   - Simple web interface to view collected data
   - Basic filtering and sorting capabilities

5. **Scheduler**
   - Runs scraping jobs at configured intervals

## Technical Details

### Data Model
```
Question {
  id: string            // Unique identifier from Zhihu
  title: string         // Question title
  url: string           // Full URL to the question
  answerCount: number   // Number of answers
  followCount: number   // Number of follows
  timestamp: datetime   // When this question was collected
  hotScore: number      // Optional, if available from source
}
```

### Scraping Process
1. Load cookies for authentication
2. Navigate to the hot questions page
3. Wait for initial content to load
4. Extract visible questions
5. Scroll down to load more content
6. Repeat extraction until at least 20 questions are collected
7. Process and store data with deduplication

### Technologies
- **Backend**: Python with FastAPI
- **Frontend**: Simple HTML/CSS/JS with a framework like Vue.js
- **Database**: SQLite for simplicity (can be upgraded to PostgreSQL later)
- **Automation**: Playwright for browser automation
- **Scheduling**: Simple cron jobs or Python's schedule library

## Implementation Plan (MVP)

### Phase 1: Core Scraper
- Set up Playwright with cookie-based authentication
- Implement scroll and extract logic
- Create basic data storage

### Phase 2: Configuration & Scheduling
- Implement configuration module
- Set up scheduled scraping

### Phase 3: Frontend
- Create simple web interface
- Implement basic data viewing capabilities

## Configuration Parameters
- `cookies_file`: Path to stored cookies
- `scrape_interval`: Time between scrapes (minutes)
- `question_limit`: Number of questions to collect (default: 20)
- `database_path`: Location of the SQLite database
- `headless`: Whether to run browser in headless mode

## Limitations & Future Improvements
- No sophisticated error handling in MVP
- Basic frontend with minimal features
- No analytics or trending analysis
- SQLite may need to be replaced for scaling
- Authentication method may need updates if Zhihu changes

This design focuses on creating a minimum viable product that satisfies the core requirements without overengineering the solution. 