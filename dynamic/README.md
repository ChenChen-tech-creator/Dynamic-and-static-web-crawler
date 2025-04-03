# Zhihu Hot Questions Scraper

A tool to scrape and store hot questions from Zhihu's creator hot question page.

## Features

- Scrapes hot questions from Zhihu using Playwright
- Handles login via cookies
- Navigates dynamic (infinite scroll) content
- Stores questions in SQLite database with deduplication
- Provides a web interface for viewing data
- Configurable scraping settings

## Installation

1. Clone the repository
2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:

```bash
python -m playwright install
```

## Usage

### Setting Cookies

Since the Zhihu hot questions page requires login, you need to provide cookies from a logged-in browser session:

```bash
python run.py save-cookies "your_cookies_string_here"
```

The cookies you provided in the requirements should look like:

```
HMACCOUNT_BFESS=CEC66825D505A816; BDUSS_BFESS=U5c2djZmxDMm41NVJNdDY4ODR-M0Nhc1ZQVzJ-MlNrMS1WODJVfkkxdG9BMU5uSUFBQUFBJCQAAAAAAAAAAAEAAAARg9-nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGh2K2doditnOW; BAIDUID_BFESS=63BAF2FD70C4B2310A6BE81E8A25A940:FG=1; ZFY=xtQKJqMu4XM3gjuHzhTK6Iqxfd:AELVajZGwUuq1fMLc:C; ...
```

### Running the Web Interface

To start the web interface:

```bash
python run.py run-server
```

Then open http://localhost:8000 in your browser.

### Running Once

To run the scraper once without the web interface:

```bash
python run.py run-once
```

### Running the Scheduler

To run the scheduler in the foreground:

```bash
python run.py run-scheduler
```

You can specify custom intervals and limits:

```bash
python run.py run-scheduler --interval 30 --limit 50
```

## Configuration

You can configure the following settings through the web interface:

- **Scrape Interval**: Time between scraping jobs (minutes)
- **Question Limit**: Maximum number of questions to scrape per run
- **Headless Mode**: Whether to run the browser in headless mode

## Structure

- `app/config`: Configuration settings
- `app/database`: Database models and storage
- `app/scraper`: Zhihu scraper implementation
- `app/scheduler`: Scheduling logic
- `app/frontend`: Web interface
- `app/main.py`: Main application code

## Notes

- This is an MVP implementation, focusing on core functionality
- The application requires valid Zhihu cookies to access the hot questions page
- Data is stored in SQLite by default for simplicity 