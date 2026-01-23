from playwright.sync_api import expect
import re
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import random
import math


class RewardsBot:
    """
    RewardsBot类，用于执行账户任务。
    """

    BING_URL = "https://www.bing.com"
    LOGIN_URL = "https://login.live.com"

    REWARDS_BING_URL = "https://rewards.bing.com/"

    def __init__(self, slow_mo=0, type="pc", min_delay=60, max_delay=90):
        """
        初始化playwright实例。
        """
        self.slow_mo = slow_mo
        self.type = type
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def open_brower(self, headless=False):
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
            # 1. 获取内置的 iPhone 13 模拟参数
            iphone_13 = self.playwright.devices['iPhone 13']
            # 1. 启动浏览器
            # 建议调试时 headless=False，部署时再改为 True
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",  # 禁用受控标志
                    "--no-sandbox",
                    # === 核心参数：禁用 WebAuthn ===
                    # 这会告诉网站：当前浏览器不支持 USB 密钥或生物识别
                    "--disable-features=WebAuthentication",
                    "--disable-features=WebAuthenticationProxy",
                    # 某些版本的 Chrome 可能还需要这个：
                    "--disable-external-intent-requests",
                ],
            )
            # 2. 创建上下文，设置视口大小 # 1. context 不要传 user_agent，让 stealth 来处理
            if self.type == "mobile":
                iphone_13 = self.playwright.devices['iPhone 13']
                self.context = await self.browser.new_context(**iphone_13)
            elif self.type == "pc":
                    self.context = await self.browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    # 额外加固：设置语言和硬件并发数，让指纹更像真人
                    locale="zh-CN",
                    device_scale_factor=1,
                )
            
            else:
                raise ValueError("Invalid type specified. Please use 'mobile' or 'pc'.")

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
            print("from new_page: ", webdriver_status)
            # 验证
            ua_in_js = await self.page.evaluate("navigator.userAgent")
            print(f"JS 中的 UA: {ua_in_js}")
            print("浏览器打开完成")

        except Exception as e:
            print(f"执行账户任务时出现错误: {str(e)}")
            await self.close()

    async def close(self):
        """
        关闭浏览器。
        """
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright_mgr:
            # 这里的 __aexit__ 会处理 playwright 实例的销毁
            await self.playwright_mgr.__aexit__()
        try:
            await self.context.close()
            await self.browser.close()
            print("浏览器已关闭")
        except Exception as e:
            print(f"关闭浏览器错误: {str(e)}")

    async def execute_account_task(
        self, account, password, search_term_list: list[str]
    ):
        """执行账户搜索任务。

        Args:
            account (str): 账号email
            password (str): 密码
            search_term_list (list[str]): 搜索词条列表
        """
        # 1. open browser
        await self.open_brower()
        # 2. login to bing
        await self.login(account, password)
        # 3. open bing page
        await self.open_bing()
        # 3. iterate over search terms
        first_point_current_date = await self.get_reward_points()
        print(f"今日的积分: {first_point_current_date}")
        for search_term in search_term_list:
            # 3.1. run search task
            await self.search(search_term)
            # 3.2. wait for a while
            await self.random_delay()
            realtime_point_current_date = await self.get_reward_points()
            print(f"实时的积分: {realtime_point_current_date}")
        # 4. close browser
        await self.close()
        print("任务完成！")

    async def open_bing(self):
        """
        打开必应首页。
        """
        print("正在访问 bing.com...")
        # 不使用 networkidle 后台一直发送请求
        await self.page.goto(
            RewardsBot.BING_URL + "/?wlexpsignin=1&synset=1", wait_until="domcontentloaded", timeout=600000
        )
        # 检查是否成功加载
        title = await self.page.title()
        print(f"页面标题: {title}")
        await self.human_delay()
        
        # 点击一下登陆按钮
        if self.type == "mobile":
            menu_selector = 'a[id="mHamburger"]'
            await self.page.locator(menu_selector).click()
            login_btn = 'div[id="hb_s"]'
            await self.page.locator(login_btn).click()
            await self.human_delay()
            menu_selector = 'a[id="mHamburger"]'
            await self.page.locator(menu_selector).click()
            not_menu_selector = 'div[id="HBleft"]'
            await self.page.locator(not_menu_selector).click()
            await self.page.reload()
            await asyncio.sleep(3)
        else:
            login_btn = '#id_l'
            await self.page.locator(login_btn).highlight()
            await self.page.locator(login_btn).click(force=True)
            await self.human_delay()
            await self.page.goto(
            RewardsBot.BING_URL + "/?wlexpsignin=1&synset=1", wait_until="domcontentloaded", timeout=600000
        )
            await asyncio.sleep(5)
            
        
        print("bing页面打开完成")
    async def login(self, account, password):
        """
        打开必应登录页面。
        """
        print(f"正在访问 ${RewardsBot.LOGIN_URL}...")
        await self.page.goto(
            RewardsBot.LOGIN_URL, wait_until="domcontentloaded", timeout=600000
        )
        # 检查是否成功加载
        title = await self.page.title()
        print(f"页面标题: {title}")
        
        # login_btn = 'a[id="id_l"]'
        # # await page.wait_for_selector(login_btn, state="visible")
        # # 调试：高亮一下看看找对没
        # await self.page.locator(login_btn).highlight()
        # await asyncio.sleep(1)  # 仅调试用，让人眼看清楚
        # await self.page.locator(login_btn).click(force=True)
        # await self.human_delay()
        # print(f"点击了登陆按钮")

        # 4. 在新页面填写账号密码
        # Playwright 的 page 对象依然指向当前标签页，所以直接继续用 page 操作即可
        username_input = 'label[for="usernameEntry"]'
        await self.page.wait_for_selector(username_input)
        print("已到达登录页面，开始输入...")

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
        # if await self.page.locator(switch_login_type_a).count() > 0:
        #     await self.page.locator(switch_login_type_a).click()
        #     await self.human_delay()
        # else:
        #     await self.page.get_by_role("button", name="其他登录方法").click()
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
        await self.page.get_by_test_id("primaryButton").click()
        await self.human_delay()
        # input_form = "input[name='q']"
        # await self.page.locator(input_form).click()
        # await self.human_delay()

        await asyncio.sleep(2)
        print("成功进入登录页面！")

    async def search(self, search_term: str):
        print(f"search_term: {search_term}的搜索开始")
        input_form = "#sb_form_q"
        await self.page.locator(input_form).highlight()
        await self.page.locator(input_form).clear()
        await self.page.locator(input_form).press_sequentially(
            search_term, delay=random.uniform(50, 150)
        )
        
        await self.page.locator(input_form).press("Enter")
        # submit_icon = 'label[id="search_icon"]'
        # submit_btn = 'input[id="sb_form_go"]'
        # await self.page.locator(submit_btn).or_(self.page.locator(submit_icon)).highlight()
        # await self.page.locator(submit_btn).or_(self.page.locator(submit_icon)).click()
        # 每次滚动随机距离
        distance = random.randint(400, 800)
        # await self.page.mouse.wheel(0, distance)
        await self.page.mouse.wheel(0, 1000)
        await self.human_delay()
        print(f"search_term: {search_term}的搜索完成")
        
    async def get_reward_points(self) -> int:
        """
        获取账户的积分。
        """
        if self.type == "mobile":
            menu_selector = 'a[id="mHamburger"]'
            await self.page.locator(menu_selector).click()
            await self.human_delay()
            point_selector = 'span[id="fly_id_rc"]'
            point = await self.page.locator(point_selector).inner_text()
            print(f"账户积分: {point}")
            if point == "":
                point = "0"
            not_menu_selector = 'div[id="HBleft"]'
            await self.page.locator(not_menu_selector).click()
        else:
            point_selector = 'span[data-tag="RewardsHeader.Counter"]'
            if await self.page.locator(point_selector).count() > 0:
                await self.page.locator(point_selector).highlight()
                point = await self.page.locator(point_selector).inner_text()
            else:
                point = "0"
        
        return int(point)
        
        
    async def random_delay(self):
        """
        生成一个符合对数正态分布的延迟，模拟人类思考停顿。
        """
        delay = self.min_delay + (
            self.max_delay - self.min_delay
        ) * random.lognormvariate(0, 1)
        print(f"随机延迟 {delay} 秒")
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
