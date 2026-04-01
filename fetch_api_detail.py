"""
爬取单个接口详情页
用法: uv run fetch_api_detail.py nhsoft.amazon.basic.client.address.read
"""
import asyncio
import sys
import re
from pathlib import Path
from playwright.async_api import async_playwright


BASE_URL = "https://console.nhsoft.cn/documents/api-doc"
OUTPUT_DIR = Path("docs/档案/客户详情")

# 账号信息
USERNAME = "haohuihua0220@163.com"
PASSWORD = "!PSWqaz147369"


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


async def expand_all_menus(page):
    """展开所有子菜单"""
    await page.evaluate("""
        async () => {
            for (const el of document.querySelectorAll('.ant-menu-submenu-title')) {
                el.click();
                await new Promise(r => setTimeout(r, 200));
            }
        }
    """)
    await page.wait_for_timeout(1500)


async def click_client_menu(page) -> bool:
    """点击客户菜单"""
    return await page.evaluate("""
        () => {
            const items = document.querySelectorAll('.ant-menu-item');
            for (const item of items) {
                const text = item.innerText.trim();
                if (text === '客户') {
                    item.click();
                    return true;
                }
            }
            return false;
        }
    """)


async def find_and_click_api_in_list(page, method_name: str) -> bool:
    """在分类列表页面中找到并点击指定接口"""
    return await page.evaluate(f"""
        () => {{
            const methodName = {repr(method_name)};
            // 查找所有包含方法名的链接或列表项
            const items = document.querySelectorAll('li.ant-list-item, a');
            for (const item of items) {{
                const text = item.innerText || item.textContent;
                if (text && text.includes(methodName)) {{
                    // 找到后点击链接
                    const link = item.tagName === 'A' ? item : item.querySelector('a');
                    if (link) {{
                        link.click();
                        return true;
                    }}
                    item.click();
                    return true;
                }}
            }}
            return false;
        }}
    """)
    """在菜单中找到并点击指定接口"""
    return await page.evaluate(f"""
        () => {{
            const methodName = {repr(method_name)};
            // 遍历所有菜单项
            const items = document.querySelectorAll('.ant-menu-item');
            for (const item of items) {{
                const text = item.innerText;
                if (text.includes(methodName)) {{
                    item.click();
                    return true;
                }}
            }}
            return false;
        }}
    """)


async def extract_detail_content(page) -> str:
    """提取接口详情页内容，转换为 Markdown 格式"""
    content = await page.evaluate(r"""
        () => {
            const wrapper = document.querySelector('[class*="content-wrapper"]');
            if (!wrapper) return '';

            const lines = [];

            function walk(el) {
                if (!el || el.nodeType !== 1) return;
                const tag = el.tagName.toLowerCase();
                const cls = (el.className || '').toString();

                if (cls.includes('breadcrumb') || tag === 'nav') return;

                // 处理表格
                if (tag === 'table') {
                    const rows = [];
                    el.querySelectorAll('tr').forEach(tr => {
                        const cells = [];
                        tr.querySelectorAll('th, td').forEach(td => {
                            cells.push(td.innerText.trim().replace(/\n/g, ' '));
                        });
                        if (cells.some(c => c)) rows.push(cells);
                    });
                    if (rows.length) {
                        lines.push('| ' + rows[0].join(' | ') + ' |');
                        lines.push('| ' + rows[0].map(() => '---').join(' | ') + ' |');
                        for (let i = 1; i < rows.length; i++) {
                            const row = [...rows[i]];
                            while (row.length < rows[0].length) row.push('');
                            lines.push('| ' + row.join(' | ') + ' |');
                        }
                        lines.push('');
                    }
                    return;
                }

                // 处理标题
                if (['h1','h2','h3','h4','h5','h6'].includes(tag)) {
                    const text = el.innerText.trim();
                    if (text) lines.push('#'.repeat(parseInt(tag[1])) + ' ' + text);
                    return;
                }

                // 处理代码块
                if (tag === 'pre') {
                    const text = el.innerText.trim();
                    if (text) lines.push('```\n' + text + '\n```');
                    return;
                }

                // 处理段落
                if (tag === 'p') {
                    const text = el.innerText.trim();
                    if (text) lines.push(text);
                    return;
                }

                // 递归处理子元素
                for (const child of el.children) {
                    walk(child);
                }
            }

            walk(wrapper);
            return lines.join('\n');
        }
    """)
    if not content:
        return ""
    return re.sub(r'\n{3,}', '\n\n', content).strip()


async def fetch_api_detail(method_name: str):
    """获取指定接口的详情"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("正在访问文档页面...")
        await page.goto(BASE_URL, wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # 检查是否需要登录
        if "/user/login" in page.url:
            print("需要登录...")
            await page.fill('input[id="username"], input[placeholder="请输入账号"]', USERNAME)
            await page.fill('input[id="password"], input[placeholder="请输入密码"], input[type="password"]', PASSWORD)
            await page.click('button[type="submit"], .ant-btn-primary, button:has-text("登录")')
            await page.wait_for_timeout(3000)

            # 重新访问文档页面
            await page.goto(BASE_URL, wait_until="networkidle")
            await page.wait_for_timeout(3000)

        print(f"正在查找接口: {method_name}")

        # 展开所有菜单
        print("展开导航菜单...")
        await expand_all_menus(page)

        # 获取所有菜单文本用于调试
        menu_items = await page.evaluate(r"""
            () => {
                const items = [];
                document.querySelectorAll('.ant-menu-item').forEach(item => {
                    items.push(item.innerText.trim());
                });
                return items;
            }
        """)

        # 查找包含客户相关内容的菜单
        client_items = [item for item in menu_items if '客户' in item or 'client' in item.lower()]
        print(f"找到 {len(client_items)} 个客户相关菜单项:")
        for item in client_items[:5]:
            print(f"  - {item[:80]}")

        # 点击客户菜单
        print("点击客户菜单...")
        if not await click_client_menu(page):
            print("未找到客户菜单")
            await browser.close()
            return False

        await page.wait_for_timeout(2000)

        # 在列表中查找并点击接口
        print(f"在客户分类中查找接口: {method_name}")
        clicked = await find_and_click_api_in_list(page, method_name)
        if not clicked:
            print(f"未在客户分类中找到接口: {method_name}")
            await browser.close()
            return False

        print(f"已找到接口，等待加载详情...")
        await page.wait_for_timeout(2000)

        # 提取内容
        content = await extract_detail_content(page)

        if not content:
            print("未能提取到内容，尝试备用方式...")
            content = await page.evaluate(r"""
                () => {
                    const el = document.querySelector('[class*="content-wrapper"]');
                    return el ? el.innerText.trim() : '';
                }
            """)

        if not content:
            print("提取内容失败")
            await browser.close()
            return False

        # 生成文件名
        filename = sanitize_filename(method_name) + ".md"
        filepath = OUTPUT_DIR / filename

        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {method_name}\n\n{content}")

        print(f"已保存到: {filepath}")
        print(f"内容长度: {len(content)} 字符")

        await browser.close()
        return True


if __name__ == "__main__":
    method_name = sys.argv[1] if len(sys.argv) > 1 else "nhsoft.amazon.basic.client.address.read"
    result = asyncio.run(fetch_api_detail(method_name))
    sys.exit(0 if result else 1)
