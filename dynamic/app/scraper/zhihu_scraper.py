"""
知乎热点问题爬虫（使用 Playwright）
"""
import re
import os
import json
import traceback
import asyncio
from typing import List, Dict, Any, Optional
import time
import random

from playwright.async_api import async_playwright, Page, TimeoutError

from app.database.models import Question
from app.config.settings import settings


class ZhihuScraper:
    """知乎热点问题爬虫"""
    
    def __init__(self, headless: bool = True):
        """初始化爬虫"""
        self.headless = headless
        self.browser = None
        self.page = None
        self.urls = [
            "https://www.zhihu.com/question/waiting",  # 等你来答
            "https://www.zhihu.com/hot",              # 热榜
            "https://www.zhihu.com",                  # 首页
            "https://www.zhihu.com/explore"           # 发现页
        ]
    
    async def initialize(self):
        """初始化浏览器"""
        try:
            print("正在初始化浏览器...")
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
            )
            
            # 创建一个新的浏览器上下文
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            
            # 修改webdriver检测
            await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            """)
            
            # 加载 cookies
            print(f"尝试从 {settings.cookies_file} 加载cookies")
            if os.path.exists(settings.cookies_file):
                try:
                    with open(settings.cookies_file, 'r', encoding='utf-8') as f:
                        cookies_data = json.load(f)
                    
                    if settings.debug:
                        print(f"cookies文件内容: {cookies_data}")
                    
                    # 格式化cookies，确保格式正确
                    cookies = []
                    for name, value in cookies_data.items():
                        cookies.append({
                            "name": name,
                            "value": value,
                            "domain": ".zhihu.com",
                            "path": "/"
                        })
                    
                    # 添加 cookies 到浏览器上下文
                    if cookies:
                        await context.add_cookies(cookies)
                        print(f"已加载 {len(cookies)} 个 cookies")
                    else:
                        print("警告: 没有有效的cookies可加载")
                except Exception as e:
                    print(f"加载 cookies 时出错: {e}")
                    traceback.print_exc()
            else:
                print(f"Cookie文件 {settings.cookies_file} 不存在")
            
            # 创建新页面
            self.page = await context.new_page()
            
            # 设置超时（增加超时时间）
            self.page.set_default_timeout(60000)  # 60秒
            print("浏览器初始化完成")
            
            return True
        except Exception as e:
            print(f"初始化浏览器时出错: {e}")
            traceback.print_exc()
            return False
    
    async def close(self):
        """关闭浏览器"""
        try:
            if self.browser:
                await self.browser.close()
                self.browser = None
                print("已关闭浏览器")
        except Exception as e:
            print(f"关闭浏览器时出错: {e}")
    
    async def scrape(self, limit: int = 20) -> List[Question]:
        """爬取知乎问题"""
        questions = []
        
        if not self.browser:
            success = await self.initialize()
            if not success:
                print("浏览器初始化失败，无法继续爬取")
                return []
        
        # 确保debug目录存在
        debug_dir = os.path.join(os.getcwd(), "debug")
        os.makedirs(debug_dir, exist_ok=True)
        
        try:
            # 尝试所有URL，直到找到问题
            for url in self.urls:
                print(f"尝试从 {url} 爬取问题...")
                page_questions = await self.extract_questions_from_url(url)
                
                if page_questions:
                    questions.extend(page_questions)
                    print(f"成功从 {url} 爬取到 {len(page_questions)} 个问题")
                    
                    # 如果已经获取足够的问题，就停止
                    if len(questions) >= limit:
                        break
            
            # 如果收集到的问题超过限制，截取到限制大小
            if len(questions) > limit:
                questions = questions[:limit]
            
            print(f"最终收集到 {len(questions)} 个问题")
            
            # 生成报告文件
            self.create_debug_report(questions, debug_dir)
            
        except Exception as e:
            print(f"爬取过程中发生错误: {e}")
            traceback.print_exc()
        
        return questions
    
    def create_debug_report(self, questions, debug_dir=None):
        """创建爬取结果报告"""
        try:
            # 如果没有提供debug_dir，使用默认路径
            if not debug_dir:
                debug_dir = os.path.join(os.getcwd(), "debug")
                os.makedirs(debug_dir, exist_ok=True)
                
            report_path = os.path.join(debug_dir, "scrape_report.txt")
            print(f"正在创建爬取报告: {report_path}")
            
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(f"爬取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"采集到问题数量: {len(questions)}\n\n")
                
                if questions:
                    f.write("问题列表:\n")
                    for i, q in enumerate(questions, 1):
                        f.write(f"{i}. ID: {q.id}\n")
                        f.write(f"   标题: {q.title}\n")
                        f.write(f"   链接: {q.url}\n")
                        f.write(f"   回答数: {q.answer_count}\n")
                        f.write(f"   关注数: {q.follow_count}\n\n")
                else:
                    f.write("未采集到任何问题\n")
                    
            print(f"爬取报告已保存到: {report_path}")
        except Exception as e:
            print(f"创建报告时出错: {e}")
            traceback.print_exc()
    
    async def extract_questions_from_url(self, url: str) -> List[Question]:
        """从指定URL提取问题"""
        questions = []
        
        try:
            print(f"导航到 {url}...")
            await self.page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 保存页面截图和源码用于调试
            if settings.debug:
                page_name = url.split('/')[-1] or 'home'
                await self.page.screenshot(path=os.path.join("debug", f"{page_name}.png"))
                
                # 保存HTML源码
                page_content = await self.page.content()
                with open(os.path.join("debug", f"{page_name}.html"), "w", encoding="utf-8") as f:
                    f.write(page_content)
            
            # 检查是否需要登录
            login_elements = await self.page.query_selector_all('.SignContainer-content, .Login-content, button:text("登录")')
            if login_elements:
                print(f"⚠️ 页面需要登录，cookies可能无效")
            
            # 滚动页面以加载更多内容
            await self.scroll_page()
            
            # 提取问题数据
            print(f"从 {url} 提取问题...")
            
            # 热榜页面的提取
            if 'hot' in url:
                questions.extend(await self.extract_hot_questions())
            
            # 默认提取方法 - 匹配所有包含/question/的链接
            if not questions:
                questions.extend(await self.extract_question_links())
            
            return questions
            
        except Exception as e:
            print(f"从 {url} 提取问题时出错: {e}")
            traceback.print_exc()
            # 出错时保存截图
            if settings.debug:
                try:
                    page_name = url.split('/')[-1] or 'home'
                    await self.page.screenshot(path=os.path.join("debug", f"error_{page_name}.png"))
                except Exception as screenshot_error:
                    print(f"保存错误截图时出错: {screenshot_error}")
                
            return []
    
    async def scroll_page(self, scroll_count=5):
        """滚动页面加载更多内容"""
        try:
            print("滚动页面加载更多内容...")
            for i in range(scroll_count):
                await self.page.evaluate("window.scrollBy(0, 800)")
                # 添加随机等待模拟真实用户
                await asyncio.sleep(random.uniform(1, 2))
        except Exception as e:
            print(f"滚动页面时出错: {e}")
    
    async def extract_hot_questions(self) -> List[Question]:
        """提取热榜问题"""
        try:
            question_data = await self.page.evaluate("""
            () => {
                const questions = [];
                const processed = new Set(); // 避免重复
                
                // 查找热榜项
                const hotItems = document.querySelectorAll('.HotItem');
                console.log(`找到 ${hotItems.length} 个热榜项`);
                
                if (hotItems.length > 0) {
                    hotItems.forEach(item => {
                        try {
                            // 提取标题和链接
                            const titleElement = item.querySelector('.HotItem-title');
                            if (!titleElement) return;
                            
                            const link = titleElement.querySelector('a');
                            if (!link) return;
                            
                            const href = link.getAttribute('href');
                            const title = link.textContent.trim();
                            
                            if (!href || !href.includes('/question/') || !title) return;
                            
                            // 提取问题ID
                            const idMatch = href.match(/\\/question\\/(\\d+)/);
                            if (!idMatch) return;
                            
                            const id = idMatch[1];
                            if (processed.has(id)) return;
                            processed.add(id);
                            
                            // 构建完整URL
                            const fullUrl = href.startsWith('http') ? href : "https://www.zhihu.com" + href;
                            
                            // 提取热度值
                            let heat = 0;
                            const heatText = item.querySelector('.HotItem-metrics');
                            if (heatText) {
                                const heatMatch = heatText.textContent.match(/(\\d+(?:\\.\\d+)?)[^\\d]*热度/);
                                if (heatMatch) {
                                    heat = parseFloat(heatMatch[1]);
                                }
                            }
                            
                            questions.push({
                                id,
                                title,
                                url: fullUrl,
                                answer_count: 0,
                                follow_count: heat || 0
                            });
                        } catch (e) {
                            console.error('提取热榜问题时出错:', e);
                        }
                    });
                }
                
                return questions;
            }
            """)
            
            # 转换为Question对象
            questions = []
            for data in question_data:
                question = Question(
                    id=data["id"],
                    title=data["title"],
                    url=data["url"],
                    answer_count=data.get("answer_count", 0),
                    follow_count=data.get("follow_count", 0)
                )
                questions.append(question)
            
            print(f"提取到 {len(questions)} 个热榜问题")
            return questions
            
        except Exception as e:
            print(f"提取热榜问题时出错: {e}")
            traceback.print_exc()
            return []
    
    async def extract_question_links(self) -> List[Question]:
        """提取所有问题链接"""
        try:
            question_data = await self.page.evaluate("""
            () => {
                const questions = [];
                const processed = new Set(); // 避免重复
                
                // 查找所有可能的问题链接
                const links = document.querySelectorAll('a[href*="/question/"]');
                console.log(`找到 ${links.length} 个可能的问题链接`);
                
                links.forEach(link => {
                    try {
                        const href = link.getAttribute('href');
                        if (!href || !href.includes('/question/')) return;
                        
                        // 提取问题ID
                        const idMatch = href.match(/\\/question\\/(\\d+)/);
                        if (!idMatch) return;
                        
                        const id = idMatch[1];
                        if (processed.has(id)) return;
                        
                        let title = link.textContent.trim();
                        
                        // 忽略过短或空标题，或者明显不是问题标题的链接
                        if (!title || title.length < 5 || 
                            title.includes('查看全部') || 
                            title.includes('更多') || 
                            title.includes('登录') ||
                            title.includes('...')) return;
                        
                        processed.add(id);
                        
                        // 构建完整URL
                        const fullUrl = href.startsWith('http') ? href : "https://www.zhihu.com" + href;
                        
                        questions.push({
                            id,
                            title,
                            url: fullUrl,
                            answer_count: 0,
                            follow_count: 0
                        });
                    } catch (e) {
                        console.error('提取问题链接时出错:', e);
                    }
                });
                
                return questions;
            }
            """)
            
            # 转换为Question对象
            questions = []
            for data in question_data:
                question = Question(
                    id=data["id"],
                    title=data["title"],
                    url=data["url"],
                    answer_count=data.get("answer_count", 0),
                    follow_count=data.get("follow_count", 0)
                )
                questions.append(question)
            
            print(f"提取到 {len(questions)} 个问题链接")
            return questions
            
        except Exception as e:
            print(f"提取问题链接时出错: {e}")
            traceback.print_exc()
            return []


async def scrape_questions(limit: int = 20, headless: bool = True) -> List[Question]:
    """爬取问题的便捷函数"""
    scraper = ZhihuScraper(headless=headless)
    try:
        return await scraper.scrape(limit=limit)
    finally:
        await scraper.close() 