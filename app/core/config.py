from pydantic_settings import BaseSettings, SettingsConfigDict
import json
from pydantic import BaseModel
from ..models.account import AccountInfo
    

class AccountSettings(BaseSettings):
    accounts: list[AccountInfo]

    # 配置 Pydantic 读取 .env 文件
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",extra="ignore")

class Setting(BaseSettings):
    chrome_path: str
    # 配置 Pydantic 读取 .env 文件
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",extra="ignore")

class DifySettings(BaseSettings):
    dify_url: str
    api_key: str
    # 配置 Pydantic 读取 .env 文件
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",extra="ignore")
    
# 实例化，全局调用这个 settings 即可
account_settings = AccountSettings()

dify_settings = DifySettings()

settings = Setting()