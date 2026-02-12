import sys
import yaml
from pathlib import Path
from loguru import logger

def setup_logging(config_path: str = "logging_config.yaml"):
    # 确保日志目录存在
    Path("logs").mkdir(exist_ok=True)

    # 1. 移除 Loguru 默认的 handler
    logger.remove()

    # 2. 读取 YAML 配置文件
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    log_config = config.get("logging", {})

    # 3. 解析并添加 Handlers
    for handler in log_config.get("handlers", []):
        # 处理特殊的 sink (如 sys.stdout)
        sink = handler.pop("sink")
        if sink == "sys.stdout":
            sink = sys.stdout
        
        # 将参数解包传给 logger.add
        logger.add(sink, format=log_config.get("format"), **handler)

    return logger

# 预初始化一个实例供全局直接 import
log = setup_logging()