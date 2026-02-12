from typing import List
from .logger import log
import requests

class SearchTerm:
    def __init__(self, dify_url: str, api_key: str):
        self.dify_url = dify_url
        self.api_key = api_key
    
    async def get_hot_search_terms(self) -> List[str]:
        """
        从Dify API获取热搜词列表
        """
        try:
            url = f"{self.dify_url}/v1/workflows/run"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            data = {
                "inputs": {},
                "response_mode": "blocking",
                "user": "bot"
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            # 解析响应
            result = response.json()
            log.info(f"Dify API调用成功，响应: {result}")
            # 检查状态
            status = result.get('data', {}).get('status')
            # if status != 'succeeded':
            log.warning(f"Dify API调用未成功，状态: {status}")

            # 获取输出结果
            outputs = result.get('data', {}).get('outputs', {})
            hot_list_str = outputs.get('hot_list', '{}')
            
            # 提取热搜词列表
            hot_search_topics = hot_list_str.get('hot_search_topics', [])
            
            if not hot_search_topics:
                log.warning("未能从Dify API响应中获取到热搜词列表")
                return self.__get_default_search_terms()
            
            log.info(f"成功获取到 {len(hot_search_topics)} 个热搜词")
            return hot_search_topics
            
        except Exception as e:
            log.exception(f"获取Dify热搜词时发生错误: {e}")
            return self.__get_default_search_terms()
    
    
    
    def __get_default_search_terms(self) -> List[str]:
        """获取默认的搜索词列表"""
        default_hot_list =  [
                "黄金白银价格双双暴跌原因",
                "爸爸在家吸烟13岁女儿腹腔长满肿瘤",
                "原来维生素D缺乏容易长白头发",
                "袁娅维在美国唐人街偶遇周深",
                "浙江要求党政机关严控PPT制作使用",
                "程潇富贵花",
                "林志玲为杨紫宣传生命树",
                "晚上10点睡和11点睡感觉真的不一样",
                "中共中央政治局1月30日召开会议",
                "王玉雯 假装车没停好听了两遍",
                "看肖战王彦霖懂了卧蚕和眼袋的区别",
                "孙颖莎王楚钦等出战海口亚洲杯",
                "金晨被曝肇事逃逸被撞墙农户已获赔",
                "网红周媛被立案调查",
                "白鹿cos安琪拉",
                "主人笑了半天才请假回家",
                "金晨驾车监控信息被交警否认",
                "刘浩存秒切破万",
                "光遇",
                "谢娜主持微博之夜",
                "河南一洗浴中心男子闯入女澡堂"
                ]
        return default_hot_list