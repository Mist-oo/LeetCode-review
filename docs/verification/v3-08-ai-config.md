# V3-08：AI 服务配置

日期：2026-10-30。状态：配置功能通过；未在本阶段声称模型生成已实现。

- 首页设置表单、按数据库隔离的本地配置、URL/模型/密钥校验、原子保存、空密钥保留与显式清除、损坏配置恢复。
- 密钥写入后，GET/PUT 返回仅含 has_key/configured 标记，界面密码框不回填；本地文件未声称加密，个人文件和临时文件被 Git 忽略。
- tests/test_ai_settings.py：5 项通过。tests/test_http.py：9 项通过，含配置 API 与临时库配置隔离、静态目录不能暴露配置。
- tests/browser/v3-ai-settings.js：8 项通过，实际表单保存、URL 规范化、无密钥回显、留空保留、坏 URL、显式清除以及无远程请求。
- 所有测试使用虚构测试值，example.invalid 仅作地址校验；保存未触发远程调用。界面错误分支的 400 资源请求为预期验证，不描述为真实模型成功。
- 接口兼容范围依据 [OpenAI Chat Completions 参考](https://developers.openai.com/api/reference/resources/chat)，具体调用/响应与语义检查在 V3-09 验收。
