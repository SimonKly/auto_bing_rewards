from playwright.sync_api import expect
import re
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import random
import math
from .logger import log
from .config import settings
import json

class RewardsBot:
    """
    RewardsBot类，用于执行账户任务。
    """

    BING_URL = "https://www.bing.com"
    LOGIN_URL = "https://login.live.com"

    REWARDS_BING_URL = "https://rewards.bing.com/"

    def __init__(self, headless=False, slow_mo=0, type="pc", min_delay=60, max_delay=90):
        """
        初始化playwright实例。
        """
        self.headless=headless
        self.slow_mo = slow_mo
        self.type = type
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        # total_item: 总搜索任务个数
        # search_item: 已搜索个数
        # is_finish: 是否已完成
        # per_point: 每个搜索可得到的point
        self.progress_data={"total_item": 0, "search_item": 0, "per_point": 3, "is_finish": False}
        

    async def open_brower(self):
        """
        open browser
        headless: True | False, 是否启动无头浏览器
        """
        stealth = Stealth()
        # 1. 初始化管理器
        self.playwright_mgr = async_playwright()
        # 2. 手动启动（相当于进入 with 块）
        self.playwright = await self.playwright_mgr.start()
        # async with Stealth().use_async(async_playwright()) as p:
        try:
            # 1. 启动浏览器
            # 建议调试时 headless=False，部署时再改为 True
            self.browser = await self.playwright.chromium.launch(
                executable_path=settings.chrome_path,
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",  # 禁用受控标志
                    "--no-sandbox",
                    # === 核心参数：禁用 WebAuthn ===
                    # 这会告诉网站：当前浏览器不支持 USB 密钥或生物识别
                    "--disable-features=WebAuthentication",
                    "--disable-features=WebAuthenticationProxy",
                    # 某些版本的 Chrome 可能还需要这个：
                    "--disable-external-intent-requests",
                    "--start-maximized"
                ],
            )
            # 2. 创建上下文，设置视口大小 # 1. context 不要传 user_agent，让 stealth 来处理
            edge_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"

            self.context = await self.browser.new_context(
                no_viewport=True,
            user_agent=edge_ua,
            # viewport={"width": 1920, "height": 1080},
            # 额外加固：设置语言和硬件并发数，让指纹更像真人
            locale="zh-CN",
            # device_scale_factor=1,
            )
            

            # 使用stealth 隐蔽
            await stealth.apply_stealth_async(self.context)

            self.page = await self.context.new_page()

            # 在 page = await context.new_page() 之后立即执行
            cdp_session = await self.context.new_cdp_session(self.page)
            await cdp_session.send("WebAuthn.enable")
            # 创建一个虚拟的身份验证器，设置它不支持各种生物识别
            await cdp_session.send(
                "WebAuthn.addVirtualAuthenticator",
                {
                    "options": {
                        "protocol": "ctap2",
                        "transport": "usb",
                        "hasResidentKey": True,
                        "hasUserVerification": True,
                        "isUserVerified": False,  # 关键：告诉它验证失败/未验证，阻止进一步弹窗
                    }
                },
            )

            webdriver_status = await self.page.evaluate("navigator.webdriver")
            log.info("from new_page: ", webdriver_status)
            # 验证
            ua_in_js = await self.page.evaluate("navigator.userAgent")
            log.info(f"JS 中的 UA: {ua_in_js}")
            log.info("浏览器打开完成")

        except Exception as e:
            log.info(f"执行账户任务时出现错误: {str(e)}")
            await self.close()

    async def close(self):
        """
        关闭浏览器。
        """
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright_mgr:
                # 这里的 __aexit__ 会处理 playwright 实例的销毁
                await self.playwright_mgr.__aexit__()
        except Exception as e:
            log.exception(f"关闭浏览器错误: {str(e)}", exc_info=True)

    async def execute_account_task(
        self, account, password, search_term_list: list[str]
    ):
        """执行账户搜索任务。

        Args:
            account (str): 账号email
            password (str): 密码
            search_term_list (list[str]): 搜索词条列表
        """
        if len(search_term_list) == 0:
            log.info("没有搜索词条，跳过账户任务")
            return
        try:
            # 1. open browser
            await self.open_brower()
            # 2. login to bing
            await self.login(account, password)
            # 3. open bing page
            await self.open_bing()
            await self.get_search_progress()
            # 3. iterate over search terms
            first_point_current_date = await self.get_reward_points()
            log.info(f"今日的积分: {first_point_current_date}")
            for search_term in search_term_list:
                is_finish = self.progress_data["is_finish"]
                if (is_finish):
                    break
                else:
                    # 3.1. run search task
                    await self.search(search_term)
                    # 3.2. wait for a while
                    await self.random_delay()
                    await self.open_bing()
                    await self.get_search_progress()
                realtime_point_current_date = await self.get_reward_points()
                log.info(f"实时的积分: {realtime_point_current_date}")
        except Exception as ex:
            log.exception(f"账号{account}处理异常", exc_info=True)
        finally:
            # 4. close browser
            await self.close()

    async def open_bing(self):
        """
        打开必应首页。
        """
        log.info("正在访问 bing.com...")
        # 不使用 networkidle 后台一直发送请求
        await self.page.goto(
            RewardsBot.BING_URL + "/?wlexpsignin=1&synset=1", wait_until="domcontentloaded", timeout=600000
        )
        # 检查是否成功加载
        title = await self.page.title()
        log.info(f"页面标题: {title}")
        await self.human_delay()
        

        await self.page.goto(
        RewardsBot.BING_URL + "/?wlexpsignin=1&synset=1", wait_until="domcontentloaded", timeout=600000)
        await asyncio.sleep(5)
            
        
        log.info("bing页面打开完成")
    async def login(self, account, password):
        """
        打开必应登录页面。
        """
        log.info(f"正在访问 {RewardsBot.LOGIN_URL}...")
        await self.page.goto(
            RewardsBot.LOGIN_URL, wait_until="domcontentloaded", timeout=600000
        )
        # 检查是否成功加载
        title = await self.page.title()
        log.info(f"页面标题: {title}")
        

        # 4. 在新页面填写账号密码
        # Playwright 的 page 对象依然指向当前标签页，所以直接继续用 page 操作即可
        username_input = 'label[for="usernameEntry"]'
        await self.page.wait_for_selector(username_input)
        log.info("已到达登录页面，开始输入...")

        await self.page.locator(username_input).click()
        await self.human_delay()
        await self.page.locator(username_input).press_sequentially(
            account, delay=random.uniform(50, 150)
        )
        next_btn = 'button[type="submit"]'
        await self.page.wait_for_selector(next_btn)
        await self.page.locator(next_btn).click()
        await self.human_delay()
        # 切换登陆方法 idA_PWD_SwitchToCredPicker
        switch_login_type_a = "a[id='idA_PWD_SwitchToCredPicker']"
        await self.page.locator(switch_login_type_a).or_(self.page.get_by_role("button", name="其他登录方法")).click()
        await self.human_delay()
        await self.page.get_by_label("使用密码").locator("div").first.click()
        await self.human_delay()
        await self.page.get_by_label("密码", exact=True).click()
        await self.human_delay()
        await self.page.get_by_label("密码", exact=True).press_sequentially(
            password, delay=random.uniform(50, 150)
        )
        await self.human_delay()
        await self.page.get_by_test_id("primaryButton").click()
        await self.human_delay()
        tip = "Please retry with a different device or other authentication method to sign in. For more details"
        text_content = await self.page.locator("body").text_content()
        if text_content.startswith(tip):
            log.error(f"{account}需要邮箱认证")
            raise Exception(f"{account}需要邮箱认证")
        
        await self.page.get_by_test_id("primaryButton").click()
        await self.human_delay()
        # input_form = "input[name='q']"
        # await self.page.locator(input_form).click()
        # await self.human_delay()

        await asyncio.sleep(2)
        log.info("成功进入登录页面！")

    async def search(self, search_term: str):
        log.info(f"search_term: {search_term}的搜索开始")
        input_form = "#sb_form_q"
        await self.page.locator(input_form).highlight()
        await self.page.locator(input_form).click()
        await self.page.locator(input_form).fill("")  # 清空输入框
        await self.human_delay()
        
        # 分批输入搜索词以避免自动联想打断
        chunk_size = 10  # 每次输入的字符数
        for i in range(0, len(search_term), chunk_size):
            chunk = search_term[i:i+chunk_size]
            await self.page.locator(input_form).press_sequentially(
                chunk, delay=random.uniform(50, 150)
            )
            await self.human_delay()
        
        # 等待可能的自动联想出现
        try:
            # 等待一小段时间让自动联想出现
            await self.page.wait_for_timeout(1000)
            # 如果有自动联想出现，则点击第一个建议
            suggestion = self.page.locator("#sa_ul li.sa_drk")
            if await suggestion.count() > 0:
                await suggestion.first.click()
            else:
                # 如果没有自动联想，直接按回车
                await self.page.locator(input_form).press("Enter")
        except Exception:
            # 如果上面的操作失败，仍然尝试按回车
            await self.page.locator(input_form).press("Enter")
        
        # 等待搜索结果加载
        await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
        
        # 多次随机滚动，增加滚动效果
        for _ in range(3):
            distance = random.randint(400, 800)
            await self.page.mouse.wheel(0, distance)
            await self.human_delay()
        
        # 额外滚动一次，确保页面充分交互
        await self.page.mouse.wheel(0, 1000)
        await self.human_delay()
        log.info(f"search_term: {search_term}的搜索完成")
        
    async def get_reward_points(self) -> int:
        """
        获取账户的积分。
        """
        try:
            await asyncio.sleep(2)
            point_selector = 'span[data-tag="RewardsHeader.Counter"]'
            if await self.page.locator(point_selector).count() > 0:
                await self.page.locator(point_selector).highlight()
                point = await self.page.locator(point_selector).inner_text()
                if point == "Rewards":
                    point = "0"
            else:
                point = "0"
            return int(point)
        except Exception as e:
            log.error(f"获取积分失败: {e}")
        return int(0)
        
    async def get_search_progress(self):
        """
        获取搜索进度，确定一下搜索了多少个
        """
        await asyncio.sleep(2)
        point_selector = 'span[data-tag="RewardsHeader.Counter"]'
        points_locator = self.page.locator(point_selector)
        if await points_locator.count() > 0:
            await points_locator.highlight()
            rewards_text = await points_locator.inner_text()
            if (rewards_text == "Rewards"):
                log.warning("rewards图标没有准备好")
                return
            # 等待它变成可见状态，如果 5 秒还不显示再报错
            try:
                await points_locator.wait_for(state="visible", timeout=5000)
                await points_locator.click()
            except Exception:
                # 动画可能太慢或元素被故意隐藏，直接用 JS 点
                await points_locator.dispatch_event("click")
            #await self.page.locator(point_selector).click()

            # 1. 定位 iframe 本身 (Locate the iframe using a selector)
            # 2. 在该 iframe 内部继续查找元素 (Search inside that frame)
            #iframe_selector = "#rewid-f > iframe" # 或者使用 id, src 等
            iframe_selector = 'iframe[src*="/rewards/panelflyout"]'
            iframe_element = self.page.frame_locator(iframe_selector)
            #if await iframe_element.count() > 0:
             #   log.warning("iframe图标没有准备好")
              #  return
            points_element = iframe_element.get_by_text(re.compile(r"你已获得 \d+ 积分"))
            daily_search_locator = iframe_element.get_by_role("link", name=re.compile(r"每日搜索 \d+\/\d+ 每天搜索并赚取最多 \d+"))
            #daily_search_locator = iframe_element.locator('.daily_search_row span')
            try:
                # 这里的技巧是：等待这两个元素中的任何一个变为 visible
                # 也可以使用 asyncio.wait([task1, task2], return_when=FIRST_COMPLETED)
                
                # 简单有效的做法：
                result = await asyncio.wait([
                    asyncio.create_task(points_element.wait_for(state="visible")),
                    asyncio.create_task(daily_search_locator.wait_for(state="visible"))
                ], return_when=asyncio.FIRST_COMPLETED)
                log.info(f"等待进度完成: {result}")
                # 4. 判断谁先出现了 (Determine which one appeared)
                if await points_element.is_visible():
                    log.success("Action: '你已获得' detected (Success)")
                    text = await points_element.first.inner_text()
                    log.info(f"找到已完成提示: {text}")
                
                    # 提取数字
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        points = int(numbers[0])
                        self.progress_data["total_item"] = points / self.progress_data["per_point"]
                        self.progress_data["search_item"] = points / self.progress_data["per_point"]
                        self.progress_data["is_finish"] = True
                        log.info(f"实际查询进度完成, {self.progress_data}")
                        
                elif await daily_search_locator.is_visible():
                    log.success("Action: 搜索组件 detected (Failure)")
                    progress_text = await daily_search_locator.last.inner_text()
                    log.info(f"找到搜索进度: {progress_text}")
                    real_progress_text = progress_text.strip()
                    
                    # 检查是否是 "数字/60" 的格式
                    progress_match = re.match(r'(\d+)\/(\d+)', real_progress_text)
                    if progress_match:
                        completed = int(progress_match.group(1))
                        total = int(progress_match.group(2))
                        
                        self.progress_data["search_item"] = completed / self.progress_data["per_point"]
                        self.progress_data["total_item"] = total / self.progress_data["per_point"]
                        self.progress_data["is_finish"] = False
                        
                        log.info(f"实际查询进度, {self.progress_data}")
                    else:
                        log.warning(f"无法解析进度文本: {real_progress_text}")
                else:
                    log.warning("无法确定进度")
                log.info("关闭rewards面板")
                await asyncio.sleep(2)
                await iframe_element.locator('#closeEduPanel').highlight()
                await iframe_element.locator('#closeEduPanel').dispatch_event("click")
                log.info("已经关闭rewards面板")
            except Exception as e:
                log.error(f"获取实际查询进度异常: {e}")
        else:
            log.warning("无法点击rewards图标")
    async def random_delay(self):
        """
        生成一个符合对数正态分布的延迟，模拟人类思考停顿。
        """
        delay = self.min_delay + (
            self.max_delay - self.min_delay
        )/10 * random.lognormvariate(0, 1)
        log.info(f"随机延迟 {delay} 秒")
        await asyncio.sleep(delay)

    async def human_delay(self, min_ms=500, max_ms=2000):
        """
        生成一个符合对数正态分布或简单随机的延迟，模拟人类思考停顿。
        """
        # 也可以简单使用均匀分布
        delay = random.uniform(min_ms / 1000, max_ms / 1000)

        # 甚至可以模拟某些时候停顿更久（比如 10% 的概率发呆 3 秒）
        if random.random() < 0.1:
            delay += random.uniform(2, 4)

        await asyncio.sleep(delay)
