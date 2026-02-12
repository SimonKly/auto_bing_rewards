
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from core.task import start_all_account_task

from fastapi import APIRouter

# 使用 Router 而不是 FastAPI 实例
router = APIRouter()

# @app.get("/api/accounts")

# 开始所有账号任务
@router.get("/start")
async def start_all():
    
    await start_all_account_task()
    


# 指定账号开始任务

# 停止所有任务

# 指定账号停止任务