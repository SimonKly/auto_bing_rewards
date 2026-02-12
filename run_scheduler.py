from app.core.scheduler import TaskScheduler
from app.core.logger import log

if __name__ == "__main__":
    log.info("正在启动自动必应奖励定时任务...")
    scheduler = TaskScheduler()
    try:
        scheduler.start()
    except KeyboardInterrupt:
        log.info("定时任务已被手动停止")
    except Exception as e:
        log.error(f"定时任务执行过程中出现异常: {e}")