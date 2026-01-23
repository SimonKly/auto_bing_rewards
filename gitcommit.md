

# 1. 提交格式标准
一个标准的 Commit Message 应该包含三个部分：Header, Body 和 Footer。

Plaintext

<type>(<scope>): <subject>
// 空行
<body>
// 空行
<footer>
## ① Header (必填)
Header 只有一行，包括三个字段：type（必需）、scope（可选）和 subject（必需）。

Type: 用于说明 commit 的类别。

feat: 新功能 (feature)

fix: 修补 bug

docs: 文档变更 (documentation)

style: 格式说明 (不影响代码运行的变动，如空格、分号等)

refactor: 重构 (即不是新增功能，也不是修改 bug 的代码变动)

perf: 性能优化 (performance)

test: 增加测试

chore: 构建过程或辅助工具的变动 (如：修改 gitignore, npm 依赖安装)

ci: CI 配置文件和脚本的变动

Scope: 说明 commit 影响的范围（如：auth, order-api, readme）。

Subject: 简短描述，不超过 50 个字符。

## ② Body (可选)
对本次提交的详细描述，阐述动机以及修改前后的对比。

## ③ Footer (可选)
主要用于：

不兼容变动 (Breaking Changes)：以 BREAKING CHANGE: 开头，后跟描述。

关闭 Issue：例如 Closes #123 或 Fixes #456。