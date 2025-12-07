# Data Model: Site Availability Check Module

**Date**: 2025-12-07
**Feature**: Site Availability Check Module
**Branch**: 001-site-availability-check

## Purpose

定义站点可用性检测功能的数据模型,包括实体结构、关系和验证规则。

## Core Entities

### 1. Site (站点)

代表一个需要检测的API站点配置。

**Source**: 从 `~/.clp/claude.json` 和 `~/.clp/codex.json` 读取

**Structure**:
```python
{
    "service": str,        # 服务类型: "claude" | "codex"
    "name": str,           # 站点名称,如 "88code", "anyrouter"
    "base_url": str,       # 基础URL,如 "https://www.88code.org/api"
    "auth_token": str,     # 认证令牌(可选)
    "api_key": str,        # API密钥(可选)
    "active": bool         # 是否激活(从配置读取,非检测状态)
}
```

**Validation Rules**:
- `service`: 必须是 "claude" 或 "codex"
- `name`: 非空字符串,唯一标识
- `base_url`: 有效的HTTP/HTTPS URL
- `auth_token` 和 `api_key`: 至少一个非空(用于认证)
- `active`: 布尔值,表示配置的激活状态(非检测结果)

**Example**:
```json
{
    "service": "claude",
    "name": "88code",
    "base_url": "https://www.88code.org/api",
    "auth_token": "88_7ecdbf8b8fc08186cb5b3528740d4c47762b791e1283c5d2432af8aa13728bf3",
    "api_key": "",
    "active": true
}
```

---

### 2. CheckRequest (检测请求)

代表一次站点可用性检测操作的请求。

**Source**: 前端发起,后端处理

**Structure**:
```python
{
    "sites": List[Site],   # 要检测的站点列表
    "timeout": int,        # 超时时间(秒),默认10
    "max_concurrent": int  # 最大并发数,默认5
}
```

**Validation Rules**:
- `sites`: 非空列表
- `timeout`: 1-30秒之间
- `max_concurrent`: 1-20之间

**Example**:
```json
{
    "sites": [
        {"service": "claude", "name": "88code", "base_url": "https://..."},
        {"service": "claude", "name": "anyrouter", "base_url": "https://..."}
    ],
    "timeout": 10,
    "max_concurrent": 5
}
```

---

### 3. CheckResult (检测结果)

代表一次站点检测的即时结果。

**Source**: 后端检测逻辑生成

**Structure**:
```python
{
    "service": str,           # 服务类型
    "name": str,              # 站点名称
    "available": bool,        # 是否可用
    "status_code": int|None,  # HTTP状态码(成功时)
    "response_time_ms": float|None,  # 响应时间(毫秒)
    "error": str|None,        # 错误信息(失败时)
    "error_type": str|None,   # 错误类型: "timeout"|"http_error"|"network_error"
    "checked_at": str         # 检测时间戳(ISO 8601)
}
```

**State Transitions**:
```
Checking -> Success (available=True, status_code=200)
         -> HTTP Error (available=False, error_type="http_error", status_code=4xx/5xx)
         -> Timeout (available=False, error_type="timeout")
         -> Network Error (available=False, error_type="network_error")
```

**Validation Rules**:
- `available=True` 时: `status_code=200`, `response_time_ms`非空
- `available=False` 时: `error`和`error_type`非空
- `checked_at`: 有效的ISO 8601时间戳

**Example (成功)**:
```json
{
    "service": "claude",
    "name": "88code",
    "available": true,
    "status_code": 200,
    "response_time_ms": 235.6,
    "error": null,
    "error_type": null,
    "checked_at": "2025-12-07T10:30:00.000Z"
}
```

**Example (失败)**:
```json
{
    "service": "claude",
    "name": "anyrouter",
    "available": false,
    "status_code": null,
    "response_time_ms": null,
    "error": "请求超时",
    "error_type": "timeout",
    "checked_at": "2025-12-07T10:30:05.000Z"
}
```

---

### 4. AvailabilityHistory (可用性历史)

代表站点的历史检测记录集合。

**Source**: 持久化到 `~/.clp/data/site_availability.json`

**Structure**:
```python
{
    "service_name": {
        "site_name": [
            CheckResult,  # 最新记录
            CheckResult,
            ...           # 最多保留10条
        ]
    }
}
```

**Constraints**:
- 每个站点最多保留10条历史记录
- 超过10条时,删除最旧的记录(FIFO)
- 记录按时间倒序排列(最新在前)

**Example**:
```json
{
    "claude": {
        "88code": [
            {
                "service": "claude",
                "name": "88code",
                "available": true,
                "status_code": 200,
                "response_time_ms": 235.6,
                "error": null,
                "error_type": null,
                "checked_at": "2025-12-07T10:30:00.000Z"
            },
            {
                "service": "claude",
                "name": "88code",
                "available": true,
                "status_code": 200,
                "response_time_ms": 240.2,
                "error": null,
                "error_type": null,
                "checked_at": "2025-12-07T10:00:00.000Z"
            }
        ],
        "anyrouter": [
            {
                "service": "claude",
                "name": "anyrouter",
                "available": false,
                "status_code": null,
                "response_time_ms": null,
                "error": "请求超时",
                "error_type": "timeout",
                "checked_at": "2025-12-07T10:30:05.000Z"
            }
        ]
    },
    "codex": {
        // ...
    }
}
```

---

## Data Relationships

```
Site
  ↓ (triggers)
CheckRequest
  ↓ (produces)
CheckResult (即时)
  ↓ (persists to)
AvailabilityHistory (持久化)
  ↓ (aggregates)
AvailabilityHistory[site_name] (每站点列表)
```

**Flow**:
1. 前端从配置读取 `Site` 列表
2. 用户触发检测,发送 `CheckRequest`
3. 后端异步检测,生成 `CheckResult`
4. `CheckResult` 保存到 `AvailabilityHistory`
5. 前端展示最新 `CheckResult` 和历史记录

---

## File Storage Schema

### File: `~/.clp/data/site_availability.json`

**Format**: JSON

**Encoding**: UTF-8

**Structure**: 见 `AvailabilityHistory` 定义

**Operations**:

**Read**:
```python
def load_history() -> dict:
    if not file.exists():
        return {"claude": {}, "codex": {}}
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)
```

**Write**:
```python
def save_history(history: dict) -> None:
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
```

**Update (添加新记录)**:
```python
def add_check_result(result: CheckResult) -> None:
    history = load_history()
    service = result['service']
    name = result['name']

    # 初始化服务和站点
    if service not in history:
        history[service] = {}
    if name not in history[service]:
        history[service][name] = []

    # 添加新记录到开头
    history[service][name].insert(0, result)

    # 保留最多10条
    history[service][name] = history[service][name][:10]

    save_history(history)
```

---

## Error Types Enumeration

```python
ERROR_TYPES = {
    "timeout": "请求超时",
    "http_error": "HTTP错误",
    "network_error": "网络错误",
    "unknown": "未知错误"
}

HTTP_STATUS_MESSAGES = {
    200: "正常",
    401: "认证失败",
    403: "访问被拒绝",
    404: "服务未找到",
    429: "请求过于频繁",
    500: "服务器内部错误",
    502: "网关错误",
    503: "服务不可用",
    504: "网关超时"
}
```

---

## Summary

**核心实体**:
1. `Site`: 站点配置(从配置文件读取)
2. `CheckRequest`: 检测请求(前端→后端)
3. `CheckResult`: 检测结果(后端→前端)
4. `AvailabilityHistory`: 历史记录(持久化存储)

**数据流**:
配置文件 → Site → CheckRequest → CheckResult → AvailabilityHistory → 前端展示

**存储**:
- 输入: `~/.clp/claude.json`, `~/.clp/codex.json`
- 输出: `~/.clp/data/site_availability.json`

**关键约束**:
- 历史记录每站点最多10条
- 检测超时10秒
- 并发检测5个站点
