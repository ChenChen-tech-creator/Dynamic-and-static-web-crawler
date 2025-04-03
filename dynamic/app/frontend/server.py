"""
知乎热点问题爬虫的 FastAPI 前端服务器
"""
import os
import json
import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config.settings import settings
from app.database.models import QuestionDatabase, Question
from app.scheduler.scheduler import ScraperScheduler, manual_run

# 初始化 FastAPI 应用
app = FastAPI(title="知乎热点问题爬虫")

# 如果模板目录不存在则创建
os.makedirs("templates", exist_ok=True)

# 如果静态文件目录不存在则创建
os.makedirs("static", exist_ok=True)

# 模板和静态文件配置
templates = Jinja2Templates(directory="templates")
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    print(f"挂载静态文件时出错: {e}")

# 初始化数据库和调度器
db = QuestionDatabase(settings.database_path)
scheduler = ScraperScheduler(
    interval_minutes=settings.scrape_interval,
    question_limit=settings.question_limit,
    database_path=settings.database_path
)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """首页，显示问题列表"""
    questions = db.get_all_questions(limit=100)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "questions": questions,
        "total_count": db.count_questions(),
        "last_run": scheduler.last_run,
        "is_running": scheduler.running
    })


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """设置页面"""
    # 读取已保存的 cookies 文件内容
    cookies_text = ""
    if os.path.exists(settings.cookies_file):
        try:
            with open(settings.cookies_file, 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)
                # 将 cookies 转换为文本格式：name=value; name2=value2;
                cookies_text = "; ".join([f"{name}={value}" for name, value in cookies_data.items()])
        except Exception as e:
            print(f"读取 cookies 文件时出错: {e}")
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "settings": settings,
        "cookies_text": cookies_text
    })


@app.post("/settings/save")
async def save_settings(
    scrape_interval: int = Form(...),
    question_limit: int = Form(...),
    headless: bool = Form(False)
):
    """保存设置"""
    # 更新设置
    settings.scrape_interval = scrape_interval
    settings.question_limit = question_limit
    settings.headless = headless
    
    # 保存到配置文件
    settings.save_to_file("config.json")
    
    # 更新调度器
    if scheduler.running:
        scheduler.stop()
    
    scheduler.interval_minutes = scrape_interval
    scheduler.question_limit = question_limit
    
    if scheduler.running:
        scheduler.start()
    
    return RedirectResponse(url="/settings", status_code=303)


@app.post("/settings/cookies")
async def save_cookies(cookies: str = Form(...)):
    """保存 Cookies"""
    success = settings.save_cookies(cookies)
    return {"success": success}


@app.post("/scraper/start")
async def start_scraper():
    """启动爬虫调度器"""
    success = scheduler.start()
    return {"success": success}


@app.post("/scraper/stop")
async def stop_scraper():
    """停止爬虫调度器"""
    scheduler.stop()
    return {"success": True}


@app.post("/scraper/run-once")
async def run_scraper_once():
    """手动运行一次爬虫"""
    try:
        # 直接await异步函数
        questions_count = await manual_run()
        
        return {"success": True, "message": f"爬虫运行成功，采集了 {questions_count} 个问题。"}
    except Exception as e:
        print(f"手动运行爬虫时出错: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"爬虫运行出错: {str(e)}"}


@app.on_event("startup")
async def startup_event():
    """启动时创建模板文件"""
    # 创建 index.html
    if not os.path.exists("templates/index.html"):
        with open("templates/index.html", "w", encoding="utf-8") as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>知乎热点问题爬虫</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .question-card {
            margin-bottom: 15px;
            transition: all 0.3s;
        }
        .question-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">知乎热点问题爬虫</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link active" href="/">首页</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/settings">设置</a>
                    </li>
                </ul>
                <div class="d-flex">
                    <button id="run-once-btn" class="btn btn-outline-light me-2">立即运行一次</button>
                    {% if is_running %}
                        <button id="stop-scraper-btn" class="btn btn-danger">停止定时任务</button>
                    {% else %}
                        <button id="start-scraper-btn" class="btn btn-success">启动定时任务</button>
                    {% endif %}
                </div>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">状态</h5>
                        <p>问题总数: <strong>{{ total_count }}</strong></p>
                        <p>调度器状态: <strong>{% if is_running %}运行中{% else %}已停止{% endif %}</strong></p>
                        <p>上次运行: <strong>{% if last_run %}{{ last_run.strftime('%Y-%m-%d %H:%M:%S') }}{% else %}从未运行{% endif %}</strong></p>
                    </div>
                </div>
            </div>
        </div>

        <h2 class="mb-4">热门问题</h2>
        
        <div class="row">
            {% for question in questions %}
            <div class="col-md-6">
                <div class="card question-card">
                    <div class="card-body">
                        <h5 class="card-title">{{ question.title }}</h5>
                        <h6 class="card-subtitle mb-2 text-muted">问题ID: {{ question.id }}</h6>
                        <p class="card-text">
                            <span class="badge bg-primary me-2">{{ question.answer_count }} 回答</span>
                            <span class="badge bg-secondary">{{ question.follow_count }} 关注</span>
                        </p>
                        <a href="{{ question.url }}" class="btn btn-sm btn-outline-primary" target="_blank">在知乎查看</a>
                        <small class="text-muted d-block mt-2">采集时间: {{ question.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</small>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('run-once-btn').addEventListener('click', function() {
            if (confirm('确定要立即运行一次爬虫吗？')) {
                fetch('/scraper/run-once', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                        location.reload();
                    } else {
                        alert(data.message);
                    }
                });
            }
        });
        
        {% if is_running %}
        document.getElementById('stop-scraper-btn').addEventListener('click', function() {
            if (confirm('确定要停止定时任务吗？')) {
                fetch('/scraper/stop', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('定时任务已停止。');
                        location.reload();
                    } else {
                        alert('停止定时任务失败。');
                    }
                });
            }
        });
        {% else %}
        document.getElementById('start-scraper-btn').addEventListener('click', function() {
            if (confirm('确定要启动定时任务吗？')) {
                fetch('/scraper/start', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('定时任务已启动。');
                        location.reload();
                    } else {
                        alert('定时任务已在运行或启动失败。');
                    }
                });
            }
        });
        {% endif %}
    </script>
</body>
</html>
            """)
    
    # 创建 settings.html
    if not os.path.exists("templates/settings.html"):
        with open("templates/settings.html", "w", encoding="utf-8") as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>设置 - 知乎热点问题爬虫</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">知乎热点问题爬虫</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/">首页</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link active" href="/settings">设置</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <h2 class="mb-4">系统设置</h2>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="card-title mb-0">爬虫设置</h5>
                    </div>
                    <div class="card-body">
                        <form action="/settings/save" method="post">
                            <div class="mb-3">
                                <label for="scrape_interval" class="form-label">爬取间隔（分钟）</label>
                                <input type="number" class="form-control" id="scrape_interval" name="scrape_interval" value="{{ settings.scrape_interval }}" min="1" required>
                            </div>
                            <div class="mb-3">
                                <label for="question_limit" class="form-label">问题数量限制</label>
                                <input type="number" class="form-control" id="question_limit" name="question_limit" value="{{ settings.question_limit }}" min="1" required>
                            </div>
                            <div class="mb-3 form-check">
                                <input type="checkbox" class="form-check-input" id="headless" name="headless" {% if settings.headless %}checked{% endif %}>
                                <label class="form-check-label" for="headless">无头模式运行（不显示浏览器窗口）</label>
                            </div>
                            <button type="submit" class="btn btn-primary">保存设置</button>
                        </form>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Cookies 设置</h5>
                    </div>
                    <div class="card-body">
                        <p class="card-text">请粘贴从知乎网站获取的 cookies 字符串，用于访问热点问题页面。</p>
                        <form id="cookies-form">
                            <div class="mb-3">
                                <label for="cookies" class="form-label">Cookies</label>
                                <textarea class="form-control" id="cookies" rows="8" placeholder="name=value; name2=value2;">{{ cookies_text }}</textarea>
                                <div class="form-text">格式: name=value; name2=value2; ...</div>
                            </div>
                            <button type="button" id="save-cookies-btn" class="btn btn-primary">保存 Cookies</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('save-cookies-btn').addEventListener('click', function() {
            const cookies = document.getElementById('cookies').value;
            
            fetch('/settings/cookies', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'cookies=' + encodeURIComponent(cookies)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Cookies 保存成功。');
                } else {
                    alert('Cookies 保存失败。');
                }
            });
        });
    </script>
</body>
</html>
            """)


# Create a main function to run the app using uvicorn
def start_server(host="0.0.0.0", port=8000):
    """启动网络服务器"""
    import uvicorn
    print(f"服务器正在启动，访问地址: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port) 