# auto_bing_rewards







## 技术栈
1. python3.12
2. playwright
3. FastApi
4. sqlite
4. jQuery
5. html5
6. bootstrap

## 详细设计

### 模块设计
#### 用户账号管理
1. 账号account
2. 密码password
3. 顺序order
3. 使用account.json保存，不提交git，防止密码泄露
4. 提交account.example.json模版
5. 项目启动判断account.json是否存在
6. 如果存在使用account.json初始化账号表
7. 不存在，则使用界面录入方式

#### 进度管理
1. 账号
2. 日期
3. pc端进度
4. 移动端进度
5. 当日首次查询的积分
6. 实时积分

#### 词条管理
1. 使用LLM生成最新最近的词条

#### 任务管理
1. 定时管理
2. 任务管理

#### 自动控制机器人
1. 使用

### 交互视觉设计
1. 满足pc和移动端浏览器展示，使用弹性布局
1. 可以筛选账号、日期
2. 使用表格展示当日进度等信息
3. 表头包括
    2. 账号
    3. pc查询进度
    4. 移动端查询进度
    5. 当日初始积分
    6. 实时积分
    7. 今日获取的积分

