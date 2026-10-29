# 拾题 · LeetCode Review

个人本地刷题复习工具：把做过的题，变成记住的题。

电脑端网页、单机使用、无需登录。Python 3.11+ 标准库服务与 SQLite，前端资源随项目本地提供，无需 pip 或 npm 安装。

## 启动

Windows 双击 **`start.cmd`**，或在 PyCharm 中直接运行 **`app.py`**，然后打开 http://127.0.0.1:8765 。

```powershell
.\.venv\Scripts\python.exe app.py
```

没有虚拟环境时使用 `python app.py`。关闭服务按 Ctrl+C。

## 第一版功能

- **记录矩阵**：题目 × 日期，连续最近 7 天，最新在左，向右加载更早日期。
- **Hot 100**：100 道题、17 个分类，支持搜索、筛选、手动加题、批量标记以前做过。
- **两种练习**：按类型选题、下一题；在已做题中完全随机复习，默认隐藏类型和历史。
- **Python 编辑器**：语法高亮、缩进、草稿自动保存、一键复制；新一天从空白开始。
- **每日记录**：每题每天一条，手动 ✅/❌，多选与自定义错误标签、错误说明、当次代码。
- **长期笔记**：思路、关键点、注意事项、易错边界、Python 参考代码，支持 Markdown 预览。

不提供运行代码、自动/AI 判题、通过率统计、历史补录、账号同步、备份导入导出或手机专门适配。

## 题目与本机数据

本机数据库位于 `data/review.db`，题面缓存位于 `data/statements.json`，均不进入 Git。

从 GitHub 克隆后首次运行 `start.cmd` 会尝试下载题面，也可手动执行 `python cache_statements.py`，随后重新启动应用。下载失败时允许粘贴原题。题面来自 doocs/leetcode，保留来源与 CC BY-SA 4.0 说明；只提取题面，不引入解法。部分图示需要联网。

详细说明：[使用说明](docs/usage.md) · [需求文档](docs/requirements.md) · [设计决策](docs/decisions.md) · [开发日志](docs/dev-log.md) · [第三方资源](THIRD_PARTY.md)。

## 验证

```powershell
python -m unittest discover -s tests -v
```

测试使用独立临时数据库，覆盖持久化、同日覆盖、跨日草稿、禁止补录、批量标记、API 和静态资源。浏览器交互验收记录见开发日志。

## Git 开发流程

公开仓库：https://github.com/Mist-oo/LeetCode-review 。第一版直接在 `main` 按功能提交。

- 每完成一个可验证的功能或独立修复，检查差异并运行与改动相称的验证。
- 同次提交包含代码、相关文档和开发日志；日志记录完成内容、关键决定、验证结果与遗留问题，不填写自身提交哈希。
- 使用 `feat:`、`fix:`、`docs:`、`chore:` 描述提交用途，提交后推送 GitHub。
- 推送失败保留本地提交，连接恢复后补推；不强制推送或覆盖远程历史。
- 不提交个人数据、IDE 配置、虚拟环境、密钥或生成文件；不建立后台自动提交任务。
