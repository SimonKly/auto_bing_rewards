from fastapi import FastAPI
import uvicorn
from api.task import router as task_router
from core.logger import setup_logging, log
from core.scheduler import TaskScheduler
import threading

setup_logging("logging_config.yaml")

app = FastAPI()

# 挂载路由
app.include_router(task_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Auto Bing Rewards Scheduler is running!"}

def start_scheduler():
    """启动定时任务调度器"""
    scheduler = TaskScheduler()
    scheduler.start()

if __name__ == "__main__":
    # 启动调度器作为后台线程
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    
    log.info("Starting Auto Bing Rewards API server...")
    # 启动FastAPI服务
    uvicorn.run(app, host="0.0.0.0", port=18000)

# if "__main__" == __name__:
#     hot_list_demo = '''
#     {
#   "task_id": "f5830555-30a5-418f-bdee-08d8471c7bca",
#   "workflow_run_id": "3b1c064b-2250-4845-8cf1-2b9f6bb3a129",
#   "data": {
#     "id": "3b1c064b-2250-4845-8cf1-2b9f6bb3a129",
#     "workflow_id": "cbf48d94-299d-4787-b6a6-97bab6b650b7",
#     "status": "succeeded",
#     "outputs": {
#       "hot_list": {
#         "datetime": "2026-02-05T07:39:51.055Z",
#         "hot_search_topics": [
#           "微博之夜红毯",
#           "王一博 大明星回内娱",
#           "2026年新春走基层",
#           "小洛熙事件最新通报",
#           "王者荣耀小马糕",
#           "娜扎 人间维纳斯",
#           "A股市场迎来调整",
#           "热巴脸链",
#           "黄金突然下跌",
#           "白鹿灼灼红裙",
#           "敖瑞鹏大背头",
#           "爱泼斯坦案证实吸血鬼舞会存在",
#           "王玉雯透纱紧身裙",
#           "家里最没用的把最有用的吃了",
#           "公考围岗令人震惊必须打击",
#           "白鹿王星越30秒饭撒30次",
#           "李兰迪粉色蓬蓬裙",
#           "微博之夜 真婚礼",
#           "#萝莉岛幸存者曾每天被侵犯3次#",
#           "#2026年新春走基层#",
#           "#小洛熙事件最新通报#",
#           "#王者荣耀小马糕#",
#           "#娜扎 人间维纳斯#",
#           "#热巴脸链#",
#           "#黄金突然下跌#",
#           "#白鹿灼灼红裙#",
#           "#敖瑞鹏大背头#",
#           "#爱泼斯坦案证实吸血鬼舞会存在#",
#           "#王玉雯透纱紧身裙#",
#           "#家里最没用的把最有用的吃了#",
#           "#公考围岗令人震惊必须打击#",
#           "#白鹿王星越30秒饭撒30次#",
#           "#李兰迪粉色蓬蓬裙#"
#         ]
#       }
#     },
#     "error": "",
#     "elapsed_time": 10.349953,
#     "total_tokens": 11916,
#     "total_steps": 5,
#     "created_at": 1770277190,
#     "finished_at": 1770277200
#   }
# }
# '''
    
    # hot_list_json = json.loads(hot_list_demo)
    # status = hot_list_json.get('data', {}).get('status')
    # if status != 'succeeded':
    #     print(f"Dify API调用未成功，状态: {status}")

    # # 获取输出结果
    # outputs = hot_list_json.get('data', {}).get('outputs', {})
    # hot_list_str = outputs.get('hot_list', '{}')
    
    # hot_search_topics = hot_list_str.get('hot_search_topics', [])
    # print(hot_search_topics)