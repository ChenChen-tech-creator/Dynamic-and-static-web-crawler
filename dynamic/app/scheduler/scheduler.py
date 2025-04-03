"""
Scheduler for running scraper at intervals
"""
import asyncio
import time
import datetime
import threading
from typing import Callable, Any, Optional
import traceback

from app.config.settings import settings
from app.database.models import QuestionDatabase
from app.scraper.zhihu_scraper import scrape_questions


class ScraperScheduler:
    """Scheduler for running the Zhihu scraper at regular intervals"""
    
    def __init__(self, 
                 interval_minutes: int = None,
                 question_limit: int = None,
                 database_path: str = None):
        """Initialize the scheduler"""
        self.interval_minutes = interval_minutes or settings.scrape_interval
        self.question_limit = question_limit or settings.question_limit
        self.database_path = database_path or settings.database_path
        self.running = False
        self.last_run = None
        self.thread = None
        self.db = QuestionDatabase(self.database_path)
    
    def start(self):
        """Start the scheduler in a separate thread"""
        if self.running:
            print("Scheduler is already running")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        return True
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=30)
            self.thread = None
    
    def _run_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                print(f"Running scheduled scraping at {datetime.datetime.now()}")
                
                # Run the scraper
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                questions = loop.run_until_complete(
                    scrape_questions(limit=self.question_limit, headless=settings.headless)
                )
                
                # Save to database
                if questions:
                    saved_count = self.db.add_questions(questions)
                    print(f"Saved {saved_count} questions to database")
                else:
                    print("No questions were scraped")
                
                self.last_run = datetime.datetime.now()
                loop.close()
            except Exception as e:
                print(f"Error in scheduler: {e}")
            
            # Sleep until next run
            next_run = datetime.datetime.now() + datetime.timedelta(minutes=self.interval_minutes)
            print(f"Next run scheduled for {next_run}")
            
            # Check if should stop every 5 seconds
            for _ in range(self.interval_minutes * 60 // 5):
                if not self.running:
                    break
                time.sleep(5)
    
    def run_once(self):
        """Run the scraper once immediately"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            questions = loop.run_until_complete(
                scrape_questions(limit=self.question_limit, headless=settings.headless)
            )
            
            if questions:
                saved_count = self.db.add_questions(questions)
                print(f"Saved {saved_count} questions to database")
            else:
                print("No questions were scraped")
            
            self.last_run = datetime.datetime.now()
            loop.close()
            return len(questions)
        except Exception as e:
            print(f"Error in manual run: {e}")
            return 0 

async def manual_run():
    """手动运行一次爬虫任务"""
    try:
        print("开始手动运行爬虫...")
        questions = await scrape_questions(limit=settings.question_limit, headless=settings.headless)
        
        if questions:
            # 保存到数据库
            db = QuestionDatabase(settings.database_path)
            saved_count = db.add_questions(questions)
            print(f"爬取成功，采集了 {len(questions)} 个问题，保存了 {saved_count} 个问题。")
            return len(questions)
        else:
            print("爬取结束，未采集到问题。")
            return 0
    except Exception as e:
        print(f"手动爬取出错: {e}")
        traceback.print_exc()
        return 0 