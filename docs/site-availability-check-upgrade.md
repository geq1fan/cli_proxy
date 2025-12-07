# 站点可用性检测功能升级文档

## 版本信息
- **版本**: v2.0
- **更新日期**: 2025-12-07
- **参考实现**: relay-pulse (github.com/prehisle/relay-pulse)

## 目录
1. [功能概述](#功能概述)
2. [核心改进](#核心改进)
3. [配置说明](#配置说明)
4. [API文档](#api文档)
5. [前端UI](#前端ui)
6. [技术实现](#技术实现)
7. [测试指南](#测试指南)
8. [代码Review要点](#代码review要点)
9. [向后兼容性](#向后兼容性)

---

## 功能概述

### 改造目标
将简单的HTTP健康检查升级为relay-pulse风格的真实API调用检测，提供更准确的站点可用性判断。

### 检测方式对比

| 项目 | 旧版本 | 新版本 |
|------|--------|--------|
| **请求方法** | GET /v1/models | POST /v1/chat/completions |
| **Token消耗** | 0 | 20-30 tokens/次 |
| **准确性** | 基础（仅HTTP状态码） | 高（HTTP + 延迟 + 内容） |
| **内容校验** | ❌ | ✅ |
| **错误分类** | 2种（可用/不可用） | 8种（精确分类） |
| **SSE支持** | ❌ | ✅ |
| **独立配置** | ❌ | ✅ 每站点6个参数 |

---

## 核心改进

### 1. 三层状态判定

按照relay-pulse的实现方式，检测分为三个层次：

```
第一层：HTTP状态码判定
├── 2xx → 绿色（正常）
├── 3xx → 绿色（重定向）
├── 401/403 → 红色（认证错误）
├── 400 → 红色（参数错误）
├── 429 → 红色（限流）
├── 5xx → 红色（服务器错误）
└── 其他4xx → 红色（客户端错误）

第二层：延迟判定
└── 响应时间 > slow_latency_ms → 黄色（慢速）

第三层：内容校验（可选）
└── 响应内容不包含 success_contains → 红色（内容不匹配）
```

### 2. 错误分类细化

定义了8种SubStatus错误类型：

```python
class SubStatus:
    NONE = "none"                          # 正常
    SLOW_LATENCY = "slow_latency"          # 慢速（黄色）
    RATE_LIMIT = "rate_limit"              # 429限流（红色）
    AUTH_ERROR = "auth_error"              # 401/403认证错误
    INVALID_REQUEST = "invalid_request"    # 400参数错误
    SERVER_ERROR = "server_error"          # 5xx服务器错误
    CONTENT_MISMATCH = "content_mismatch"  # 内容不匹配
    NETWORK_ERROR = "network_error"        # 网络错误
    CLIENT_ERROR = "client_error"          # 其他4xx错误
```

### 3. SSE流式响应支持

支持解析两种SSE格式：

**Anthropic格式**:
```
event: content_block_delta
data: {"delta":{"text":"Hello"}}
```

**OpenAI格式**:
```
data: {"choices":[{"delta":{"content":"Hello"}}]}
```

---

## 配置说明

### 新增配置字段

每个站点配置新增6个检测相关字段：

```json
{
  "site_name": {
    "base_url": "https://api.example.com",
    "auth_token": "sk-xxx",
    "active": true,

    // ========== 新增检测配置 ==========
    "enable_check": true,              // 是否启用检测
    "check_model": "gpt-3.5-turbo",    // 检测使用的模型
    "check_message": "hi",             // 检测消息内容
    "check_max_tokens": 1,             // 最大token数
    "success_contains": "hi",          // 预期响应内容（可选）
    "slow_latency_ms": 5000            // 慢速阈值（毫秒）
  }
}
```

### 字段详细说明

#### 1. enable_check
- **类型**: Boolean
- **默认值**: `true`
- **说明**: 是否对该站点启用可用性检测
- **用途**:
  - 设为`false`可禁用检测，节省tokens
  - 禁用的站点在UI上显示为蓝色🔵

#### 2. check_model
- **类型**: String
- **默认值**:
  - Claude服务: `"claude-3-haiku-20240307"`
  - Codex服务: `"gpt-3.5-turbo"`
- **说明**: 检测时使用的模型名称
- **建议**: 使用便宜的小模型以降低成本

#### 3. check_message
- **类型**: String
- **默认值**: `"hi"`
- **说明**: 发送给API的测试消息
- **建议**: 使用简短消息以减少token消耗

#### 4. check_max_tokens
- **类型**: Integer
- **默认值**: `1`
- **范围**: 1-100
- **说明**: 限制响应的最大token数
- **建议**: 保持为1以最小化成本

#### 5. success_contains
- **类型**: String
- **默认值**: `null` (不校验)
- **说明**: 预期响应内容应包含的关键字
- **用途**:
  - 为空时不进行内容校验
  - 有值时检查响应是否包含该关键字
  - 不匹配时标记为红色，错误类型为`content_mismatch`

#### 6. slow_latency_ms
- **类型**: Integer
- **默认值**: `5000`
- **范围**: 1000-30000
- **说明**: 慢速阈值，单位毫秒
- **用途**: 响应时间超过此值标记为黄色🟡

### 配置示例

#### 示例1: 完整配置
```json
{
  "production-claude": {
    "base_url": "https://api.anthropic.com",
    "auth_token": "sk-ant-xxx",
    "active": true,
    "enable_check": true,
    "check_model": "claude-3-haiku-20240307",
    "check_message": "hi",
    "check_max_tokens": 1,
    "success_contains": "hi",
    "slow_latency_ms": 5000
  }
}
```

#### 示例2: 最小配置（使用默认值）
```json
{
  "simple-site": {
    "base_url": "https://api.example.com",
    "auth_token": "sk-xxx",
    "active": true
  }
}
```

#### 示例3: 禁用检测
```json
{
  "disabled-site": {
    "base_url": "https://disabled.example.com",
    "auth_token": "sk-xxx",
    "active": false,
    "enable_check": false
  }
}
```

---

## API文档

### 检测端点

#### POST /api/site-availability/check

**功能**: 对指定站点执行可用性检测

**请求体**:
```json
{
  "sites": [
    {
      "service": "claude",
      "name": "site_name",
      "base_url": "https://api.example.com",
      "auth_token": "sk-xxx",
      "enable_check": true,
      "check_model": "claude-3-haiku-20240307",
      "check_message": "hi",
      "check_max_tokens": 1,
      "success_contains": "hi",
      "slow_latency_ms": 5000
    }
  ],
  "timeout": 10,
  "max_concurrent": 5
}
```

**响应体**:
```json
{
  "results": [
    {
      "service": "claude",
      "name": "site_name",
      "available": true,
      "status": 1,
      "sub_status": "none",
      "status_code": 200,
      "response_time_ms": 1234.56,
      "error": null,
      "error_type": null,
      "checked_at": "2025-12-07T14:23:12.123456Z"
    }
  ]
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | Integer | 0=红色(不可用), 1=绿色(可用), 2=黄色(降级) |
| `sub_status` | String | 详细状态类型（SubStatus枚举值） |
| `available` | Boolean | 是否可用（status==1） |
| `status_code` | Integer | HTTP状态码 |
| `response_time_ms` | Float | 响应时间（毫秒） |
| `error` | String | 错误信息（失败时） |
| `error_type` | String | 错误类型（向后兼容字段） |
| `checked_at` | String | 检测时间（ISO 8601格式） |

#### GET /api/site-availability/sites

**功能**: 获取所有站点配置（包含检测配置）

**响应体**:
```json
{
  "sites": [
    {
      "service": "claude",
      "name": "site_name",
      "base_url": "https://api.example.com",
      "active": true,
      "enable_check": true,
      "check_model": "claude-3-haiku-20240307",
      "check_message": "hi",
      "check_max_tokens": 1,
      "success_contains": "",
      "slow_latency_ms": 5000
    }
  ]
}
```

---

## 前端UI

### 配置界面

#### 交互模式
在"交互模式"标签下，每个站点卡片新增"检测配置"区域：

```
┌─────────────────────────────────┐
│ 站点名称: 88code                │
│ 目标地址: https://...           │
│ ─────────────────────────────   │
│ 检测配置:                       │
│   启用检测: [✓]                 │
│   检测模型: [claude-3-haiku...] │
│   检测消息: [hi              ]  │
│   最大Tokens: [1]               │
│   预期内容: [留空则不校验     ]  │
│   慢速阈值: [5000]              │
└─────────────────────────────────┘
```

#### 合并模式
在"合并模式"标签下，分组头部新增检测配置区域（可折叠）。

### 状态显示

#### 站点卡片状态指示器

```
🟢 绿色 - 正常可用
   └─ status=1, sub_status="none"
   └─ 显示响应时间（如：1234ms）

🟡 黄色 - 降级/慢速
   ├─ status=2, sub_status="slow_latency"
   │  └─ 显示：慢速 5678ms
   └─ status=2, sub_status="rate_limit"
      └─ 显示：限流

🔴 红色 - 不可用
   ├─ status=0, 各种sub_status
   └─ 显示错误信息 + 错误类型标签

🔵 蓝色 - 已禁用检测
   └─ enable_check=false
   └─ 显示：已禁用检测
```

#### 错误类型标签

当status=0或status=2时，显示对应的错误类型标签：

```css
.sub-status-badge.slow     /* 黄色背景：慢速 */
.sub-status-badge.error    /* 红色背景：各种错误 */
```

标签文本：
- 慢速、限流、认证失败、参数错误
- 服务器错误、内容不匹配、网络错误、客户端错误

---

## 技术实现

### 核心函数

#### 1. check_site_async() - 主检测函数

```python
async def check_site_async(site: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
    """
    执行单个站点的可用性检测

    流程:
    1. 构建POST请求到 {base_url}/v1/chat/completions
    2. 发送请求并计时
    3. 读取响应体（用于内容校验）
    4. 调用determine_status()判定基础状态
    5. 调用evaluate_status()进行内容校验（如果配置）
    6. 返回检测结果
    """
```

**关键点**:
- 使用`httpx.AsyncClient`进行异步HTTP请求
- 使用`response.aread()`读取完整响应体
- 异常处理：TimeoutException、ConnectError、HTTPStatusError等

#### 2. determine_status() - HTTP状态判定

```python
def determine_status(status_code: int, latency_ms: int, slow_threshold: int) -> Tuple[int, str]:
    """
    根据HTTP状态码和延迟判定监控状态

    返回: (status, sub_status)
    - status: 0=红色, 1=绿色, 2=黄色
    - sub_status: SubStatus枚举值
    """
```

**判定规则**:
```
2xx + 延迟正常 → (1, "none")           绿色
2xx + 延迟超标 → (2, "slow_latency")   黄色
3xx           → (1, "none")           绿色
401/403       → (0, "auth_error")     红色
400           → (0, "invalid_request") 红色
429           → (0, "rate_limit")     红色
5xx           → (0, "server_error")   红色
其他4xx        → (0, "client_error")   红色
```

#### 3. evaluate_status() - 内容校验

```python
def evaluate_status(
    base_status: int,
    base_sub_status: str,
    body: bytes,
    success_contains: str
) -> Tuple[int, str]:
    """
    在基础状态上叠加响应内容匹配规则

    规则:
    1. 如果没有配置success_contains，直接返回基础状态
    2. 红色已是最差状态，不需要校验
    3. 429限流的响应体是错误信息，不做内容校验
    4. 对2xx响应做内容校验（绿色和慢速黄色）
    5. 空响应或内容不匹配 → (0, "content_mismatch")
    """
```

#### 4. aggregate_response_text() - 响应文本提取

```python
def aggregate_response_text(body: bytes) -> str:
    """
    将原始响应体整理为用于关键字匹配的文本

    支持格式:
    1. OpenAI JSON: choices[0].message.content
    2. Anthropic JSON: content[0].text
    3. SSE流式: 调用extract_text_from_sse()
    4. 原始文本: 直接返回
    """
```

#### 5. extract_text_from_sse() - SSE解析

```python
def extract_text_from_sse(body: bytes) -> str:
    """
    从SSE响应中提取文本内容

    支持格式:
    - Anthropic: event: content_block_delta + data: {"delta":{"text":"..."}}
    - OpenAI: data: {"choices":[{"delta":{"content":"..."}}]}
    - 通用兜底: content或message字段
    """
```

### 前端核心逻辑

#### 1. 配置同步 (app.js)

```javascript
// JSON → 表单
function syncJsonToForm(service) {
    // 解析JSON配置
    // 提取新增的6个检测字段
    // 应用默认值
}

// 表单 → JSON
function syncFormToJson(service) {
    // 收集表单数据
    // 序列化为JSON
    // 可选字段处理（空值不保存）
}
```

#### 2. 检测逻辑 (site-availability.js)

```javascript
class SiteAvailabilityChecker {
    async checkAllSites() {
        // 过滤出enable_check=true的站点
        const enabledSites = this.state.sites.filter(
            site => site.enable_check !== false
        );

        // 调用API执行检测
        // 更新UI显示
    }

    renderSiteCard(site) {
        // 根据status和sub_status选择图标和文本
        // 渲染错误类型标签
    }

    getSubStatusBadge(subStatus) {
        // 返回错误类型的HTML标签
    }
}
```

---

## 测试指南

### 功能测试清单

#### 1. UI配置测试

**交互模式**:
- [ ] 打开"配置文件编辑" → "交互模式"
- [ ] 验证每个站点卡片显示6个检测配置字段
- [ ] 修改各字段值并保存
- [ ] 重新打开配置，验证修改已保存

**合并模式**:
- [ ] 打开"配置文件编辑" → "合并模式"
- [ ] 验证分组头部显示检测配置区域
- [ ] 测试折叠/展开功能
- [ ] 修改配置并保存

**JSON模式**:
- [ ] 打开"配置文件编辑" → "JSON模式"
- [ ] 手动编辑JSON添加新字段
- [ ] 验证JSON语法正确性
- [ ] 切换到交互模式验证解析正确

#### 2. 配置保存测试

```bash
# 查看配置文件
cat ~/.clp/claude.json
cat ~/.clp/codex.json

# 验证字段存在
# enable_check、check_model、check_message、check_max_tokens
# success_contains（如果配置）、slow_latency_ms（如果非默认）
```

#### 3. 检测功能测试

**基础检测**:
- [ ] 点击"检测所有站点"按钮
- [ ] 验证按钮变为"检测中..."并禁用
- [ ] 等待检测完成
- [ ] 验证站点状态更新（绿色/黄色/红色）
- [ ] 验证响应时间显示

**禁用检测测试**:
- [ ] 将某站点的`enable_check`设为`false`
- [ ] 点击"检测所有站点"
- [ ] 验证该站点显示蓝色🔵"已禁用检测"
- [ ] 验证该站点不会被检测

**慢速检测测试**:
- [ ] 设置`slow_latency_ms`为很小的值（如100）
- [ ] 执行检测
- [ ] 验证站点显示黄色🟡"慢速 XXXms"

**内容校验测试**:
- [ ] 设置`success_contains`为不可能出现的字符串
- [ ] 执行检测
- [ ] 验证站点显示红色🔴"内容不匹配"
- [ ] 验证显示错误类型标签

#### 4. 历史记录测试

- [ ] 点击站点卡片展开历史记录
- [ ] 验证显示历史检测记录
- [ ] 验证显示可用率统计
- [ ] 执行多次检测验证记录增长

#### 5. 向后兼容性测试

```bash
# 1. 备份现有配置
cp ~/.clp/claude.json ~/.clp/claude.json.bak

# 2. 恢复不含新字段的旧配置
cat > ~/.clp/claude.json << 'EOF'
{
  "old-site": {
    "base_url": "https://api.example.com",
    "auth_token": "sk-xxx",
    "active": true
  }
}
EOF

# 3. 重启服务器
# 4. 打开配置编辑器
# 5. 验证新字段使用默认值
# 6. 执行检测，验证功能正常
```

### 性能测试

#### Token消耗测试

```bash
# 记录检测前的token使用量
BEFORE=$(curl http://localhost:3300/api/stats | jq .total_tokens)

# 执行检测
curl -X POST http://localhost:3300/api/site-availability/check \
  -H "Content-Type: application/json" \
  -d '{"sites": [...], "timeout": 10}'

# 记录检测后的token使用量
AFTER=$(curl http://localhost:3300/api/stats | jq .total_tokens)

# 计算消耗
echo "Token消耗: $((AFTER - BEFORE)) tokens"
```

**预期结果**: 每个站点消耗20-30 tokens

#### 并发检测测试

```bash
# 测试5个站点并发检测
time curl -X POST http://localhost:3300/api/site-availability/check \
  -H "Content-Type: application/json" \
  -d '{
    "sites": [站点1, 站点2, 站点3, 站点4, 站点5],
    "timeout": 10,
    "max_concurrent": 5
  }'
```

**预期结果**: 总时间约等于单个最慢站点的响应时间

---

## 代码Review要点

### 1. 后端代码 (src/utils/site_checker.py)

**关键检查点**:

```python
# ✓ SubStatus枚举定义完整
class SubStatus:
    NONE = "none"
    SLOW_LATENCY = "slow_latency"
    # ... 共8种

# ✓ determine_status逻辑正确
def determine_status(status_code, latency_ms, slow_threshold):
    # HTTP状态码判定
    # 延迟判定
    # 返回(status, sub_status)

# ✓ evaluate_status内容校验逻辑
def evaluate_status(base_status, base_sub_status, body, success_contains):
    # 红色不校验（已是最差状态）
    # 429不校验（响应体是错误信息）
    # 2xx校验（绿色和慢速黄色）

# ✓ check_site_async主流程
async def check_site_async(site, timeout):
    # 1. 构建POST请求到/v1/chat/completions
    # 2. 发送请求并计时
    # 3. 读取响应体
    # 4. 判定基础状态
    # 5. 内容校验（如果配置）
    # 6. 返回结果

# ✓ 异常处理完整
try:
    # 正常流程
except httpx.TimeoutException:
    # 超时处理
except httpx.ConnectError:
    # 连接错误处理
except Exception:
    # 其他错误处理
```

**安全性检查**:
- [ ] 认证头正确设置（Bearer token）
- [ ] 超时设置合理（默认10秒）
- [ ] 响应体大小限制（避免内存溢出）
- [ ] 错误信息不泄露敏感信息

**性能检查**:
- [ ] 使用异步HTTP客户端（httpx.AsyncClient）
- [ ] 并发控制（max_concurrent参数）
- [ ] 连接池复用
- [ ] 响应体流式读取（aread()）

### 2. 前端代码

**app.js配置同步**:
```javascript
// ✓ 默认值处理
enableCheck: cfg.enable_check !== undefined ? cfg.enable_check : true

// ✓ 可选字段处理
if (site.successContains) {
    config.success_contains = site.successContains;
}

// ✓ 数据类型转换
checkMaxTokens: cfg.check_max_tokens || 1  // Number
```

**site-availability.js检测逻辑**:
```javascript
// ✓ 过滤禁用站点
const enabledSites = this.state.sites.filter(
    site => site.enable_check !== false
);

// ✓ 状态判定逻辑
if (site.enable_check === false) {
    // 蓝色：已禁用
} else if (site.status === 1) {
    // 绿色：可用
} else if (site.status === 2) {
    // 黄色：降级
} else if (site.status === 0) {
    // 红色：不可用
}

// ✓ 错误类型标签
const badges = {
    'slow_latency': '<span class="sub-status-badge slow">慢速</span>',
    // ... 其他类型
};
```

**index.html UI组件**:
- [ ] 所有字段都有label和placeholder
- [ ] 输入验证（min/max/step）
- [ ] 双向数据绑定（v-model）
- [ ] 事件处理（@change/@blur）

### 3. 数据流检查

```
配置保存流程:
用户编辑UI → syncFormToJson() → POST /api/config/{service} →
  ui_server保存JSON → ~/.clp/{service}.json

配置读取流程:
load_sites() → 读取JSON文件 → 应用默认值 →
  返回站点列表 → get_sites() API → 前端syncJsonToForm() →
  更新UI表单

检测执行流程:
前端checkAllSites() → 过滤enable_check=true →
  POST /api/site-availability/check → check_all_sites_async() →
  并发执行check_site_async() → 返回结果 →
  前端renderSiteCard()更新UI
```

### 4. 边界条件检查

**配置字段**:
- [ ] 空字符串处理
- [ ] null/undefined处理
- [ ] 超出范围的数值
- [ ] 特殊字符转义

**网络请求**:
- [ ] 超时处理
- [ ] 连接失败
- [ ] DNS解析失败
- [ ] SSL证书错误
- [ ] 响应体过大

**内容校验**:
- [ ] 空响应体
- [ ] 非UTF-8编码
- [ ] JSON解析失败
- [ ] SSE格式错误

---

## 向后兼容性

### 配置文件兼容

**旧配置示例**:
```json
{
  "old-site": {
    "base_url": "https://api.example.com",
    "auth_token": "sk-xxx",
    "active": true
  }
}
```

**行为**:
- `enable_check`默认为`true` → 自动启用检测
- `check_model`自动选择默认值
- `check_message`使用`"hi"`
- `check_max_tokens`使用`1`
- `success_contains`为`null` → 不校验内容
- `slow_latency_ms`使用`5000`

**结论**: 旧配置无缝升级，无需手动修改

### API兼容

**检测响应格式向后兼容**:
```json
{
  "service": "claude",
  "name": "site_name",
  "available": true,      // 保留：向后兼容
  "status": 1,            // 新增：三色状态
  "sub_status": "none",   // 新增：详细状态
  "status_code": 200,     // 保留
  "response_time_ms": 1234.56,  // 保留
  "error": null,          // 保留
  "error_type": null,     // 保留：等同于sub_status
  "checked_at": "..."     // 保留
}
```

**旧客户端兼容性**:
- 只使用`available`字段 → 功能正常
- 只使用`error`字段 → 功能正常
- 忽略新增字段 → 不影响功能

---

## 常见问题

### Q1: 为什么检测会消耗tokens？

**A**: 新版本使用POST /v1/chat/completions进行真实API调用，这是实际的LLM推理请求，会消耗tokens（每次约20-30个）。相比旧版的GET /v1/models（仅检查服务是否响应），新版本能更准确地检测API的实际可用性。

### Q2: 如何节省检测成本？

**A**:
1. 将不需要频繁检测的站点的`enable_check`设为`false`
2. 使用便宜的小模型（如claude-3-haiku或gpt-3.5-turbo）
3. 将`check_max_tokens`设为1
4. 使用简短的`check_message`（如"hi"）
5. 减少检测频率（手动触发而非自动定时）

### Q3: success_contains什么时候需要配置？

**A**:
- **不配置**（推荐）：仅检查API是否响应200
- **配置**：当需要验证API返回的内容是否正确时
  - 例如：检测某些站点是否返回了期望的模型响应
  - 例如：发现某些站点虽然返回200但内容是错误信息

### Q4: 慢速阈值怎么设置合理？

**A**:
- **默认5000ms**：适用于大多数情况
- **较小值（2000-3000ms）**：对响应速度要求高的场景
- **较大值（8000-10000ms）**：可以容忍较慢响应的场景
- **建议**：根据实际API的平均响应时间设置为1.5-2倍

### Q5: 为什么有的站点检测失败但实际可用？

**A**: 可能的原因：
1. **内容校验过严**：`success_contains`配置的关键字不合理
2. **超时时间过短**：默认10秒，某些API可能需要更长时间
3. **模型不支持**：`check_model`指定的模型在该站点不存在
4. **Token配额耗尽**：站点限流但UI健康检查仍能通过

**解决方法**：
- 检查配置是否合理
- 查看错误类型标签定位问题
- 查看站点历史记录分析趋势

---

## 附录

### A. 完整配置模板

```json
{
  "site_name": {
    // ========== 基础配置 ==========
    "base_url": "https://api.example.com",
    "auth_token": "sk-xxx",
    "api_key": "",
    "active": true,
    "weight": 0,

    // ========== 检测配置 ==========
    "enable_check": true,
    "check_model": "claude-3-haiku-20240307",
    "check_message": "hi",
    "check_max_tokens": 1,
    "success_contains": null,
    "slow_latency_ms": 5000
  }
}
```

### B. SubStatus错误码映射表

| SubStatus | 中文 | status | 显示颜色 | 触发条件 |
|-----------|------|--------|----------|----------|
| `none` | 正常 | 1 | 🟢 | 2xx + 延迟正常 |
| `slow_latency` | 慢速 | 2 | 🟡 | 2xx + 延迟超标 |
| `rate_limit` | 限流 | 0 | 🔴 | HTTP 429 |
| `auth_error` | 认证失败 | 0 | 🔴 | HTTP 401/403 |
| `invalid_request` | 参数错误 | 0 | 🔴 | HTTP 400 |
| `server_error` | 服务器错误 | 0 | 🔴 | HTTP 5xx |
| `content_mismatch` | 内容不匹配 | 0 | 🔴 | 响应不含success_contains |
| `network_error` | 网络错误 | 0 | 🔴 | 连接失败/超时 |
| `client_error` | 客户端错误 | 0 | 🔴 | 其他4xx |

### C. 测试数据集

**测试站点配置**:
```json
{
  "test-normal": {
    "base_url": "https://api.anthropic.com",
    "auth_token": "sk-ant-valid-token",
    "enable_check": true,
    "check_model": "claude-3-haiku-20240307",
    "check_message": "hi",
    "check_max_tokens": 1
  },
  "test-slow": {
    "base_url": "https://slow-api.example.com",
    "auth_token": "sk-xxx",
    "enable_check": true,
    "slow_latency_ms": 100
  },
  "test-content-check": {
    "base_url": "https://api.example.com",
    "auth_token": "sk-xxx",
    "enable_check": true,
    "success_contains": "IMPOSSIBLE_STRING_xyz123"
  },
  "test-disabled": {
    "base_url": "https://api.example.com",
    "auth_token": "sk-xxx",
    "enable_check": false
  }
}
```

---

## 更新日志

### v2.0 (2025-12-07)
- ✅ 检测方式从GET /v1/models升级为POST /v1/chat/completions
- ✅ 新增6个检测配置字段
- ✅ 实现三层状态判定（HTTP + 延迟 + 内容）
- ✅ 新增8种SubStatus错误分类
- ✅ 支持SSE流式响应解析（Anthropic + OpenAI）
- ✅ UI新增检测配置界面（交互模式 + 合并模式）
- ✅ 新增状态显示系统（三色 + 错误标签）
- ✅ 完全向后兼容旧配置

### v1.0 (之前版本)
- 基础HTTP健康检查（GET /v1/models）
- 简单的可用/不可用二元状态

---

## 参考资料

- **relay-pulse项目**: https://github.com/prehisle/relay-pulse
- **relay-pulse probe.go**: 核心检测逻辑的参考实现
- **Anthropic API文档**: https://docs.anthropic.com/
- **OpenAI API文档**: https://platform.openai.com/docs/

---

**文档版本**: 1.0
**最后更新**: 2025-12-07
**维护者**: CLI Proxy Team
