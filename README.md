# auto_bing_rewards

## How to download dependency
uv python pin 3.12
uv init
cat requirement.txt | xargs uv add 



## 技术栈
1. python3.12
2. playwright
3. playwright-stealth 2.0+
4. FastApi
5. sqlite
6. jQuery
7. html5
8. bootstrap

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

## 项目结构

```shell
ms_rewards_project/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 路由与主程序 (API Routes & Main App)
│   ├── database.py      # 数据库模型与 CRUD (Database Models & CRUD)
│   ├── bot.py           # Playwright 自动化核心逻辑 (Playwright Bot Logic)
│   └── static/          # 前端静态文件 (Frontend Static Files)
│       └── index.html   # 可视化仪表盘 (Dashboard UI)
├── data/                # 存放 SQLite 数据库 (Database Storage)
├── logs/                # 运行日志 (Execution Logs)
├── requirements.txt     # 项目依赖 (Dependencies)
└── .env                 # 环境变量 (Environment Variables)
```


## todo
0. 云服务器上部署DailyHotApi
1. 使用云dify
2. 调用云服务器上的DailyHotApi
3. Dify workflow暴露接口

```markdown
你好！作为全栈工程师，我明白你目前遇到的问题：原有的提示词使用了 `hot_tokenizers` 这个术语，导致 LLM 将注意力集中在了**分词（Tokenization）**上，产出的结果往往是细碎的“单词”而非完整的“热搜话题/事件”。

为了提取更具语义完整性的**热搜标题或事件短语**，我们需要将“Tokenizer”替换为“Search Trends”或“Hot Topics”，并明确要求提取**短语实体**。

以下是优化后的版本：

---

# Role

你是一位资深热点新闻分析员，精通新闻语义分析与趋势追踪，擅长从全网海量信息中提取高价值的**热搜话题短语**。

# Guidelines

* **Task**: 提取当前或指定文本中的 **30个** 核心热搜话题（hot_search_topics）。
* **Granularity**: 不要提取单个词汇（如“科技”、“大涨”），而要提取**完整的短语实体或事件摘要**（如“SpaceX 成功发射”、“2026 A股开门红”、“某明星回应传闻”）。
* **Output Standard**: 严格遵守 JSON Schema 规范，不输出任何解释性文字。
* **Topic Selection**: 确保覆盖科技、社会、财经、国际及文娱等多个维度，优先选取社交媒体高活跃度、搜索量激增的突发事件。

# JSON Schema Definition

{
"$schema": "[http://json-schema.org/draft-07/schema#](http://json-schema.org/draft-07/schema#)",
"type": "object",
"properties": {
"datetime": {
"type": "string",
"format": "date-time",
"description": "当前的日期和精确时间"
},
"hot_search_topics": {
"type": "array",
"items": {
"type": "string",
"description": "完整的热搜事件短语"
},
"minItems": 30,
"maxItems": 30,
"description": "包含30个独立热搜话题的数组"
}
},
"required": ["datetime", "hot_search_topics"]
}

# Output Example

{
"datetime": "2026-01-30 14:00:00",
"hot_search_topics": [
"全球首款 AI 医生正式上线测试",
"某地突发 5.0 级地震",
"2026 年度科技风云榜单发布",
"...",
"第 30 个完整热搜事件"
]
}

---

### 优化点解析：

1. **术语更迭**：将 `hot_tokenizers` 全面替换为 `hot_search_topics`。在 LLM 的语境中，Tokenizer 带有强烈的自然语言处理底层色彩，容易诱导模型输出碎词。
2. **明确粒度（Granularity）**：新增了对“短语实体”的要求，通过正向引导（如“SpaceX 成功发射”）和反向约束（不要“科技”、“大涨”），确保提取出的是完整的新闻点。
3. **Schema 描述强化**：在 `items` 中加入了 `description`，进一步在结构化层面约束模型理解“什么是话题”。

**需要我为你编写一个 Python 脚本来解析这个 JSON 输出，并将其直接对接到你的前端展示组件中吗？**


```