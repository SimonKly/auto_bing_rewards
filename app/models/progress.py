from pydantic import BaseModel

class DetailInfo(BaseModel):
    # 时间戳
    time: int
    # 信息
    message: str

class Progress(BaseModel):
    """
    进度信息
    """
    # 开始时间戳
    start_time: int
    # 结束时间戳
    end_time: int
    # 账号邮箱
    email: str
    # 日期
    date: str
    # 实时积分
    real_point: int
    # 首次查询的积分
    first_query_points: int
    # 查询次数
    query_count: int
    # 进度详情
    detail_info_list: list[DetailInfo]
 