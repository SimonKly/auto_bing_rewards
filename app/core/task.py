import requests
import json
import os
from .bot import RewardsBot
from .config import account_settings
from .logger import log
import time
from .searchterm import SearchTerm
from .config import dify_settings
from ..models.progress import Progress
"""
全局热搜词列表
"""
HOT_LIST = []
# 全局的热词搜索句柄
search_term_handler = SearchTerm(dify_url=dify_settings.dify_url, api_key=dify_settings.api_key)
# 全局账号锁，防止一个账号正在执行任务时，不允许启动同一个账号任务
account_lock = {}

async def start_all_account_task():
    accounts = account_settings.accounts

    if len(HOT_LIST) == 0:
        log.info("热搜列表为空，开始获取热搜列表")
        HOT_LIST = await search_term_handler.get_hot_search_terms()
        log.info(f"获取热搜列表完成, 获取{len(HOT_LIST)}条数据")

    for account in accounts:
        account_progress = Progress()
        
        email = account.email
        password = account.password
        if account_lock.get(email, False):
            log.warning(f"账号: {email} 正在运行任务中，请勿重复启动")
            continue
        else:
            account_lock[email] = True
            log.info(f"账号: {email} 任务开始")
            st = time.perf_counter()
            
            # 将获取到的热搜词列表传递给Bot实例
            reward_bot = RewardsBot(min_delay=80, max_delay=120, slow_mo=5000, headless=False)
            await reward_bot.execute_account_task(account=email, password=password, search_term_list=HOT_LIST)
            
            et = time.perf_counter()
            log.info(f"账号：{email} 任务结束，耗时：{et - st:.4f} 秒")
    
if "__main__" == __name__:
    hot_list_demo = '''{
    "hot_list": {
    "datetime": "2026-02-05T07:18:20.900Z",
    "hot_search_topics": [
      "微博之夜红毯",
      "王一博 大明星回内娱"]}'''
    
    hot_list_json = json.loads(hot_list_demo)
    hot_search_topics = hot_list_json.get('hot_search_topics', [])
    print(hot_search_topics)
    