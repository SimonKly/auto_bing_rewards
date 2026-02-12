from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from .task import start_all_account_task
from .logger import log
import asyncio
import traceback
from .searchterm import SearchTerm
from .task import HOT_LIST
from .task import search_term_handler



class TaskScheduler:
    def __init__(self):
        self.scheduler = BlockingScheduler()
        self.first_execution_failed = False
        
    def schedule_jobs(self):
        # 每天凌晨4点执行任务
        self.scheduler.add_job(
            func=self.run_task_at_4am,
            trigger=CronTrigger(hour=4, minute=0),
            id='run_task_4am',
            name='Run task at 4 AM',
            replace_existing=True
        )
        
        # 每天上午8点执行任务（作为备用）
        self.scheduler.add_job(
            func=self.run_task_at_8am,
            trigger=CronTrigger(hour=8, minute=0),
            id='run_task_8am',
            name='Run task at 8 AM if 4 AM failed',
            replace_existing=True
        )
    
    async def _execute_task(self):
        """执行获取热词列表的任务"""
        try:
            
            HOT_LIST(await search_term_handler.get_hot_search_terms())
            log.info("任务执行成功")
            return True
        except Exception as e:
            log.error(f"任务执行失败: {str(e)}")
            log.error(traceback.format_exc())
            return False
    
    def run_task_at_4am(self):
        """4点执行的任务"""
        log.info("开始执行4点的任务")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            success = loop.run_until_complete(self._execute_task())
            if not success:
                self.first_execution_failed = True
                log.warning("4点任务执行失败，将在8点重试")
            
            loop.close()
        except Exception as e:
            log.error(f"4点任务执行过程中出现异常: {e}")
            log.error(traceback.format_exc())
            self.first_execution_failed = True
    
    def run_task_at_8am(self):
        """8点执行的任务（备用）"""
        log.info("开始执行8点的任务")
        
        # 如果4点的任务已经成功执行，则跳过8点的任务
        if not self.first_execution_failed:
            log.info("4点任务已成功执行，跳过8点任务")
            return
            
        # 否则执行备用任务
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            loop.run_until_complete(self._execute_task())
            # 重置标志位
            self.first_execution_failed = False
            
            loop.close()
        except Exception as e:
            log.error(f"8点任务执行过程中出现异常: {e}")
            log.error(traceback.format_exc())
    
    def start(self):
        """启动调度器"""
        self.schedule_jobs()
        log.info("定时任务调度器已启动...")
        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            log.info("定时任务调度器已停止")
            self.scheduler.shutdown()