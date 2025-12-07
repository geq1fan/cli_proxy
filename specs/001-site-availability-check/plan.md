# Implementation Plan: Site Availability Check Module

**Branch**: `001-site-availability-check` | **Date**: 2025-12-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-site-availability-check/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

在CLI Proxy Web UI首页新增站点可用性检测模块,通过发送最小API请求(模型列表查询)验证所有已配置的Claude和Codex站点的实时可用性。首次加载自动检测,后续支持手动刷新。使用localStorage保存历史记录(10-20条),详细显示HTTP状态码和错误信息,限制并发数为5个避免资源耗尽。

## Technical Context

**Language/Version**: Python >=3.8 (现有项目), JavaScript ES6+ (前端)
**Primary Dependencies**:
  - Backend: Flask 2.0+, httpx 0.27+ (用于异步HTTP请求), aiohttp 3.8+
  - Frontend: Vue 3 (CDN), Element Plus 2.8 (UI组件库)
**Storage**: JSON文件 ~/.clp/data/site_availability.json (检测历史), 浏览器sessionStorage (当前检测状态)
**Testing**: 无(项目当前无测试框架,建议后续引入pytest)
**Target Platform**: Web应用 (桌面浏览器), 后端支持Windows/Linux/macOS
**Project Type**: Web (Flask后端 + Vue 3前端)
**Performance Goals**:
  - 首次加载显示模块 <1秒 (SC-001)
  - 单站点检测完成 <10秒 (SC-002)
  - 手动刷新响应 <500ms (SC-004)
**Constraints**:
  - 并发限制5个请求 (避免浏览器连接限制)
  - localStorage存储上限 (通常5-10MB,需评估20站点*20条历史记录的容量)
**Scale/Scope**: 支持20+站点同时检测,保留每站点10-20条历史

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: ✅ PASS - 项目宪法尚未建立,使用常规Web开发最佳实践

由于`.specify/memory/constitution.md`仍为模板状态,本功能遵循以下通用原则:

1. **代码组织**: 前端代码集中在`src/ui/static/`,后端API路由在`src/ui/ui_server.py`
2. **最小侵入**: 新增功能不修改现有代理逻辑,仅添加新的API端点和前端组件
3. **数据隔离**: 检测历史存储在浏览器端,不污染后端日志文件
4. **向后兼容**: 功能为增强型添加,不影响现有服务状态监控

**无需Complexity Tracking表** - 功能符合现有架构模式

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── ui/
│   ├── ui_server.py              # Flask后端 - 新增/api/sites/check端点
│   └── static/
│       ├── index.html             # 主页面 - 新增站点检测模块
│       ├── app.js                 # Vue应用 - 新增检测逻辑和状态管理
│       ├── availability-check.js  # 新建 - 站点检测服务模块
│       └── style.css              # 样式更新 - 检测模块样式
├── claude/
│   └── configs.py                 # 读取claude站点配置(现有)
└── codex/
    └── configs.py                 # 读取codex站点配置(现有)

tests/                             # NEEDS CLARIFICATION - 测试结构待确定
├── backend/
│   └── test_availability_api.py   # 新建 - API端点测试
└── frontend/
    └── test_availability_ui.js    # 新建(可选) - 前端组件测试
```

**Structure Decision**: 采用现有Web应用结构(Option 2变体)。后端使用Flask单体应用模式,前端使用Vue 3 CDN模式(非构建工具)。新功能通过以下方式集成:

1. **后端**: 在`src/ui/ui_server.py`添加新的API路由`/api/sites/check`
2. **前端**: 在`src/ui/static/`下新增`availability-check.js`模块,在`app.js`中导入并集成到主Vue应用
3. **配置读取**: 复用现有的`configs.py`模块读取站点配置

## Complexity Tracking

N/A - 无宪法违规或复杂度告警
