# 文档 + Flask + Microsoft Entra ID 身份验证

[English](README.md) | 简体中文 | [Deutsch](README.de.md)

[![CI](https://github.com/xiepei1/mkdocs-msal-auth/actions/workflows/ci.yml/badge.svg)](https://github.com/xiepei1/mkdocs-msal-auth/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MkDocs](https://img.shields.io/badge/MkDocs-1.6.1-000000)](https://www.mkdocs.org/)
[![uv](https://img.shields.io/badge/deps-uv-DE5FE9?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![License](https://img.shields.io/badge/License-MIT-green?logo=open-source-initiative&logoColor=white)](#许可证)

本项目用 [MkDocs](https://www.mkdocs.org/) 和 [Material](https://squidfunk.github.io/mkdocs-material/) 主题构建文档。Flask 提供生成的静态站点。访问受 Microsoft Entra ID (Azure AD) 保护。Python 端使用 MSAL。

## 架构

1. MkDocs 把静态 HTML 构建到 `site/` 文件夹。
2. Flask 从 `site/` 提供文件。
3. 未登录用户被重定向到 Microsoft Entra ID 登录页。
4. 登录成功后，Flask 把用户身份存入安全会话。
5. 你可以按邮箱域名和指定邮箱地址限制访问。

## 功能

- 用 MkDocs 和 Material 主题生成文档
- 用 Flask 服务器托管生成的 HTML
- 通过 MSAL 使用 Microsoft Entra ID OAuth2 授权码流程
- 用 `allowed_domains` 和 `allowed_emails` 控制访问
- 运行时配置来自环境变量。本地开发用 `.env`。

## 快速开始

依赖用 [uv](https://docs.astral.sh/uv/) 管理。

1. 安装依赖：

```bash
uv sync
```

2. 复制环境变量模板并填入取值：

```bash
cp .env.example .env
```

3. 构建文档：

```bash
uv run mkdocs build
```

4. 启动本地服务器：

```bash
uv run python -m app.webapp.server
```

5. 打开 `http://localhost:5000`。

## 编写文档

你把内容写成 `docs/` 下的 Markdown 文件。MkDocs 把这些文件构建为 `site/` 下的静态 HTML。Flask 服务器确认登录状态后提供该 HTML。`docs/` 下的每个页面都属于受保护站点。

### 添加页面

1. 在 `docs/` 下创建 Markdown 文件。文件 `docs/guides/api.md` 对应 URL `/guides/api/`。
2. 在文件顶部放一个一级标题。主题把该标题显示为页面标题。
3. 用相对当前文件的路径链接到其他页面。链接 `[Setup](setup.md)` 可从 `docs/index.md` 使用。
4. 运行 `uv run mkdocs build` 并阅读输出。确保构建没有报告错误。

### 设置菜单顺序

`mkdocs.yml` 没有 `nav` 键。所以 Material 主题按文件夹结构和文件名构建菜单。若你要固定顺序和自定义标题，请在 `mkdocs.yml` 中添加 `nav` 键：

```yaml
nav:
  - Home: index.md
  - Setup: setup.md
  - Writing: writing.md
```

`nav` 中的路径相对于 `docs/`。MkDocs 会构建不在 `nav` 中的页面，并在构建日志中列出它们。这些页面仍可通过 URL 访问。

### 用文件夹组织页面

`docs/` 下的子文件夹成为 URL 路径中的一段。`docs/guides/` 下的页面 URL 以 `/guides/` 开头。文件夹名成为 URL 名。请用带连字符的短名。避免空格和大写字母。

### 添加图片和静态文件

把图片和其他静态文件放在 `docs/assets/` 下。用相对页面文件的路径链接它们。文件 `docs/assets/diagram.png` 从 `docs/index.md` 需要链接 `assets/diagram.png`。该文件从 `docs/guides/api.md` 需要链接 `../assets/diagram.png`。

不要把私密内容放在 `/auth/`、`/login/`、`/assets/`、`/images/`、`/javascripts/` 或 `/stylesheets/` 下。服务器不经过登录步骤就提供这些路径前缀。任何人都能读取该内容。

### 用宏复用取值

macros 插件已启用。它在构建时把 Markdown 中的 Jinja 表达式替换为取值。在 `mkdocs.yml` 的 `extra` 下定义取值：

```yaml
extra:
  owner: Platform Team
```

然后在任意页面使用它：

```markdown
This site is maintained by {{ owner }}.
```

该插件还向 Markdown 暴露 `config`、`page`、`files` 和 `navigation`。页面可在文件顶部的 YAML front matter 块中定义自己的取值。当页面必须显示字面量 `{{` 或 `}}` 时，请用 `{% raw %}` 和 `{% endraw %}` 包裹该文本。

### 预览与重新构建

1. 运行 `uv run mkdocs serve` 获得实时预览。它在每次保存时重新加载。该预览没有登录步骤。
2. 每轮编辑后运行 `uv run mkdocs build`。Flask 服务器读取 `site/`。它不重建文档。

构建通过 `mkdocs-simple-hooks` 运行 `app/mkdocs_msal_auth/hooks.py` 中的钩子。钩子读取 `extra.auth` 并把其取值传给主题模板。它们不改你的页面 Markdown。

## 开发

```bash
uv run pytest            # run the test suite
uv run ruff check .      # lint
uv run mkdocs serve      # live docs preview
```

测试套件不需要 Entra ID 凭据。它不发起网络调用。它覆盖访问允许列表、豁免路径规则、配置加载，以及登录和回调流程的每个分支。

`pyproject.toml` 是依赖的唯一事实来源。`uv.lock` 固定确切版本。拉取变更后运行 `uv sync`。用 `uv add <package>` 添加依赖。用 `uv add --dev <package>` 添加开发工具。

## 生产运行 (WSGI)

用 Gunicorn 和 WSGI 入口点：

```bash
.venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 3 app.webapp.wsgi:app
```

可选加固：

- 通过 HTTPS 提供服务时，设置 `SESSION_COOKIE_SECURE=true`。
- 始终设置一个强的 `SECRET_KEY`。

## 必需的环境变量

- `CLIENT_ID`：Entra 应用（客户端）ID
- `CLIENT_SECRET`：Entra 客户端密钥
- `TENANT_ID`：Entra 租户 ID
- `AUTHORITY`（可选）：覆盖默认值 `https://login.microsoftonline.com/<TENANT_ID>`
- `SECRET_KEY`：Flask 会话签名密钥

## Entra 应用注册

在 Microsoft Entra 管理中心：

1. 注册一个应用。
2. 添加 Web 重定向 URI：`http://localhost:5000/auth/authorized`。也可以填你的生产 URL。
3. 创建客户端密钥。
4. 授予委托权限 `User.Read`（Microsoft Graph）。

## 访问策略配置

`mkdocs.yml` 中的 `extra.auth` 是可选的。若完全省略它，应用仍用这些默认值工作：

- 启用身份验证
- 无域名允许列表
- 无邮箱允许列表

添加此节以覆盖默认值：

```yaml
extra:
  auth:
    enabled: true
    allowed_domains: []
    allowed_emails: []
```

行为：

- 若缺少 `extra.auth`，MSAL 身份验证仍以默认行为生效。
- 若两个列表都为空，任何成功通过身份验证的 Entra 用户都获准访问。
- 若任一列表有取值，用户必须匹配允许的域名或邮箱之一。

## Docker

```bash
docker build -t mkdocs-msal-auth .
docker run -p 5000:5000 \
  -e CLIENT_ID="your-client-id" \
  -e CLIENT_SECRET="your-client-secret" \
  -e TENANT_ID="your-tenant-id" \
  -e SECRET_KEY="your-secret-key" \
  -e SESSION_COOKIE_SECURE=true \
  mkdocs-msal-auth
```

镜像从 `uv.lock` 安装依赖。它在镜像构建时构建文档站点。

## 冒烟检查

查看访问流程最快的方式是启动服务器并打开站点。对 `/` 的未登录请求必须重定向到 `/auth/login`。

## 源码布局

```
.
├── .claude/settings.json       代理命令允许列表
├── .github/
│   ├── instructions/           指向 AGENTS.md
│   └── workflows/ci.yml        每次推送时做 lint、测试和构建
├── app/                        全部 Python 代码
│   ├── mkdocs_msal_auth/
│   │   └── hooks.py            访问设置的 MkDocs 构建钩子
│   └── webapp/
│       ├── server.py           Flask 应用和 Entra 登录流程
│       └── wsgi.py             生产 WSGI 入口点
├── docs/                       MkDocs 构建的 Markdown
│   ├── assets/                 登录页样式和错误脚本
│   ├── index.md
│   ├── login.md
│   └── setup.md
├── tests/                      pytest 套件，无网络和无凭据
│   ├── conftest.py             MSAL 和 Graph 边界上的 fixture 和假实现
│   ├── test_auth_policy.py     允许列表和豁免路径规则
│   ├── test_config.py          环境变量和 mkdocs.yml 加载
│   ├── test_hooks.py           MkDocs 构建钩子契约
│   └── test_routes.py          登录、回调、登出和静态服务
├── AGENTS.md                   代理指引，唯一事实来源
├── CLAUDE.md                   指向 AGENTS.md
├── Dockerfile                  构建 site/ 然后用 Gunicorn 提供服务
├── LICENSE                     MIT 许可证
├── mkdocs.yml                  MkDocs 配置和 extra.auth 策略
├── pyproject.toml              依赖和工具配置
└── .python-version             固定的 Python 版本
```

Flask 应用位于 `app/webapp/` 下。MkDocs 构建钩子位于 `app/mkdocs_msal_auth/` 下。文档内容位于 `docs/` 下。测试位于 `tests/` 下。测试从不触网。`.cache/`、`.pytest_cache/`、`.ruff_cache/`、`site/` 和 `.venv/` 下的文件是生成的。git 不跟踪它们。

## 许可证

MIT。完整文本见 [LICENSE](LICENSE)。
