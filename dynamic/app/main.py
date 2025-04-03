"""
知乎热点问题爬虫主脚本
"""
import os
import sys
import argparse
import asyncio

from app.config.settings import settings
from app.database.models import QuestionDatabase
from app.scraper.zhihu_scraper import scrape_questions
from app.scheduler.scheduler import ScraperScheduler
from app.frontend.server import start_server


def save_cookies_from_string(cookies_str):
    """从字符串保存 cookies 到文件"""
    success = settings.save_cookies(cookies_str)
    if success:
        print("Cookies 保存成功。")
    else:
        print("Cookies 保存失败。")
    return success


def run_once():
    """运行一次爬虫并退出"""
    print("正在运行爬虫...")
    db = QuestionDatabase(settings.database_path)
    
    # 在事件循环中运行爬虫
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    questions = loop.run_until_complete(
        scrape_questions(limit=settings.question_limit, headless=settings.headless)
    )
    loop.close()
    
    if questions:
        saved_count = db.add_questions(questions)
        print(f"已保存 {saved_count} 个问题到数据库。")
    else:
        print("未爬取到任何问题。")
    
    return len(questions)


def run_scheduler():
    """在前台运行调度器"""
    print("正在启动调度器...")
    scheduler = ScraperScheduler(
        interval_minutes=settings.scrape_interval,
        question_limit=settings.question_limit
    )
    
    try:
        scheduler.start()
        print(f"调度器已启动。每 {settings.scrape_interval} 分钟爬取一次。")
        print("按 Ctrl+C 停止。")
        
        # 保持主线程运行
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止调度器...")
        scheduler.stop()
        print("调度器已停止。")


def run_server(host="0.0.0.0", port=8000):
    """运行网络服务器"""
    print(f"正在启动网络服务器，地址：{host}:{port}...")
    start_server(host=host, port=port)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="知乎热点问题爬虫")
    
    # 设置子解析器
    subparsers = parser.add_subparsers(dest="command", help="要运行的命令")
    
    # save-cookies 命令
    cookies_parser = subparsers.add_parser("save-cookies", help="保存 cookies")
    cookies_parser.add_argument("cookies", help="从浏览器获取的 cookies 字符串")
    
    # run-once 命令
    subparsers.add_parser("run-once", help="运行一次爬虫并退出")
    
    # run-scheduler 命令
    scheduler_parser = subparsers.add_parser("run-scheduler", help="在前台运行调度器")
    scheduler_parser.add_argument("--interval", type=int, help="爬取间隔（分钟）")
    scheduler_parser.add_argument("--limit", type=int, help="爬取问题数量限制")
    
    # run-server 命令
    server_parser = subparsers.add_parser("run-server", help="运行网络服务器")
    server_parser.add_argument("--host", type=str, default="0.0.0.0", help="绑定的主机地址")
    server_parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    
    # 解析参数
    args = parser.parse_args()
    
    # 处理命令
    if args.command == "save-cookies":
        save_cookies_from_string(args.cookies)
    
    elif args.command == "run-once":
        run_once()
    
    elif args.command == "run-scheduler":
        # Override settings if provided
        if args.interval:
            settings.scrape_interval = args.interval
        if args.limit:
            settings.question_limit = args.limit
        
        run_scheduler()
    
    elif args.command == "run-server":
        run_server(host=args.host, port=args.port)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 