# UI Design: Site Availability Check Module

**Date**: 2025-12-07
**Feature**: Site Availability Check Module
**Branch**: 001-site-availability-check

## Overview

站点可用性检测模块位于Web UI首页顶部,采用卡片式布局,提供清晰的视觉反馈和直观的交互体验。

---

## Page Layout

### 整体布局（分组显示）

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Proxy Dashboard                      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           🔍 站点可用性检测                            │  │
│  │  ┌────────────────────────────────┐  ┌────────────┐  │  │
│  │  │ 最后检测: 2025-12-07 10:30:00  │  │ 🔄 刷新全部 │  │  │
│  │  └────────────────────────────────┘  └────────────┘  │  │
│  │                                                        │  │
│  │  ┌─ Claude 站点 ───────────────────────────────────┐  │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │  │  │
│  │  │  │ 88code      │  │ anyrouter   │  │ site3    │ │  │  │
│  │  │  │ 🟢 235ms    │  │ 🔴 超时      │  │ ⚪ 未检测  │ │  │  │
│  │  │  │ www.88co... │  │ anyroute... │  │ site3... │ │  │  │
│  │  │  │ [查看详情]  │  │ [查看详情]  │  │ [查看详情]│ │  │  │
│  │  │  └─────────────┘  └─────────────┘  └──────────┘ │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │                                                        │  │
│  │  ┌─ Codex 站点 ────────────────────────────────────┐  │  │
│  │  │  ┌─────────────┐  ┌─────────────┐               │  │  │
│  │  │  │ codex-site1 │  │ codex-site2 │               │  │  │
│  │  │  │ 🟢 180ms    │  │ 🟢 210ms    │               │  │  │
│  │  │  │ api.code... │  │ openai.c... │               │  │  │
│  │  │  │ [查看详情]  │  │ [查看详情]  │               │  │  │
│  │  │  └─────────────┘  └─────────────┘               │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  服务运行状态                                          │  │
│  │  ...现有内容...                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. 模块容器 (Module Container) - 分组显示

```html
<div class="site-availability-module">
  <div class="module-header">
    <h2>🔍 站点可用性检测</h2>
    <div class="module-controls">
      <span class="last-check">最后检测: 2025-12-07 10:30:00</span>
      <button class="refresh-btn" id="refresh-all">
        <span class="icon">🔄</span> 刷新全部
      </button>
    </div>
  </div>

  <!-- Claude 站点分组 -->
  <div class="service-group claude-group">
    <div class="service-group-header">
      <h3 class="service-title">
        <span class="service-icon">🤖</span>
        Claude 站点
        <span class="site-count">(3)</span>
      </h3>
      <button class="group-refresh-btn" data-service="claude">
        <span class="icon">🔄</span> 刷新Claude
      </button>
    </div>
    <div class="sites-grid" id="claude-sites-grid">
      <!-- Claude site cards here -->
    </div>
  </div>

  <!-- Codex 站点分组 -->
  <div class="service-group codex-group">
    <div class="service-group-header">
      <h3 class="service-title">
        <span class="service-icon">💻</span>
        Codex 站点
        <span class="site-count">(2)</span>
      </h3>
      <button class="group-refresh-btn" data-service="codex">
        <span class="icon">🔄</span> 刷新Codex
      </button>
    </div>
    <div class="sites-grid" id="codex-sites-grid">
      <!-- Codex site cards here -->
    </div>
  </div>
</div>
```

**样式**:
```css
.site-availability-module {
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.module-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f0f0f0;
}

.module-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.module-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.last-check {
  font-size: 14px;
  color: #666;
}

.refresh-btn {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background: #45a049;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(76,175,80,0.3);
}

.refresh-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
}

.refresh-btn.checking {
  background: #FF9800;
}

.refresh-btn.checking .icon {
  animation: spin 1s linear infinite;
}

/* 服务分组样式 */
.service-group {
  margin-bottom: 24px;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
}

.service-group:last-child {
  margin-bottom: 0;
}

.claude-group {
  border-left: 4px solid #1976D2;
}

.codex-group {
  border-left: 4px solid #7B1FA2;
}

.service-group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.service-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.service-icon {
  font-size: 20px;
}

.site-count {
  font-size: 13px;
  font-weight: 400;
  color: #666;
  margin-left: 4px;
}

.group-refresh-btn {
  background: transparent;
  border: 1px solid #4CAF50;
  color: #4CAF50;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.group-refresh-btn:hover {
  background: #4CAF50;
  color: white;
}

.group-refresh-btn:disabled {
  border-color: #ccc;
  color: #ccc;
  cursor: not-allowed;
}

.group-refresh-btn.checking {
  border-color: #FF9800;
  color: #FF9800;
}

.group-refresh-btn.checking .icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

---

### 2. 站点卡片 (Site Card) - 简化版

```html
<div class="site-card" data-service="claude" data-name="88code">
  <div class="site-card-header">
    <h3 class="site-name">88code</h3>
    <div class="site-status">
      <span class="status-icon available">🟢</span>
      <span class="status-text">235ms</span>
    </div>
  </div>

  <div class="site-card-body">
    <div class="site-url" title="https://www.88code.org/api">
      https://www.88code.org/api
    </div>
    <div class="site-meta">
      <span class="active-badge">● 激活中</span>
    </div>
  </div>

  <div class="site-card-footer">
    <button class="detail-btn" onclick="toggleDetails('claude', '88code')">
      查看详情 ▼
    </button>
  </div>

  <!-- 展开的详情区域(默认隐藏) -->
  <div class="site-details" id="details-claude-88code" style="display: none;">
    <div class="details-header">
      <h4>历史记录</h4>
      <span class="record-count">最近10次检测</span>
    </div>
    <div class="history-list">
      <div class="history-item">
        <span class="time">10:30:00</span>
        <span class="status available">🟢 可用</span>
        <span class="response">235ms</span>
      </div>
      <div class="history-item">
        <span class="time">10:00:00</span>
        <span class="status available">🟢 可用</span>
        <span class="response">240ms</span>
      </div>
      <div class="history-item">
        <span class="time">09:30:00</span>
        <span class="status unavailable">🔴 不可用</span>
        <span class="error">连接超时</span>
      </div>
    </div>
  </div>
</div>
```

**说明**: 由于已通过分组区分服务类型,卡片内不再显示服务标签,界面更简洁。

**样式**:
```css
.sites-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.site-card {
  background: #fafafa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s;
  cursor: pointer;
}

.site-card:hover {
  border-color: #4CAF50;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.site-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.site-name {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.site-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.status-icon {
  font-size: 24px;
  line-height: 1;
}

.status-text {
  font-size: 14px;
  font-weight: 600;
  color: #4CAF50;
}

.status-text.error {
  color: #f44336;
  font-size: 12px;
  max-width: 100px;
  text-align: right;
  word-wrap: break-word;
}

.status-text.unchecked {
  color: #9e9e9e;
}

.site-card-body {
  margin-bottom: 12px;
}

.site-url {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 8px;
}

.site-meta {
  display: flex;
  gap: 8px;
}

.active-badge {
  font-size: 11px;
  color: #4CAF50;
  font-weight: 500;
}

.site-card-footer {
  border-top: 1px solid #e0e0e0;
  padding-top: 12px;
  margin-top: 12px;
}

.detail-btn {
  background: transparent;
  border: none;
  color: #1976D2;
  font-size: 13px;
  cursor: pointer;
  padding: 4px 0;
  width: 100%;
  text-align: left;
  font-weight: 500;
  transition: color 0.2s;
}

.detail-btn:hover {
  color: #1565C0;
  text-decoration: underline;
}
```

---

### 3. 站点详情展开区域

```css
.site-details {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 2px solid #e0e0e0;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 500px;
  }
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.details-header h4 {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.record-count {
  font-size: 12px;
  color: #666;
}

.history-list {
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border-radius: 4px;
  margin-bottom: 6px;
  font-size: 13px;
}

.history-item:last-child {
  margin-bottom: 0;
}

.history-item .time {
  color: #666;
  font-family: monospace;
}

.history-item .status {
  font-weight: 500;
}

.history-item .status.available {
  color: #4CAF50;
}

.history-item .status.unavailable {
  color: #f44336;
}

.history-item .response {
  color: #4CAF50;
  font-weight: 600;
}

.history-item .error {
  color: #f44336;
  font-size: 12px;
}
```

---

## State Visualization

### 状态指示器设计

#### 可用状态 (Available)
```
┌─────────────┐
│ 88code      │
│ Claude      │
│ 🟢 235ms    │  ← 绿色圆点 + 响应时间
│ ────────    │
│ www.88co... │
│ [查看详情]  │
└─────────────┘
```

#### 不可用状态 (Unavailable)
```
┌─────────────┐
│ anyrouter   │
│ Claude      │
│ 🔴 超时      │  ← 红色圆点 + 错误信息
│ ────────    │
│ anyroute... │
│ [查看详情]  │
└─────────────┘
```

#### 未检测状态 (Unchecked)
```
┌─────────────┐
│ site3       │
│ Codex       │
│ ⚪ 未检测    │  ← 灰色圆点 + "未检测"
│ ────────    │
│ api.sit...  │
│ [查看详情]  │
└─────────────┘
```

#### 检测中状态 (Checking)
```
┌─────────────┐
│ 88code      │
│ Claude      │
│ ⏳ 检测中... │  ← 沙漏图标 + 动画
│ ────────    │
│ www.88co... │
│ [查看详情]  │
└─────────────┘
```

---

## Interaction Flow

### 1. 页面加载流程

```
用户访问首页
    ↓
自动调用 GET /api/site-availability/sites
    ↓
渲染站点卡片(未检测状态)
    ↓
展示"刷新"按钮
```

### 2. 手动检测流程

```
用户点击"刷新"按钮
    ↓
按钮文字变为"检测中..." + 禁用
    ↓
所有站点卡片状态变为"⏳ 检测中..."
    ↓
调用 POST /api/site-availability/check
    ↓
等待后端响应(最多10秒)
    ↓
逐个更新站点状态
    ↓
按钮恢复 + 更新"最后检测"时间
```

### 3. 查看详情流程

```
用户点击"查看详情"
    ↓
卡片展开,显示历史记录区域
    ↓
调用 GET /api/site-availability/history
    ↓
渲染最近10条记录
    ↓
按钮文字变为"收起 ▲"
```

---

## Responsive Design

### 桌面端 (≥1024px)
```css
.sites-grid {
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
```

### 平板端 (768px - 1023px)
```css
@media (max-width: 1023px) {
  .sites-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}
```

### 移动端 (<768px)
```css
@media (max-width: 767px) {
  .sites-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .module-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .module-controls {
    width: 100%;
    justify-content: space-between;
  }
}
```

---

## Animation & Transitions

### 1. 卡片悬停效果
```css
.site-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

### 2. 刷新按钮旋转动画
```css
.refresh-btn.checking .icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

### 3. 详情区域展开动画
```css
@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 500px;
  }
}
```

### 4. 状态更新脉冲效果
```css
.status-icon.updating {
  animation: pulse 0.5s ease-in-out;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.8; }
}
```

---

## Color Palette

```css
:root {
  /* Primary Colors */
  --color-available: #4CAF50;     /* 绿色 - 可用 */
  --color-unavailable: #f44336;   /* 红色 - 不可用 */
  --color-unchecked: #9e9e9e;     /* 灰色 - 未检测 */
  --color-checking: #FF9800;      /* 橙色 - 检测中 */

  /* Service Badge Colors */
  --color-claude-bg: #E3F2FD;
  --color-claude-text: #1976D2;
  --color-codex-bg: #F3E5F5;
  --color-codex-text: #7B1FA2;

  /* Background & Border */
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #fafafa;
  --color-border: #e0e0e0;
  --color-border-hover: #4CAF50;

  /* Text Colors */
  --color-text-primary: #333333;
  --color-text-secondary: #666666;
  --color-text-tertiary: #999999;

  /* Button Colors */
  --color-btn-primary: #4CAF50;
  --color-btn-primary-hover: #45a049;
  --color-btn-link: #1976D2;
  --color-btn-link-hover: #1565C0;
}
```

---

## Accessibility

### 1. 键盘导航
```javascript
// 支持Tab键导航
document.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && e.target.classList.contains('site-card')) {
    toggleDetails(e.target.dataset.name);
  }
});
```

### 2. ARIA标签
```html
<button
  class="refresh-btn"
  id="refresh-all"
  aria-label="刷新所有站点状态"
  aria-busy="false">
  🔄 刷新
</button>

<div
  class="site-card"
  role="article"
  aria-labelledby="site-name-88code"
  tabindex="0">
  <h3 id="site-name-88code">88code</h3>
  ...
</div>
```

### 3. 对比度
- 文字对比度 ≥ 4.5:1 (WCAG AA标准)
- 状态指示器使用图标+文字双重表达
- 错误信息使用红色+文字说明

---

## Mock Data Example

```javascript
// 初始状态(未检测)
const mockSites = [
  {
    service: 'claude',
    name: '88code',
    base_url: 'https://www.88code.org/api',
    active: true,
    available: null,  // 未检测
    status_code: null,
    response_time_ms: null,
    error: null
  },
  {
    service: 'claude',
    name: 'anyrouter',
    base_url: 'https://anyrouter.hachimitsu.netlib.re',
    active: false,
    available: null,
    status_code: null,
    response_time_ms: null,
    error: null
  }
];

// 检测后状态
const mockCheckedSites = [
  {
    service: 'claude',
    name: '88code',
    base_url: 'https://www.88code.org/api',
    active: true,
    available: true,
    status_code: 200,
    response_time_ms: 235.6,
    error: null,
    error_type: null,
    checked_at: '2025-12-07T10:30:00.000Z'
  },
  {
    service: 'claude',
    name: 'anyrouter',
    base_url: 'https://anyrouter.hachimitsu.netlib.re',
    active: false,
    available: false,
    status_code: null,
    response_time_ms: null,
    error: '请求超时',
    error_type: 'timeout',
    checked_at: '2025-12-07T10:30:05.000Z'
  }
];
```

---

## Summary

**设计原则**:
1. **清晰** - 状态一目了然(颜色+图标+文字)
2. **简洁** - 卡片式布局,信息密度适中
3. **响应** - 自适应不同屏幕尺寸
4. **友好** - 平滑动画,良好的交互反馈
5. **高效** - 网格布局,最大化空间利用
6. **分组** - Claude和Codex站点明确分离

**关键特性**:
- 🎨 三种状态可视化(可用/不可用/未检测)
- 🔄 一键刷新所有站点 或 分组刷新
- 📊 历史记录展开查看
- 📱 响应式设计
- ♿ 无障碍支持
- 🗂️ 服务分组显示(Claude/Codex)

**分组设计优势**:
- ✅ **视觉区分**: 左侧彩条标识(蓝色=Claude, 紫色=Codex)
- ✅ **独立刷新**: 可单独刷新某个服务的所有站点
- ✅ **统计清晰**: 每组显示站点数量
- ✅ **界面简洁**: 卡片内无需服务标签,减少视觉噪音
- ✅ **扩展性好**: 未来添加新服务时易于扩展

**分组交互**:
1. **全局刷新**: 点击顶部"刷新全部"→ 检测所有服务的所有站点
2. **分组刷新**: 点击分组内"刷新Claude/Codex"→ 仅检测该服务站点
3. **状态隔离**: 一个服务检测中不影响另一个服务的操作

**技术实现**:
- 原生CSS Grid布局
- JavaScript分组状态管理
- CSS动画增强体验
- ARIA无障碍标签
- 服务分组数据结构

---

## 分组逻辑实现示例

### JavaScript 分组管理

```javascript
const SiteAvailabilityChecker = {
  state: {
    sites: {
      claude: [],
      codex: []
    },
    checking: {
      all: false,
      claude: false,
      codex: false
    },
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

    // 按服务分组
    this.state.sites.claude = data.sites.filter(s => s.service === 'claude');
    this.state.sites.codex = data.sites.filter(s => s.service === 'codex');
  },

  attachEventListeners() {
    // 全局刷新
    document.getElementById('refresh-all').addEventListener('click', () => {
      this.checkAllSites();
    });

    // 分组刷新
    document.querySelectorAll('.group-refresh-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const service = e.currentTarget.dataset.service;
        this.checkServiceSites(service);
      });
    });
  },

  async checkAllSites() {
    this.state.checking.all = true;
    this.render();

    const allSites = [...this.state.sites.claude, ...this.state.sites.codex];
    await this.performCheck(allSites);

    this.state.checking.all = false;
    this.state.lastCheck = new Date();
    this.render();
  },

  async checkServiceSites(service) {
    this.state.checking[service] = true;
    this.render();

    const sites = this.state.sites[service];
    await this.performCheck(sites);

    this.state.checking[service] = false;
    this.render();
  },

  async performCheck(sites) {
    const response = await fetch('/api/site-availability/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sites: sites,
        timeout: 10,
        max_concurrent: 5
      })
    });

    const data = await response.json();

    // 更新状态
    data.results.forEach(result => {
      const service = result.service;
      const siteIndex = this.state.sites[service].findIndex(
        s => s.name === result.name
      );
      if (siteIndex !== -1) {
        this.state.sites[service][siteIndex] = {
          ...this.state.sites[service][siteIndex],
          ...result
        };
      }
    });
  },

  render() {
    this.renderClaudeSites();
    this.renderCodexSites();
    this.updateButtons();
    this.updateLastCheckTime();
  },

  renderClaudeSites() {
    const container = document.getElementById('claude-sites-grid');
    const sites = this.state.sites.claude;

    // 更新站点数量
    document.querySelector('.claude-group .site-count').textContent =
      `(${sites.length})`;

    container.innerHTML = sites.map(site =>
      this.renderSiteCard(site)
    ).join('');
  },

  renderCodexSites() {
    const container = document.getElementById('codex-sites-grid');
    const sites = this.state.sites.codex;

    // 更新站点数量
    document.querySelector('.codex-group .site-count').textContent =
      `(${sites.length})`;

    container.innerHTML = sites.map(site =>
      this.renderSiteCard(site)
    ).join('');
  },

  updateButtons() {
    const refreshAll = document.getElementById('refresh-all');
    const claudeBtn = document.querySelector('[data-service="claude"]');
    const codexBtn = document.querySelector('[data-service="codex"]');

    // 全局按钮
    if (this.state.checking.all) {
      refreshAll.disabled = true;
      refreshAll.classList.add('checking');
      refreshAll.textContent = '检测中...';
    } else {
      refreshAll.disabled = false;
      refreshAll.classList.remove('checking');
      refreshAll.innerHTML = '<span class="icon">🔄</span> 刷新全部';
    }

    // Claude按钮
    if (this.state.checking.claude || this.state.checking.all) {
      claudeBtn.disabled = true;
      claudeBtn.classList.add('checking');
    } else {
      claudeBtn.disabled = false;
      claudeBtn.classList.remove('checking');
    }

    // Codex按钮
    if (this.state.checking.codex || this.state.checking.all) {
      codexBtn.disabled = true;
      codexBtn.classList.add('checking');
    } else {
      codexBtn.disabled = false;
      codexBtn.classList.remove('checking');
    }
  },

  renderSiteCard(site) {
    const statusIcon = site.available ? '🟢' :
                       (site.available === null ? '⚪' : '🔴');
    const statusText = site.available
      ? `${site.response_time_ms?.toFixed(0)}ms`
      : (site.error || '未检测');

    return `
      <div class="site-card" data-service="${site.service}" data-name="${site.name}">
        <div class="site-card-header">
          <h3 class="site-name">${site.name}</h3>
          <div class="site-status">
            <span class="status-icon">${statusIcon}</span>
            <span class="status-text ${site.available === false ? 'error' : ''}
                                     ${site.available === null ? 'unchecked' : ''}">
              ${statusText}
            </span>
          </div>
        </div>
        <div class="site-card-body">
          <div class="site-url" title="${site.base_url}">${site.base_url}</div>
          <div class="site-meta">
            ${site.active ? '<span class="active-badge">● 激活中</span>' : ''}
          </div>
        </div>
        <div class="site-card-footer">
          <button class="detail-btn"
                  onclick="SiteAvailabilityChecker.toggleDetails('${site.service}', '${site.name}')">
            查看详情 ▼
          </button>
        </div>
        <div class="site-details" id="details-${site.service}-${site.name}"
             style="display: none;">
          <!-- 历史记录内容 -->
        </div>
      </div>
    `;
  }
};

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
  SiteAvailabilityChecker.init();
});
```
