# 第三方资源与题面出处

应用前端使用以下固定版本的本地资源，日常使用不访问 npm 或 CDN：

| 资源 | 版本 | 用途 | 许可文件 |
| --- | --- | --- | --- |
| [CodeMirror](https://github.com/codemirror/codemirror5) | 5.65.21 | Python 语法高亮、缩进、行号 | static/vendor/CODEMIRROR-LICENSE |
| [Marked](https://github.com/markedjs/marked) | 15.0.12 | Markdown 渲染 | static/vendor/MARKED-LICENSE |
| [DOMPurify](https://github.com/cure53/DOMPurify) | 3.2.7 | 清理题面和笔记 HTML | static/vendor/DOMPURIFY-LICENSE |

这些文件从 npm 官方 registry 的对应版本包获取，保留原始许可。DOMPurify 提供 Apache-2.0 或 MPL-2.0 许可选择，详见所附文件。

## Hot 100 与题目内容

- 题单参照 [力扣热题 100](https://leetcode.cn/studyplan/top-100-liked/)，本项目固定一份 100 题、17 分类的目录，不自动跟随官方题单变化。
- 题目归 LeetCode 及对应权利人所有；本工具不提供解法、不执行或判定代码，也不代表 LeetCode 官方。
- 力扣官网拒绝程序化读取时，使用 [doocs/leetcode](https://github.com/doocs/leetcode) 的中文题面副本作为本机缓存来源。该仓库声明 [CC BY-SA 4.0](https://github.com/doocs/leetcode/blob/main/LICENSE)。
- `cache_statements.py` 只提取 README 中 description:start 至 description:end 的题面区段，不提取解法、思路或参考答案。缓存保留上游提交固定链接，并在题面下方展示来源、提取说明和许可链接。
- 题面缓存保存在 `data/statements.json`，属于本机数据，不提交 Git；重新下载时可能得到新的上游版本。导入不会覆盖已经保存的题面或用户修改。
- 原题图示通过原地址加载，需要联网；题面文字、代码编辑、记录和笔记可离线使用。实际题意以力扣原题链接为准。

## 第二版本地 Python 依赖

- Jedi 0.19.2：Python 静态补全，MIT，https://github.com/davidhalter/jedi 。
- Parso 0.8.7：Jedi 的 Python 解析依赖，MIT，https://github.com/davidhalter/parso 。
- psutil 7.2.2：运行进程与内存监控，BSD-3-Clause，https://github.com/giampaolo/psutil 。
- CodeMirror show-hint 使用同一 5.65.21 包中的原始 JS/CSS，沿用已附 MIT 许可。
- CodeMirror closebrackets 使用 [5.65.21 官方源码](https://github.com/codemirror/codemirror5/blob/5.65.21/addon/edit/closebrackets.js)，保留原文件版权声明，沿用已附 MIT 许可。

Python 包通过 requirements.txt 安装，原许可位于各安装包中；不把虚拟环境上传仓库。补全不调用远程模型，测试数据与参考/独立计算由本项目实现，不来自官方隐藏测试。
