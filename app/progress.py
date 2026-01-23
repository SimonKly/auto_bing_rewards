class progress():
    """
    1. 账号
2. 日期
3. pc端进度
4. 移动端进度
5. 当日首次查询的积分
6. 实时积分
    
    """
    def __init__(self, account, date):
        self.account = account
        self.date = date
        self.pc_progress = 0
        self.mobile_progress = 0
        self.first_query_points = 0
        self.real_points = 0
    
    def up_progress(self, type, progress, first_query_points, real_points):
        if type == "pc":
            self.pc_progress = progress
        elif type == "mobile":
            self.mobile_progress = progress
        else:
            raise ValueError("Invalid type")
        
        self.first_query_points = first_query_points
        self.real_points = real_points
        
    def save(self):
        db = get_db()