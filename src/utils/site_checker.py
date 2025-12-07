"""
Site Availability Checker Module

提供站点可用性检测功能,包括:
- 读取站点配置
- 异步检测站点可用性
- 错误分类和处理
- 历史记录持久化
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import httpx


# 错误分类枚举（参考relay-pulse的SubStatus）
class SubStatus:
    """检测状态细分类型"""
    NONE = "none"                          # 正常
    SLOW_LATENCY = "slow_latency"          # 慢速（黄色）
    RATE_LIMIT = "rate_limit"              # 429限流（红色）
    AUTH_ERROR = "auth_error"              # 401/403认证错误（红色）
    INVALID_REQUEST = "invalid_request"    # 400参数错误（红色）
    SERVER_ERROR = "server_error"          # 5xx服务器错误（红色）
    CONTENT_MISMATCH = "content_mismatch"  # 内容不匹配（红色）
    NETWORK_ERROR = "network_error"        # 网络错误（红色）
    CLIENT_ERROR = "client_error"          # 其他4xx错误（红色）


def get_default_model(service: str) -> str:
    """根据服务类型返回默认检测模型"""
    return {
        'claude': 'claude-3-haiku-20240307',
        'codex': 'gpt-3.5-turbo'
    }.get(service, 'gpt-3.5-turbo')


def get_error_message(sub_status: str) -> str:
    """根据SubStatus返回友好的错误消息"""
    messages = {
        SubStatus.SLOW_LATENCY: '响应过慢',
        SubStatus.RATE_LIMIT: 'API限流（429）',
        SubStatus.AUTH_ERROR: '认证失败（401/403）',
        SubStatus.INVALID_REQUEST: '请求参数错误（400）',
        SubStatus.SERVER_ERROR: '服务器错误（5xx）',
        SubStatus.CONTENT_MISMATCH: '响应内容不匹配',
        SubStatus.NETWORK_ERROR: '网络连接失败',
        SubStatus.CLIENT_ERROR: '客户端错误（4xx）'
    }
    return messages.get(sub_status, '未知错误')


def determine_status(status_code: int, latency_ms: int, slow_threshold: int) -> Tuple[int, str]:
    """
    根据HTTP状态码和延迟判定监控状态
    参考relay-pulse的实现方式

    Args:
        status_code: HTTP状态码
        latency_ms: 响应延迟(毫秒)
        slow_threshold: 慢速阈值(毫秒)

    Returns:
        (status, sub_status) 元组
        - status: 0=红色(不可用), 1=绿色(可用), 2=黄色(降级/慢速)
        - sub_status: SubStatus枚举值
    """
    # 2xx = 绿色或黄色(取决于延迟)
    if 200 <= status_code < 300:
        if latency_ms > slow_threshold:
            return (2, SubStatus.SLOW_LATENCY)  # 黄色慢速
        return (1, SubStatus.NONE)  # 绿色正常

    # 3xx = 绿色(重定向视为正常)
    if 300 <= status_code < 400:
        return (1, SubStatus.NONE)

    # 401/403 = 红色(认证失败)
    if status_code in (401, 403):
        return (0, SubStatus.AUTH_ERROR)

    # 400 = 红色(参数错误)
    if status_code == 400:
        return (0, SubStatus.INVALID_REQUEST)

    # 429 = 红色(限流)
    if status_code == 429:
        return (0, SubStatus.RATE_LIMIT)

    # 5xx = 红色(服务器错误)
    if status_code >= 500:
        return (0, SubStatus.SERVER_ERROR)

    # 其他4xx = 红色(客户端错误)
    if status_code >= 400:
        return (0, SubStatus.CLIENT_ERROR)

    # 其他未知状态码默认为客户端错误
    return (0, SubStatus.CLIENT_ERROR)


def extract_text_from_sse(body: bytes) -> str:
    """
    从SSE (Server-Sent Events) 响应中提取文本内容
    参考relay-pulse的实现方式

    支持格式:
    - Anthropic: event: content_block_delta + data: {"delta":{"text":"..."}}
    - OpenAI: data: {"choices":[{"delta":{"content":"..."}}]}

    Args:
        body: SSE格式的原始响应体

    Returns:
        聚合后的文本内容
    """
    body_str = body.decode('utf-8', errors='ignore')
    lines = body_str.split('\n')

    aggregated_text = []

    for line in lines:
        line = line.strip()
        if not line.startswith('data:'):
            continue

        payload = line[5:].strip()  # 去掉 "data:" 前缀
        if not payload or payload == '[DONE]':
            continue

        try:
            obj = json.loads(payload)

            # Anthropic格式: delta.text
            if 'delta' in obj and 'text' in obj['delta']:
                aggregated_text.append(obj['delta']['text'])

            # OpenAI格式: choices[0].delta.content
            if 'choices' in obj:
                for choice in obj['choices']:
                    if 'delta' in choice and 'content' in choice['delta']:
                        aggregated_text.append(choice['delta']['content'])

            # 通用兜底: content或message字段
            if 'content' in obj and isinstance(obj['content'], str):
                aggregated_text.append(obj['content'])
            if 'message' in obj and isinstance(obj['message'], str):
                aggregated_text.append(obj['message'])

        except json.JSONDecodeError:
            # 非JSON的data行,直接拼接
            aggregated_text.append(payload)

    return ''.join(aggregated_text)


def aggregate_response_text(body: bytes) -> str:
    """
    将原始响应体整理为用于关键字匹配的文本
    参考relay-pulse的实现方式

    支持:
    - 普通JSON: 提取content字段
    - SSE流式: 解析data行并聚合

    Args:
        body: 原始响应体(字节)

    Returns:
        提取出的文本内容,用于关键字匹配
    """
    if not body:
        return ""

    # 尝试解析为JSON
    try:
        data = json.loads(body)

        # OpenAI格式: choices[0].message.content
        if 'choices' in data and len(data['choices']) > 0:
            choice = data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                return choice['message']['content']

        # Anthropic格式: content[0].text
        if 'content' in data and len(data['content']) > 0:
            if 'text' in data['content'][0]:
                return data['content'][0]['text']

    except json.JSONDecodeError:
        pass

    # 检查是否是SSE格式
    body_str = body.decode('utf-8', errors='ignore')
    if 'event:' in body_str and 'data:' in body_str:
        return extract_text_from_sse(body)

    # 回退到原始文本
    return body_str


def evaluate_status(
    base_status: int,
    base_sub_status: str,
    body: bytes,
    success_contains: str
) -> Tuple[int, str]:
    """
    在基础状态上叠加响应内容匹配规则
    参考relay-pulse的实现方式

    Args:
        base_status: 基础状态(0=红, 1=绿, 2=黄)
        base_sub_status: 基础子状态
        body: 响应体字节
        success_contains: 预期包含的文本内容

    Returns:
        (status, sub_status) 元组
        - 内容匹配: 返回base_status
        - 内容不匹配: 返回(0, CONTENT_MISMATCH)
    """
    # 如果没有配置内容校验,直接返回基础状态
    if not success_contains:
        return (base_status, base_sub_status)

    # 红色已是最差状态,不需要校验
    if base_status == 0:
        return (base_status, base_sub_status)

    # 429限流: 响应体是错误信息,不做内容校验
    # (relay-pulse的逻辑: 429虽然是黄色,但响应内容无效)
    if base_status == 2 and base_sub_status == SubStatus.RATE_LIMIT:
        return (base_status, base_sub_status)

    # 对2xx响应做内容校验(绿色和慢速黄色)
    text = aggregate_response_text(body)

    # 空响应视为内容不匹配
    if not text.strip():
        return (0, SubStatus.CONTENT_MISMATCH)

    # 检查是否包含预期内容
    if success_contains not in text:
        return (0, SubStatus.CONTENT_MISMATCH)

    # 内容匹配,返回基础状态
    return (base_status, base_sub_status)


# 配置文件路径
def get_config_dir() -> Path:
    """获取配置目录路径"""
    return Path.home() / ".clp"


def get_data_dir() -> Path:
    """获取数据目录路径"""
    data_dir = get_config_dir() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_history_file() -> Path:
    """获取历史记录文件路径"""
    return get_data_dir() / "site_availability.json"


# T005: 站点配置读取
def load_sites() -> List[Dict[str, Any]]:
    """
    从配置文件读取所有站点配置

    Returns:
        站点配置列表,每个站点包含:
        - service: "claude" | "codex"
        - name: 站点名称
        - base_url: 基础URL
        - auth_token: 认证令牌
        - api_key: API密钥(可选)
        - active: 是否激活
    """
    sites = []

    # 读取Claude配置
    claude_file = get_config_dir() / "claude.json"
    if claude_file.exists():
        try:
            with open(claude_file, 'r', encoding='utf-8') as f:
                claude_configs = json.load(f)

            for name, config in claude_configs.items():
                if isinstance(config, dict) and 'base_url' in config:
                    site_config = {
                        'service': 'claude',
                        'name': name,
                        'base_url': config.get('base_url', ''),
                        'auth_token': config.get('auth_token', ''),
                        'api_key': config.get('api_key', ''),
                        'active': config.get('active', False),
                        # 新增检测配置字段
                        'enable_check': config.get('enable_check', True),
                        'check_model': config.get('check_model') or get_default_model('claude'),
                        'check_message': config.get('check_message', 'hi'),
                        'check_max_tokens': config.get('check_max_tokens', 1),
                        'success_contains': config.get('success_contains'),
                        'slow_latency_ms': config.get('slow_latency_ms', 5000)
                    }
                    sites.append(site_config)
        except (json.JSONDecodeError, OSError) as e:
            print(f"加载Claude配置失败: {e}")

    # 读取Codex配置
    codex_file = get_config_dir() / "codex.json"
    if codex_file.exists():
        try:
            with open(codex_file, 'r', encoding='utf-8') as f:
                codex_configs = json.load(f)

            for name, config in codex_configs.items():
                if isinstance(config, dict) and 'base_url' in config:
                    sites.append({
                        'service': 'codex',
                        'name': name,
                        'base_url': config.get('base_url', ''),
                        'auth_token': config.get('auth_token', ''),
                        'api_key': config.get('api_key', ''),
                        'active': config.get('active', False),
                        # 新增检测配置字段
                        'enable_check': config.get('enable_check', True),
                        'check_model': config.get('check_model') or get_default_model('codex'),
                        'check_message': config.get('check_message', 'hi'),
                        'check_max_tokens': config.get('check_max_tokens', 1),
                        'success_contains': config.get('success_contains'),
                        'slow_latency_ms': config.get('slow_latency_ms', 5000)
                    })
        except (json.JSONDecodeError, OSError) as e:
            print(f"加载Codex配置失败: {e}")

    return sites


# T006, T008: 异步站点检测和错误分类 (relay-pulse风格)
async def check_site_async(site: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
    """
    按照relay-pulse方式检测站点可用性
    使用POST /v1/chat/completions进行真实API调用检测

    Args:
        site: 站点配置字典,包含:
            - service: 服务类型
            - name: 站点名称
            - base_url: API基础URL
            - auth_token/api_key: 认证信息
            - check_model: 检测使用的模型
            - check_message: 检测消息内容
            - check_max_tokens: 最大token数
            - success_contains: 预期响应内容(可选)
            - slow_latency_ms: 慢速阈值
        timeout: 超时时间(秒)

    Returns:
        检测结果字典,包含:
        - service: 服务类型
        - name: 站点名称
        - available: 是否可用(True/False)
        - status: 状态码(0=红色, 1=绿色, 2=黄色)
        - sub_status: 子状态(SubStatus枚举值)
        - status_code: HTTP状态码
        - response_time_ms: 响应时间(毫秒)
        - error: 错误信息(失败时)
        - error_type: 错误类型(向后兼容)
        - checked_at: 检测时间戳
    """
    service = site.get('service', 'unknown')
    name = site.get('name', 'unknown')
    base_url = site.get('base_url', '')

    # 根据服务类型选择正确的API端点和格式
    if service == 'claude':
        # Claude/Anthropic格式
        check_url = base_url.rstrip('/') + '/v1/messages'
        request_body = {
            "model": site.get('check_model', get_default_model(service)),
            "messages": [
                {"role": "user", "content": site.get('check_message', 'hi')}
            ],
            "max_tokens": site.get('check_max_tokens', 1)
        }
        headers = {
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        # Claude使用x-api-key或authorization header
        if site.get('auth_token'):
            headers['x-api-key'] = site['auth_token']
        elif site.get('api_key'):
            headers['x-api-key'] = site['api_key']
    else:
        # OpenAI/Codex格式
        check_url = base_url.rstrip('/') + '/v1/chat/completions'
        request_body = {
            "model": site.get('check_model', get_default_model(service)),
            "messages": [
                {"role": "user", "content": site.get('check_message', 'hi')}
            ],
            "max_tokens": site.get('check_max_tokens', 1)
        }
        headers = {
            'Content-Type': 'application/json'
        }
        if site.get('api_key'):
            headers['Authorization'] = f"Bearer {site['api_key']}"
        elif site.get('auth_token'):
            headers['Authorization'] = f"Bearer {site['auth_token']}"

    checked_at = datetime.now(timezone.utc).isoformat()

    try:
        start_time = time.time()

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                check_url,
                json=request_body,
                headers=headers
            )

            elapsed_ms = (time.time() - start_time) * 1000

            # 读取响应体(用于内容校验和SSE解析)
            body_bytes = await response.aread()

            # 判定基础状态(HTTP状态码 + 延迟)
            status, sub_status = determine_status(
                response.status_code,
                int(elapsed_ms),
                site.get('slow_latency_ms', 5000)
            )

            # 内容校验(如果配置了success_contains)
            success_contains = site.get('success_contains')
            if success_contains:
                status, sub_status = evaluate_status(
                    status,
                    sub_status,
                    body_bytes,
                    success_contains
                )

            # 返回检测结果
            return {
                'service': service,
                'name': name,
                'available': status == 1,  # 1=绿色可用
                'status': status,  # 0=红色, 1=绿色, 2=黄色
                'sub_status': sub_status,
                'status_code': response.status_code,
                'response_time_ms': elapsed_ms,
                'error': None if status == 1 else get_error_message(sub_status),
                'error_type': sub_status if status != 1 else None,
                'checked_at': checked_at
            }

    except httpx.TimeoutException:
        return {
            'service': service,
            'name': name,
            'available': False,
            'status': 0,  # 红色
            'sub_status': SubStatus.NETWORK_ERROR,
            'status_code': None,
            'response_time_ms': None,
            'error': '请求超时',
            'error_type': 'timeout',  # 向后兼容
            'checked_at': checked_at
        }

    except httpx.ConnectError as e:
        return {
            'service': service,
            'name': name,
            'available': False,
            'status': 0,  # 红色
            'sub_status': SubStatus.NETWORK_ERROR,
            'status_code': None,
            'response_time_ms': None,
            'error': f'连接失败: {str(e)}',
            'error_type': 'network_error',  # 向后兼容
            'checked_at': checked_at
        }

    except httpx.NetworkError as e:
        return {
            'service': service,
            'name': name,
            'available': False,
            'status': 0,  # 红色
            'sub_status': SubStatus.NETWORK_ERROR,
            'status_code': None,
            'response_time_ms': None,
            'error': f'网络错误: {str(e)}',
            'error_type': 'network_error',  # 向后兼容
            'checked_at': checked_at
        }

    except Exception as e:
        return {
            'service': service,
            'name': name,
            'available': False,
            'status': 0,  # 红色
            'sub_status': SubStatus.NETWORK_ERROR,
            'status_code': None,
            'response_time_ms': None,
            'error': f'未知错误: {str(e)}',
            'error_type': 'unknown',  # 向后兼容
            'checked_at': checked_at
        }


# T007: 并发控制的批量检测
async def check_all_sites_async(
    sites: List[Dict[str, Any]],
    timeout: int = 10,
    max_concurrent: int = 5
) -> List[Dict[str, Any]]:
    """
    并发检测多个站点的可用性

    Args:
        sites: 站点配置列表
        timeout: 超时时间(秒)
        max_concurrent: 最大并发数

    Returns:
        检测结果列表
    """
    if not sites:
        return []

    # 过滤出启用检测的站点
    # enable_check默认为True,只过滤显式设置为False的站点
    enabled_sites = [site for site in sites if site.get('enable_check', True)]

    if not enabled_sites:
        return []

    # 使用信号量控制并发
    semaphore = asyncio.Semaphore(max_concurrent)

    async def check_with_limit(site: Dict[str, Any]) -> Dict[str, Any]:
        async with semaphore:
            return await check_site_async(site, timeout)

    # 创建所有任务
    tasks = [check_with_limit(site) for site in enabled_sites]

    # 等待所有任务完成
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 处理异常结果
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # 如果任务本身抛出异常,构建错误结果
            site = enabled_sites[i]
            processed_results.append({
                'service': site.get('service', 'unknown'),
                'name': site.get('name', 'unknown'),
                'available': False,
                'status_code': None,
                'response_time_ms': None,
                'error': f'检测失败: {str(result)}',
                'error_type': 'unknown',
                'checked_at': datetime.now(timezone.utc).isoformat()
            })
        else:
            processed_results.append(result)

    return processed_results


# T009: 历史记录持久化
def load_history() -> Dict[str, Any]:
    """
    从文件加载历史记录

    Returns:
        历史记录字典,格式:
        {
            "claude": {
                "site_name": [CheckResult, ...]
            },
            "codex": {
                "site_name": [CheckResult, ...]
            }
        }
    """
    history_file = get_history_file()

    if not history_file.exists():
        return {"claude": {}, "codex": {}}

    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)

        # 确保结构正确
        if not isinstance(history, dict):
            return {"claude": {}, "codex": {}}

        # 确保两个服务键存在
        history.setdefault('claude', {})
        history.setdefault('codex', {})

        return history

    except (json.JSONDecodeError, OSError) as e:
        print(f"加载历史记录失败: {e}")
        return {"claude": {}, "codex": {}}


def save_history(history: Dict[str, Any]) -> None:
    """
    保存历史记录到文件

    Args:
        history: 历史记录字典
    """
    history_file = get_history_file()

    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"保存历史记录失败: {e}")
        raise


def add_check_result(result: Dict[str, Any]) -> None:
    """
    添加检测结果到历史记录

    Args:
        result: 检测结果字典
    """
    history = load_history()

    service = result.get('service', 'unknown')
    name = result.get('name', 'unknown')

    # 确保服务键存在
    if service not in history:
        history[service] = {}

    # 确保站点键存在
    if name not in history[service]:
        history[service][name] = []

    # 添加到列表开头(最新在前)
    history[service][name].insert(0, result)

    # 保留最多10条记录
    history[service][name] = history[service][name][:10]

    # 保存到文件
    save_history(history)
