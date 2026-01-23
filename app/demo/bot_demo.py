from playwright.sync_api import expect
import re
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import random
import math

async def run():
    # This is the recommended usage. All pages created will have stealth applied:
    async with Stealth().use_async(async_playwright()) as p:
        try:
            # 1. 启动浏览器
            # 建议调试时 headless=False，部署时再改为 True
            browser = await p.chromium.launch(
                headless=False,
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
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                # 额外加固：设置语言和硬件并发数，让指纹更像真人
                locale="zh-CN",
                device_scale_factor=1,
            )

            page = await context.new_page()

            # 在 page = await context.new_page() 之后立即执行
            cdp_session = await context.new_cdp_session(page)
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

            webdriver_status = await page.evaluate("navigator.webdriver")
            print("from new_page: ", webdriver_status)

            print("正在访问 bing.com...")
            # 使用 networkidle 确保 JS 加载完成，防止白屏
            await page.goto(
                "https://cn.bing.com/", wait_until="domcontentloaded", timeout=600000
            )
            # 检查是否成功加载
            title = await page.title()
            print(f"页面标题: {title}")
            # 验证
            ua_in_js = await page.evaluate("navigator.userAgent")
            print(f"JS 中的 UA: {ua_in_js}")

            login_btn = 'a[id="id_l"]'
            # await page.wait_for_selector(login_btn, state="visible")
            # 调试：高亮一下看看找对没
            await page.locator(login_btn).highlight()
            await asyncio.sleep(1)  # 仅调试用，让人眼看清楚
            await page.locator(login_btn).click(force=True)

            print(f"点击了登陆按钮")

            # 4. 在新页面填写账号密码
            # Playwright 的 page 对象依然指向当前标签页，所以直接继续用 page 操作即可
            username_input = 'label[for="usernameEntry"]'
            await page.wait_for_selector(username_input)
            print("已到达登录页面，开始输入...")
            # 验证
            ua_in_js = await page.evaluate("navigator.userAgent")
            print(f"JS 中的 UA: {ua_in_js}")
            await page.locator(username_input).click()
            await page.locator(username_input).fill("*")
            next_btn = 'button[type="submit"]'
            await page.wait_for_selector(next_btn)
            await page.locator(next_btn).click()
            # 切换登陆方法
            switch_login_type_a = "a[id = 'idA_PWD_SwitchToCredPicker']"
            if await page.locator(switch_login_type_a).count() > 0:
                await page.locator(switch_login_type_a).click()
            else:
                await page.get_by_role("button", name="其他登录方法").click()
            await page.get_by_label("使用密码").locator("div").first.click()
            await page.get_by_label("密码", exact=True).click()
            await page.get_by_label("密码", exact=True).fill("")
            await page.get_by_test_id("primaryButton").click()
            await page.get_by_test_id("primaryButton").click()
            input_form = "input[name='q']"
            await page.locator(input_form).click()

            # 演示：等待输入框出现
            # await page.wait_for_selector('input[type="email"]', timeout=10000)
            print("成功进入登录页面！")

            # 此处可以进行后续操作...
            await asyncio.sleep(5)

        except Exception as e:
            print(f"发生错误: {e}")
            print(f"超时时的 URL: {page.url}")
            # 截图看看是不是还在 Bing 首页，或者是一个白屏
            await page.screenshot(path="debug_timeout.png")
        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run())

