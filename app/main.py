from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import database
from .database import engine, SessionLocal, get_db, Account
from typing import List
import json
import os

app = FastAPI()

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 读取accounts.json文件内容
def load_accounts_from_json():
    if os.path.exists("accounts.json"):
        with open("accounts.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("accounts", [])
    return []

# 初始化数据库中的账户
def init_accounts():
    db = SessionLocal()
    try:
        # 加载JSON文件中的账户
        json_accounts = load_accounts_from_json()
        
        # 检查数据库中是否已有这些账户
        for acc_data in json_accounts:
            existing_acc = db.query(Account).filter(Account.email == acc_data["email"]).first()
            if not existing_acc:
                new_acc = Account(
                    username=acc_data["name"],
                    email=acc_data["email"],
                    password=acc_data["password"]
                )
                db.add(new_acc)
        db.commit()
    finally:
        db.close()

# 应用启动时初始化账户
@app.on_event('startup')
def startup_event():
    init_accounts()

@app.get("/")
async def read_root():
    with open("app/static/index.html", "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/html")

@app.get("/api/accounts")
async def list_accounts(db: Session = Depends(get_db)):
    accounts = db.query(Account).all()
    return [
        {
            "id": acc.id,
            "username": acc.username,
            "email": acc.email,
            "pc_search_progress": acc.pc_search_progress,
            "mobile_search_progress": acc.mobile_search_progress,
            "daily_set_status": acc.daily_set_status,
            "last_run": acc.last_run,
            "status": "Running" if acc.last_run and (datetime.datetime.utcnow() - acc.last_run.replace(tzinfo=None)).seconds < 300 else "Idle"
        }
        for acc in accounts
    ]

@app.post("/api/run/{account_id}")
async def start_task(account_id: int, db: Session = Depends(get_db)):
    from .bot import RewardsBot
    import asyncio
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # 在后台运行任务
    import threading
    def run_bot_task():
        bot = RewardsBot()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.execute_account_task(account))
    
    thread = threading.Thread(target=run_bot_task)
    thread.start()
    
    return {"message": f"Task started for account {account.username}"}

# 添加一个响应类，用于返回HTML内容
from starlette.responses import Response
import datetime