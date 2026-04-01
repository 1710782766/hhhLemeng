# hhhLemeng

对接乐檬开放平台的中间层服务，基于 Tornado 异步框架。

## 快速开始

```bash
# 安装依赖
uv sync

# 启动服务（端口8167）
cd hhh_lemeng && uv run python server.py

# 爬取API文档
uv run main.py
```

## 项目结构

- `hhh_lemeng/` - 生产服务（Tornado）
- `docs/` - API 文档
- `main.py` / `fetch_api_detail.py` - 文档爬虫
