# Research: Site Availability Check Module

**Date**: 2025-12-07
**Feature**: Site Availability Check Module
**Branch**: 001-site-availability-check

## Purpose

本文档解决实现计划中的技术未明确项,并研究关键技术决策的最佳实践。

## Research Items

### 1. Testing Framework Selection

**Question**: 项目当前使用什么测试框架?

**Research Process**:
- 检查项目根目录是否有测试目录
- 检查 pyproject.toml 中的测试依赖
- 检查现有代码中的测试导入

**Findings**:
```bash
# 检查结果:
- 项目根目录无 tests/ 目录
- pyproject.toml 无测试框架依赖
- 代码中无测试文件
```

**Decision**: **暂不添加测试框架**

**Rationale**:
- 当前项目无测试基础设施
- 本特性为MVP,优先实现功能
- 测试框架引入属于项目级决策,超出单特性范围
- 可在后续迭代添加(pytest是Python标准选择)

**Alternative Considered**:
- pytest + pytest-asyncio: 标准Python测试框架
- unittest: Python内置框架
- **Rejected because**: 需要项目级决策和基础设施搭建

**Action**: 在 Technical Context 中标记为 "无(项目当前无测试框架)"

---

### 2. Async HTTP Request Best Practices

**Question**: Flask环境下,如何高效实现异步站点检测?

**Research Process**:
- 分析现有项目中的HTTP请求实现
- 评估可用的异步HTTP库
- 考虑Flask WSGI的异步限制

**Findings**:

项目已有依赖:
- `httpx 0.27+`: 现代异步HTTP客户端
- `aiohttp 3.8+`: 另一个异步HTTP库
- `requests 2.25+`: 同步HTTP库

Flask WSGI限制:
- Flask在WSGI模式下不原生支持async/await
- 但可以在路由处理器中使用`asyncio.run()`启动事件循环
- 或使用线程池处理异步任务

**Decision**: **使用 httpx + asyncio.run() 模式**

**Rationale**:
1. httpx已经是项目依赖,无需引入新库
2. httpx支持同步和异步API,灵活性高
3. 在Flask路由中使用`asyncio.run()`可以运行异步代码
4. 简单且符合项目现有技术栈

**Implementation Pattern**:
```python
import asyncio
import httpx

async def check_site_async(url: str, timeout: int = 10):
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(url)
            return {"available": True, "status_code": response.status_code, ...}
        except Exception as e:
            return {"available": False, "error": str(e)}

@app.route('/api/site-availability/check', methods=['POST'])
def check_sites():
    sites = request.json.get('sites', [])
    # 使用asyncio.run在同步上下文中运行异步代码
    results = asyncio.run(check_all_sites(sites))
    return jsonify(results)
```

**Alternative Considered**:
- Threading + requests: 使用线程池并发
  - Rejected: 线程开销大,httpx性能更好
- aiohttp: 另一个异步库
  - Rejected: httpx API更直观,已是项目依赖
- Celery异步任务队列: 重量级解决方案
  - Rejected: 对于简单检测过度工程化

---

### 3. Concurrent Request Handling Strategy

**Question**: 如何控制并发检测数量,避免资源耗尽?

**Research Process**:
- 研究Python asyncio信号量机制
- 评估批处理策略
- 考虑用户体验影响

**Decision**: **使用 asyncio.Semaphore 限制并发数**

**Rationale**:
- asyncio.Semaphore是标准并发控制机制
- 简单高效,无需引入外部库
- 可灵活配置并发数(建议5-10)

**Implementation Pattern**:
```python
async def check_all_sites(sites: list, max_concurrent: int = 5):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def check_with_limit(site):
        async with semaphore:
            return await check_site_async(site['url'])

    tasks = [check_with_limit(site) for site in sites]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

**Alternative Considered**:
- 顺序检测: 一个接一个
  - Rejected: 20个站点需要200秒(10s*20)
- 无限制并发: 全部同时检测
  - Rejected: 可能耗尽系统资源
- 批处理: 分批5个5个检测
  - Rejected: Semaphore更优雅,效果相同

---

### 4. Frontend State Management

**Question**: 前端如何管理检测状态和结果?

**Research Process**:
- 检查现有UI代码的状态管理模式
- 评估是否需要引入框架
- 考虑实时更新需求

**Findings**:

现有前端技术栈:
- 原生JavaScript (无框架)
- 使用简单的DOM操作
- 有`realtime-manager.js`处理实时更新

**Decision**: **原生JavaScript + 简单状态对象**

**Rationale**:
- 保持与现有代码风格一致
- 状态复杂度低,无需React/Vue等框架
- 使用简单的JavaScript对象存储状态

**Implementation Pattern**:
```javascript
// site-availability.js
const SiteAvailabilityChecker = {
  state: {
    sites: [],
    checking: false,
    lastCheck: null
  },

  async checkSites() {
    this.state.checking = true;
    this.render();

    const response = await fetch('/api/site-availability/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sites: this.state.sites })
    });

    const results = await response.json();
    this.state.sites = results;
    this.state.checking = false;
    this.state.lastCheck = new Date();
    this.render();
  },

  render() {
    // 更新DOM
  }
};
```

**Alternative Considered**:
- React/Vue.js: 现代前端框架
  - Rejected: 项目无构建工具,引入复杂度过高
- Web Components: 原生组件化
  - Rejected: 浏览器兼容性问题,过度工程化
- jQuery: 简化DOM操作
  - Rejected: 2025年不建议新引入jQuery

---

### 5. Data Persistence Strategy

**Question**: 历史记录如何存储和读取?

**Research Process**:
- 检查现有项目的数据存储方式
- 评估JSON文件 vs SQLite

**Findings**:

现有存储方式:
- `~/.clp/data/proxy_requests.jsonl`: JSONL格式
- `~/.clp/data/history_usage.json`: JSON格式
- `~/.clp/data/lb_config.json`: JSON格式

**Decision**: **JSON文件存储**

**Rationale**:
- 与现有数据存储方式一致
- 数据量小(每站点10条记录)
- 读写简单,无需SQLite复杂性
- 便于调试和手动检查

**Data Structure**:
```json
{
  "claude": {
    "88code": [
      {
        "timestamp": "2025-12-07T10:30:00",
        "available": true,
        "response_time_ms": 235,
        "status_code": 200
      }
    ],
    "anyrouter": [
      {
        "timestamp": "2025-12-07T10:30:05",
        "available": false,
        "error": "Connection timeout"
      }
    ]
  },
  "codex": {
    // ...
  }
}
```

**File Path**: `~/.clp/data/site_availability.json`

**Alternative Considered**:
- SQLite: 关系型数据库
  - Rejected: 数据量小,JSON足够
- JSONL (追加式): 类似日志格式
  - Rejected: 需要定期清理,JSON更简单
- 内存缓存 + 定期落盘: 性能优化
  - Rejected: MVP不需要,过度优化

---

### 6. Error Classification Strategy

**Question**: 如何区分不同类型的检测失败?

**Research Process**:
- 研究httpx异常类型
- 分析用户关心的错误类别

**Decision**: **三级错误分类**

**Categories**:

1. **Timeout**: 超时错误
   - `httpx.TimeoutException`
   - 显示: "请求超时"

2. **HTTP Error**: HTTP状态码错误
   - 4xx客户端错误: "认证失败" / "请求错误"
   - 5xx服务器错误: "服务器错误"
   - 显示具体状态码

3. **Network Error**: 网络连接错误
   - `httpx.ConnectError`: "连接失败"
   - `httpx.NetworkError`: "网络错误"
   - DNS错误: "域名解析失败"

**Implementation Pattern**:
```python
async def check_site_async(url: str, timeout: int = 10):
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            return {
                "available": response.status_code == 200,
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "error": None if response.status_code == 200 else f"HTTP {response.status_code}"
            }
    except httpx.TimeoutException:
        return {"available": False, "error": "请求超时"}
    except httpx.ConnectError:
        return {"available": False, "error": "连接失败"}
    except httpx.NetworkError as e:
        return {"available": False, "error": f"网络错误: {str(e)}"}
    except Exception as e:
        return {"available": False, "error": f"未知错误: {str(e)}"}
```

**Rationale**:
- 用户友好的错误信息
- 便于调试和问题定位
- 涵盖常见失败场景

---

## Summary

### Resolved Clarifications

| Item | Original | Resolution |
|------|----------|------------|
| Testing Framework | NEEDS CLARIFICATION | 无(项目当前无测试框架) |

### Key Technical Decisions

1. **异步检测**: httpx + asyncio.run() 模式
2. **并发控制**: asyncio.Semaphore限制5-10并发
3. **前端状态**: 原生JavaScript + 简单状态对象
4. **数据存储**: JSON文件(`~/.clp/data/site_availability.json`)
5. **错误分类**: Timeout/HTTP Error/Network Error三级分类

### Next Steps

所有技术未明确项已解决,可以进入Phase 1设计阶段:
- 生成data-model.md
- 生成API contracts
- 生成quickstart.md
