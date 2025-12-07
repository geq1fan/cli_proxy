# Quick Start: Site Availability Check Module

**Date**: 2025-12-07
**Feature**: Site Availability Check Module
**Branch**: 001-site-availability-check

## Purpose

快速上手指南,帮助开发者理解站点可用性检测功能的使用方法和实现要点。

## User Flow

### 1. 用户打开Web UI首页

**步骤**:
1. 启动CLI代理服务: `clp start`
2. 浏览器访问: `http://localhost:3300`
3. 首页自动加载站点可用性检测模块

**预期结果**:
- 页面顶部显示"站点可用性检测"模块
- 自动从配置读取所有站点
- 显示每个站点的基本信息(名称、URL)

---

### 2. 查看站点状态

**步骤**:
1. 模块显示所有配置站点列表
2. 每个站点显示:
   - 站点名称(如"88code")
   - 服务类型标签(Claude/Codex)
   - 状态指示器(🟢 可用 / 🔴 不可用 / ⚪ 未检测)
   - 响应时间(如"235ms")或错误信息

**前端API调用**:
```javascript
// 1. 获取站点列表
const response = await fetch('/api/site-availability/sites');
const data = await response.json();
console.log(data.sites); // 所有配置的站点
```

---

### 3. 手动触发检测

**步骤**:
1. 点击"检测所有站点"按钮
2. 按钮显示"检测中..."并禁用
3. 系统并发检测所有站点(最多5个并发)
4. 逐个更新站点状态
5. 检测完成,按钮恢复

**前端API调用**:
```javascript
// 2. 触发检测
const checkResponse = await fetch('/api/site-availability/check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        sites: data.sites,  // 所有站点
        timeout: 10,        // 超时10秒
        max_concurrent: 5   // 最多5个并发
    })
});

const results = await checkResponse.json();
console.log(results.results); // 所有站点的检测结果

// 3. 更新UI
results.results.forEach(result => {
    updateSiteStatus(result.name, result);
});
```

**后端处理**:
```python
@app.route('/api/site-availability/check', methods=['POST'])
def check_sites():
    data = request.json
    sites = data.get('sites', [])
    timeout = data.get('timeout', 10)
    max_concurrent = data.get('max_concurrent', 5)

    # 使用asyncio并发检测
    results = asyncio.run(check_all_sites_async(sites, timeout, max_concurrent))

    # 保存到历史记录
    for result in results:
        save_to_history(result)

    return jsonify({'results': results})
```

---

### 4. 查看站点详情和历史

**步骤**:
1. 点击某个站点卡片
2. 展开显示该站点的详细信息
3. 显示最近10次检测记录

**前端API调用**:
```javascript
// 4. 获取历史记录
const historyResponse = await fetch('/api/site-availability/history?service=claude&name=88code');
const history = await historyResponse.json();
console.log(history.claude['88code']); // 该站点最近10次记录

// 5. 渲染历史记录
renderHistory(history.claude['88code']);
```

---

## Component Overview

### Backend Components

#### 1. API Endpoints (`src/ui/ui_server.py`)

```python
# 新增3个端点:
@app.route('/api/site-availability/sites', methods=['GET'])
def get_sites():
    """读取所有站点配置"""
    pass

@app.route('/api/site-availability/check', methods=['POST'])
def check_sites():
    """异步检测站点可用性"""
    pass

@app.route('/api/site-availability/history', methods=['GET'])
def get_history():
    """获取历史记录"""
    pass
```

#### 2. Site Checker Module (`src/utils/site_checker.py`)

```python
import asyncio
import httpx
from typing import List, Dict

async def check_site_async(site: Dict, timeout: int = 10) -> Dict:
    """异步检测单个站点"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            start = time.time()
            response = await client.get(
                site['base_url'],
                headers=build_auth_headers(site)
            )
            elapsed_ms = (time.time() - start) * 1000

            return {
                'service': site['service'],
                'name': site['name'],
                'available': response.status_code == 200,
                'status_code': response.status_code,
                'response_time_ms': elapsed_ms,
                'error': None,
                'error_type': None,
                'checked_at': datetime.utcnow().isoformat() + 'Z'
            }
    except httpx.TimeoutException:
        return build_error_result(site, "请求超时", "timeout")
    except httpx.ConnectError:
        return build_error_result(site, "连接失败", "network_error")
    except Exception as e:
        return build_error_result(site, str(e), "unknown")

async def check_all_sites_async(sites: List[Dict], timeout: int, max_concurrent: int) -> List[Dict]:
    """并发检测多个站点"""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def check_with_limit(site):
        async with semaphore:
            return await check_site_async(site, timeout)

    tasks = [check_with_limit(site) for site in sites]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r if not isinstance(r, Exception) else build_error_result(...) for r in results]
```

---

### Frontend Components

#### 1. Main HTML (`src/ui/static/index.html`)

```html
<!-- 在服务状态卡片上方添加 -->
<div id="site-availability-module">
    <h2>站点可用性检测</h2>
    <button id="check-all-btn">检测所有站点</button>
    <div id="sites-list">
        <!-- 动态生成站点卡片 -->
    </div>
</div>
```

#### 2. Frontend Logic (`src/ui/static/site-availability.js`)

```javascript
const SiteAvailabilityChecker = {
    state: {
        sites: [],
        checking: false,
        lastCheck: null
    },

    async init() {
        await this.loadSites();
        this.attachEventListeners();
        this.render();
    },

    async loadSites() {
        const response = await fetch('/api/site-availability/sites');
        const data = await response.json();
        this.state.sites = data.sites;
    },

    async checkAllSites() {
        this.state.checking = true;
        this.render();

        const response = await fetch('/api/site-availability/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sites: this.state.sites,
                timeout: 10,
                max_concurrent: 5
            })
        });

        const data = await response.json();
        this.state.sites = data.results;
        this.state.checking = false;
        this.state.lastCheck = new Date();
        this.render();
    },

    render() {
        const container = document.getElementById('sites-list');
        container.innerHTML = this.state.sites.map(site => this.renderSiteCard(site)).join('');
    },

    renderSiteCard(site) {
        const statusIcon = site.available ? '🟢' : (site.available === null ? '⚪' : '🔴');
        const statusText = site.available
            ? `${site.response_time_ms.toFixed(0)}ms`
            : (site.error || '未检测');

        return `
            <div class="site-card">
                <div class="site-header">
                    <span class="site-name">${site.name}</span>
                    <span class="service-badge">${site.service}</span>
                </div>
                <div class="site-status">
                    <span class="status-icon">${statusIcon}</span>
                    <span class="status-text">${statusText}</span>
                </div>
                <div class="site-url">${site.base_url}</div>
            </div>
        `;
    }
};

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    SiteAvailabilityChecker.init();
});
```

---

## Key Implementation Points

### 1. Async/Await in Flask

Flask不原生支持async,使用`asyncio.run()`桥接:

```python
import asyncio

@app.route('/api/site-availability/check', methods=['POST'])
def check_sites():
    # 同步Flask路由中运行异步代码
    results = asyncio.run(check_all_sites_async(...))
    return jsonify({'results': results})
```

### 2. Concurrent Control

使用`asyncio.Semaphore`限制并发:

```python
semaphore = asyncio.Semaphore(5)  # 最多5个并发

async def check_with_limit(site):
    async with semaphore:  # 获取信号量
        return await check_site_async(site)
```

### 3. Error Handling

三级错误分类:

```python
try:
    response = await client.get(url)
    # 成功
except httpx.TimeoutException:
    # 超时
    error_type = "timeout"
except httpx.ConnectError:
    # 连接错误
    error_type = "network_error"
except httpx.HTTPStatusError as e:
    # HTTP错误
    error_type = "http_error"
    status_code = e.response.status_code
```

### 4. History Management

FIFO队列,最多10条:

```python
def add_to_history(result):
    history = load_history()
    service = result['service']
    name = result['name']

    # 初始化
    if service not in history:
        history[service] = {}
    if name not in history[service]:
        history[service][name] = []

    # 添加到队首
    history[service][name].insert(0, result)

    # 保留最多10条
    history[service][name] = history[service][name][:10]

    save_history(history)
```

---

## Testing Guide

### Manual Testing

1. **启动服务**:
   ```bash
   clp start
   ```

2. **访问UI**:
   ```
   http://localhost:3300
   ```

3. **测试检测功能**:
   - 点击"检测所有站点"
   - 观察状态指示器变化
   - 检查响应时间是否显示

4. **测试历史记录**:
   - 多次检测同一站点
   - 点击站点卡片查看历史
   - 验证最多显示10条

### API Testing

使用curl测试API:

```bash
# 1. 获取站点列表
curl http://localhost:3300/api/site-availability/sites

# 2. 检测站点
curl -X POST http://localhost:3300/api/site-availability/check \
  -H "Content-Type: application/json" \
  -d '{
    "sites": [
      {"service": "claude", "name": "88code", "base_url": "https://www.88code.org/api"}
    ],
    "timeout": 10,
    "max_concurrent": 5
  }'

# 3. 获取历史记录
curl http://localhost:3300/api/site-availability/history?service=claude&name=88code
```

---

## Summary

**核心流程**:
1. 页面加载 → 读取站点配置
2. 用户点击 → 触发异步检测
3. 后端并发 → 检测所有站点
4. 保存结果 → 更新历史记录
5. 返回前端 → 更新UI显示

**关键技术**:
- asyncio + httpx 异步检测
- asyncio.Semaphore 并发控制
- Flask + asyncio.run() 桥接
- JSON文件持久化
- 原生JavaScript状态管理

**文件清单**:
- `src/ui/ui_server.py`: 添加3个API端点
- `src/utils/site_checker.py`: 新增检测模块
- `src/ui/static/index.html`: 添加UI模块
- `src/ui/static/site-availability.js`: 新增前端逻辑
- `src/ui/static/style.css`: 添加样式
- `~/.clp/data/site_availability.json`: 历史记录存储
