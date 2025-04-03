"""
Configuration settings for the Zhihu Hot Questions Scraper
"""
import os
import json
from pathlib import Path

class Settings:
    """Settings class for the scraper application"""
    
    def __init__(self):
        """初始化配置"""
        # 默认配置
        self.cookies_file = os.path.join(os.getcwd(), "cookies.json")
        self.zhihu_url = "https://www.zhihu.com/question/waiting"  # 知乎等你来答页面
        self.scrape_interval = 60  # 爬取间隔，单位：分钟
        self.question_limit = 20  # 每次爬取的问题数量限制
        self.database_path = os.path.join(os.getcwd(), "questions.db")
        self.headless = True  # 设置为True，使用无头模式
        self.debug = True  # 保持调试模式打开，便于排错
        
        # 加载配置文件
        self.load_config()
    
    def load_config(self):
        """从config.json加载配置"""
        config_path = os.path.join(os.getcwd(), "config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.cookies_file = config.get("cookies_file", self.cookies_file)
                    self.zhihu_url = config.get("zhihu_url", self.zhihu_url)
                    self.scrape_interval = config.get("scrape_interval", self.scrape_interval)
                    self.question_limit = config.get("question_limit", self.question_limit)
                    self.database_path = config.get("database_path", self.database_path)
                    self.headless = config.get("headless", self.headless)  # 正常读取配置的headless设置
                    self.debug = config.get("debug", True)
                print(f"已加载配置: {config}")
        except Exception as e:
            print(f"加载配置文件出错: {e}")
            print("将使用默认配置")
    
    def save_to_file(self, config_file):
        """Save current settings to a JSON configuration file"""
        config = {
            'zhihu_url': self.zhihu_url,
            'cookies_file': self.cookies_file,
            'scrape_interval': self.scrape_interval,
            'question_limit': self.question_limit,
            'database_path': self.database_path,
            'headless': self.headless
        }
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    def save_cookies(self, cookies_text: str) -> bool:
        """保存 cookies 到文件"""
        try:
            # 处理 cookies
            cookies_json = {}
            if cookies_text.strip():
                # 如果输入是JSON格式
                if cookies_text.strip().startswith('{') and cookies_text.strip().endswith('}'):
                    try:
                        cookies_json = json.loads(cookies_text)
                    except:
                        print("无法解析JSON格式，尝试解析Cookie字符串")
                        cookies_json = self.parse_cookie_string(cookies_text)
                # 如果输入是Cookie: 开头的标头格式
                elif cookies_text.strip().startswith('Cookie:'):
                    cookies_text = cookies_text.replace('Cookie:', '').strip()
                    cookies_json = self.parse_cookie_string(cookies_text)
                # 普通Cookie字符串格式：name=value; name2=value2
                else:
                    cookies_json = self.parse_cookie_string(cookies_text)
            
            print(f"处理后的cookies: {cookies_json}")
            print(f"cookies个数: {len(cookies_json)}")
            
            # 保存到文件
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies_json, f, ensure_ascii=False, indent=4)
            
            return True
        except Exception as e:
            print(f"保存cookies时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_cookies(self):
        """Load cookies from file"""
        if not os.path.exists(self.cookies_file):
            return {}
            
        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cookies: {e}")
            return {}

    def parse_cookie_string(self, cookie_string: str) -> dict:
        """解析Cookie字符串，转换为字典格式"""
        cookies = {}
        try:
            if not cookie_string:
                return {}
            
            # 解析cookie字符串
            parts = cookie_string.split(';')
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                # 处理特殊情况，如果没有=号，跳过
                if '=' not in part:
                    continue
                
                key, value = part.split('=', 1)
                cookies[key.strip()] = value.strip()
            
            return cookies
        except Exception as e:
            print(f"解析Cookie字符串时出错: {e}")
            return {}


# Create a default settings instance
settings = Settings() 