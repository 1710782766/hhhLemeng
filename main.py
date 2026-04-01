"""
乐檬开放平台文档爬虫（两层结构）
- 第一层：导航菜单（分组 + 分类）
- 第二层：分类页面（API 列表 + 基础信息）
"""
import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright


BASE_URL = "https://console.nhsoft.cn/documents/api-doc"
OUTPUT_DIR = Path("docs")


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


async def expand_all_menus(page):
    await page.evaluate("""
        async () => {
            for (const el of document.querySelectorAll('.ant-menu-submenu-title')) {
                el.click();
                await new Promise(r => setTimeout(r, 200));
            }
        }
    """)
    await page.wait_for_timeout(1500)


async def get_nav_items(page) -> list:
    """获取菜单结构（只取直接子项，避免重复）"""
    return await page.evaluate("""
        () => {
            const result = [];
            const rootMenu = document.querySelector('.ant-menu.ant-menu-root');
            if (!rootMenu) return result;
            for (const el of rootMenu.children) {
                if (el.classList.contains('ant-menu-submenu')) {
                    const titleEl = el.querySelector(':scope > .ant-menu-submenu-title .ant-menu-title-content');
                    const groupName = titleEl ? titleEl.textContent.trim() : '';
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


async def click_menu_item(page, name: str) -> bool:
    return await page.evaluate(f"""
        () => {{
            for (const el of document.querySelectorAll('.ant-menu-item .ant-menu-title-content')) {{
                if (el.textContent.trim() === {json.dumps(name)}) {{
                    el.closest('.ant-menu-item').click();
                    return true;
                }}
            }}
            return false;
        }}
    """)


async def extract_content(page) -> str:
    """提取内容区域，转换为 Markdown 格式"""
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

                if (['h1','h2','h3','h4','h5','h6'].includes(tag)) {
                    const text = el.innerText.trim();
                    if (text) lines.push('#'.repeat(parseInt(tag[1])) + ' ' + text);
                    return;
                }

                if (tag === 'pre') {
                    const text = el.innerText.trim();
                    if (text) lines.push('```\n' + text + '\n```');
                    return;
                }

                if (tag === 'p') {
                    const text = el.innerText.trim();
                    if (text) lines.push(text);
                    return;
                }

                if (tag === 'li') {
                    // 分类列表页：提取 API 条目信息
                    if (el.classList.contains('ant-list-item')) {
                        const nameEl = el.querySelector('.ant-list-item-meta-title');
                        const linkEl = el.querySelector('a');
                        const descEl = el.querySelector('.ant-list-item-meta-description');
                        const name = nameEl ? nameEl.innerText.trim() : el.innerText.split('\n')[0].trim();
                        const method = linkEl ? linkEl.textContent.trim() : '';
                        const desc = descEl ? descEl.innerText.trim() : '';
                        if (name || method) {
                            lines.push(`- **${name}**`);
                            if (method) lines.push(`  - 方法名：\`${method}\``);
                            if (desc) lines.push(`  - ${desc}`);
                        }
                        return;
                    }
                    const text = el.innerText.trim();
                    if (text) lines.push('- ' + text);
                    return;
                }

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


async def scrape_docs():
    # 清空旧文档
    if OUTPUT_DIR.exists():
        import shutil
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("正在加载文档页面...")
        await page.goto(BASE_URL, wait_until="networkidle")
        await page.wait_for_timeout(3000)

        print("正在展开导航菜单...")
        await expand_all_menus(page)

        nav_items = await get_nav_items(page)
        print(f"共找到 {len(nav_items)} 个分类\n")

        with open(OUTPUT_DIR / "_nav.json", "w", encoding="utf-8") as f:
            json.dump(nav_items, f, ensure_ascii=False, indent=2)

        groups: dict[str, list] = {}
        for item in nav_items:
            g = item["group"] or "通用"
            groups.setdefault(g, []).append(item)

        saved = 0

        for group_name, items in groups.items():
            group_dir = OUTPUT_DIR / sanitize_filename(group_name)
            group_dir.mkdir(exist_ok=True)
            print(f"=== {group_name} ({len(items)} 个) ===")

            for item in items:
                name = item["name"]
                print(f"  > {name}", end="", flush=True)

                clicked = await click_menu_item(page, name)
                if not clicked:
                    print(" [未找到]")
                    continue

                await page.wait_for_timeout(1500)
                content = await extract_content(page)

                if not content:
                    # 备用：直接取 innerText
                    content = await page.evaluate(r"""
                        () => {
                            const el = document.querySelector('[class*="content-wrapper"]');
                            return el ? el.innerText.trim() : '';
                        }
                    """)

                if not content:
                    print(" [空]")
                    continue

                filepath = group_dir / (sanitize_filename(name) + ".md")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"# {name}\n\n{content}")

                saved += 1
                print(f" [{len(content)} 字符]")

        await browser.close()

    # 生成总索引
    with open(OUTPUT_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write("# 乐檬开放平台 API 文档\n\n")
        current_group = None
        for item in nav_items:
            g = item["group"] or "通用"
            if g != current_group:
                f.write(f"\n## {g}\n\n")
                current_group = g
            name = item["name"]
            f.write(f"- [{name}]({sanitize_filename(g)}/{sanitize_filename(name)}.md)\n")

    print(f"\n完成！共保存 {saved} 个文档")
    print(f"文档目录：{OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    asyncio.run(scrape_docs())
