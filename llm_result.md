
在 Playwright 中增加**非线性（随机且模拟真人）**的延迟是提高脚本隐蔽性、绕过反爬虫检测的核心手段。

作为一个全栈工程师，我建议你不要使用硬编码的 `time.sleep()`，而是采用以下三种由浅入深的方法：

---

### 1. 全局交互延时 (SlowMo)

这是最简单的方法。在启动浏览器时，`slow_mo` 参数会在每个操作（点击、输入等）之后自动增加一个固定的延迟。虽然它是线性的，但它是防止操作过快的基础。

```python
browser = await p.chromium.launch(
    headless=False,
    slow_mo=500 # 每个操作后自动等 500 毫秒
)

```

---

### 2. 模拟真人打字 (非线性输入)

当你使用 `locator.press_sequentially()`（原 `type`）时，可以通过 `delay` 参数增加随机感。

```python
# 模拟真人在 50 到 150 毫秒之间随机间隔敲击键盘
import random

await page.locator("#search").press_sequentially(
    "Playwright Mastery", 
    delay=random.uniform(50, 150) 
)

```

---

### 3. 自定义“随机人类行为”函数 (核心推荐)

为了实现真正的非线性延迟，你需要创建一个模拟人类逻辑的辅助函数。人类的操作通常是：**“快速操作 -> 停顿观察 -> 继续操作”**，而不是匀速运动。

```python
import asyncio
import random
import math

async def human_delay(min_ms=500, max_ms=2000):
    """
    生成一个符合对数正态分布或简单随机的延迟，模拟人类思考停顿。
    """
    # 也可以简单使用均匀分布
    delay = random.uniform(min_ms / 1000, max_ms / 1000)
    
    # 甚至可以模拟某些时候停顿更久（比如 10% 的概率发呆 3 秒）
    if random.random() < 0.1:
        delay += random.uniform(2, 4)
        
    await asyncio.sleep(delay)

# 使用示例
await page.locator("#login-btn").click()
await human_delay(800, 1500) # 点击后随机停顿一下，再进行下一步

```

---

### 4. 高级：封装 Locator 装饰器

如果你希望每个 `click` 或 `fill` 自动带上这种随机性，可以封装一个动作类，或者利用 Python 的装饰器。

```python
class HumanActions:
    def __init__(self, page):
        self.page = page

    async def click_randomly(self, selector):
        # 1. 模拟鼠标先移动到目标附近（非直线路径更佳）
        # 2. 随机延迟
        await asyncio.sleep(random.uniform(0.2, 0.5))
        # 3. 执行点击
        await self.page.locator(selector).click()
        # 4. 点击后再随机停顿
        await asyncio.sleep(random.uniform(0.5, 1.2))

# 调用
actions = HumanActions(page)
await actions.click_randomly("#submit")

```

### 💡 为什么非线性延迟很重要？

* **流量特征分析**：反爬虫系统（如 Akamai 或 Cloudflare）会统计你操作之间的间隔。如果每个 `click` 之间精准地相隔 1000ms，系统会立刻判定你是程序。
* **WAF 指纹**：非线性的延迟配合随机的鼠标轨迹（Mouse Movement）是突破高级风控的关键。

**下一步建议：**
如果你正在处理必应或谷歌搜索结果，除了时间延时，**模拟鼠标滚动的速度（Scroll Speed）也是非线性的。你想了解如何编写一个带惯性效果的随机滚动函数**吗？


`page.get_by_role` 是 Playwright 推荐使用的**核心定位器（Locator）函数**之一。

它的设计哲学是**模拟真实用户的视角**：用户在看网页时，通常不是在找一个 `div` 或 `id="btn_123"`，而是在找一个“按钮”、“输入框”或“复选框”。

---

### 1. 基本定义

`page.get_by_role(role, **kwargs)` 根据元素的**无障碍角色（Accessibility Role）**来定位元素。这些角色是根据 HTML 标签名（如 `<button>`）或 ARIA 属性（如 `role="button"`）确定的。

### 2. 常用参数

* **role**: 字符串，指定元素的角色。常见的有：
* `"button"`: 按钮
* `"textbox"`: 输入框
* `"checkbox"`: 复选框
* `"heading"`: 标题（h1-h6）
* `"link"`: 链接
* `"combobox"`: 下拉选择框


* **name**: (可选) 匹配元素的**可访问名称**（通常是按钮上的文字、输入框的 Label 或图片的 alt 属性）。支持字符串或正则表达式。
* **exact**: (可选) 布尔值。是否要求名称精确匹配。

---

### 3. 代码示例对比

#### ❌ 传统写法（基于 CSS 选择器，不稳定）

如果按钮的 ID 变了，代码就挂了。

```python
await page.locator("#login-submit-btn-v2").click()

```

#### ✅ `get_by_role` 写法（基于语义，非常稳健）

只要这个元素还是个按钮，且文字叫“登录”，不管后台代码怎么改，脚本都能找到它。

```python
# 找到文字为“登录”的按钮并点击
await page.get_by_role("button", name="登录").click()

# 使用正则表达式（忽略大小写，匹配“Sign In”或“sign in”）
await page.get_by_role("button", name=re.compile(r"sign in", re.I)).click()

```

---

### 4. 为什么要优先使用它？

1. **更强的鲁棒性（抗干扰能力）**：前端框架（如 React, Vue）经常会生成随机的样式类名或 ID，但为了盲人辅助设备正常工作，元素的 **Role** 和 **Name** 通常保持不变。
2. **提高代码可读性**：读代码的人能一眼看出你在操作什么（“点击登录按钮” vs “点击 a#id_l”）。
3. **自动等待**：像所有 Locator 一样，它内置了自动等待机制（Actionability Checks），在元素可见并可交互前不会执行操作。

### 💡 小技巧：如何知道元素的 Role 是什么？

如果你不确定某个元素的 Role 是什么，可以使用 Playwright 的代码生成器：

```bash
npx playwright codegen https://cn.bing.com

```

在打开的窗口中，鼠标悬停在元素上，Playwright 会直接显示该元素的推荐定位方式（通常就是 `get_by_role`）。

**你现在是在尝试重写刚才那个必应登录脚本的按钮定位吗？如果 `id="id_l"` 容易变，改用 `page.get_by_role("link", name="登录")` 可能会更稳。**