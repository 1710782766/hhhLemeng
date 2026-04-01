"""调试脚本：分析页面结构和内容提取问题"""
import asyncio
from playwright.async_api import async_playwright


async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 可见模式方便调试
        page = await browser.new_page()

        await page.goto("https://console.nhsoft.cn/documents/api-doc", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # 1. 展开所有子菜单
        print("=== 展开子菜单 ===")
        await page.evaluate("""
            async () => {
                const submenus = document.querySelectorAll('.ant-menu-submenu-title');
                for (const item of submenus) {
                    item.click();
                    await new Promise(r => setTimeout(r, 300));
                }
            }
        """)
        await page.wait_for_timeout(2000)

        # 2. 查看正确的菜单结构（只取顶层直接子项）
        print("=== 菜单结构（去重版）===")
        nav = await page.evaluate("""
            () => {
                const result = [];
                // 找到根菜单（最外层）
                const rootMenu = document.querySelector('.ant-menu.ant-menu-root');
                if (!rootMenu) return [{error: 'no root menu'}];

                // 只遍历直接子 li
                for (const el of rootMenu.children) {
                    if (el.classList.contains('ant-menu-submenu')) {
                        const titleEl = el.querySelector(':scope > .ant-menu-submenu-title .ant-menu-title-content');
                        const groupName = titleEl ? titleEl.textContent.trim() : '';

                        // 子菜单的直接子项
                        const subUl = el.querySelector(':scope > ul');
                        if (subUl) {
                            for (const child of subUl.children) {
                                if (child.classList.contains('ant-menu-item')) {
                                    const c = child.querySelector('.ant-menu-title-content');
                                    if (c) result.push({ group: groupName, name: c.textContent.trim() });
                                }
                            }
                        }
                    } else if (el.classList.contains('ant-menu-item')) {
                        const c = el.querySelector('.ant-menu-title-content');
                        if (c) result.push({ group: '', name: c.textContent.trim() });
                    }
                }
                return result;
            }
        """)
        for item in nav:
            print(f"  {item}")

        # 3. 点击"全局说明"，检查内容区域
        print("\n=== 点击全局说明，检查内容 ===")
        await page.click('.ant-menu-item:first-child')
        await page.wait_for_timeout(2000)

        # 检查所有可能的内容容器
        content_check = await page.evaluate("""
            () => {
                const selectors = [
                    '.ant-layout-content',
                    '[class*="content"]',
                    '[class*="Content"]',
                    'main',
                    '.markdown-body',
                ];
                const result = {};
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    result[sel] = el ? el.innerText.substring(0, 200) : null;
                }
                // 另外输出 body 前200字
                result['body'] = document.body.innerText.substring(0, 500);
                return result;
            }
        """)
        for sel, text in content_check.items():
            if text:
                print(f"\n[{sel}]:\n{text[:200]}")

        # 4. 点击"档案 > 商品"
        print("\n\n=== 点击档案>商品，检查内容 ===")
        clicked = await page.evaluate("""
            () => {
                const items = document.querySelectorAll('.ant-menu-item .ant-menu-title-content');
                for (const el of items) {
                    if (el.textContent.trim() === '商品') {
                        el.closest('.ant-menu-item').click();
                        return true;
                    }
                }
                return false;
            }
        """)
        print(f"点击成功: {clicked}")
        await page.wait_for_timeout(2000)

        body_text = await page.evaluate("() => document.body.innerText.substring(0, 1000)")
        print(f"body innerText:\n{body_text}")

        # 5. 检查所有类名
        all_classes = await page.evaluate("""
            () => {
                const classes = new Set();
                document.querySelectorAll('[class]').forEach(el => {
                    el.className.split(' ').forEach(c => {
                        if (c && (c.includes('content') || c.includes('main') || c.includes('doc'))) {
                            classes.add(c);
                        }
                    });
                });
                return [...classes];
            }
        """)
        print(f"\n内容相关的类名: {all_classes}")

        await page.screenshot(path="debug.png", full_page=True)
        print("\n截图保存到 debug.png")

        input("按回车关闭浏览器...")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug())
