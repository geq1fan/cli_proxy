/**
 * Site Availability Checker Frontend Module
 *
 * 提供前端站点可用性检测功能:
 * - 加载和显示站点列表
 * - 手动触发站点检测
 * - 查看历史检测记录
 * - 实时更新UI状态
 */

const SiteAvailabilityChecker = {
    state: {
        sites: [],
        checking: false,
        lastCheck: null,
        expandedSites: new Set(),
        siteHistories: {} // 存储各站点的历史记录 {service-name: [records]}
    },

    /**
     * T014: 初始化模块 - 页面加载时调用
     * T019: 自动触发首次检测
     */
    async init() {
        console.log('Site Availability Checker initializing...');

        try {
            // 加载站点列表
            await this.loadSites();

            // 渲染初始状态
            this.render();

            // T025: 绑定事件监听器
            this.attachEventListeners();

            // T019: 首次加载时自动检测所有站点
            if (this.state.sites && this.state.sites.length > 0) {
                console.log('Auto-triggering initial site check...');
                await this.checkAllSites();
            }
        } catch (error) {
            console.error('Site availability checker initialization failed:', error);
        }
    },

    /**
     * T015: 从后端加载站点配置
     */
    async loadSites() {
        try {
            const response = await fetch('/api/site-availability/sites');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.state.sites = data.sites || [];

            console.log(`Loaded ${this.state.sites.length} sites`);

            return this.state.sites;
        } catch (error) {
            console.error('Failed to load sites:', error);
            this.state.sites = [];
            throw error;
        }
    },

    /**
     * T022: 触发所有站点检测
     * T023: 按钮状态管理
     * T024: 重复请求防护
     */
    async checkAllSites() {
        // T024: 防止重复请求
        if (this.state.checking) {
            console.log('Already checking, ignoring duplicate request');
            return;
        }

        // 过滤出启用检测的站点
        const enabledSites = this.state.sites.filter(site =>
            site.enable_check !== false  // 默认启用
        );

        if (enabledSites.length === 0) {
            alert('没有启用检测的站点');
            return;
        }

        console.log(`Starting site availability check for ${enabledSites.length} enabled sites...`);

        try {
            // T023: 设置检测状态
            this.state.checking = true;
            this.render(); // 更新UI显示"检测中..."

            // 发送检测请求（只检测启用的站点）
            const response = await fetch('/api/site-availability/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sites: enabledSites,
                    timeout: 10,
                    max_concurrent: 5
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const results = data.results || [];

            console.log(`Received ${results.length} check results`);

            // T026: 更新站点状态
            // 将检测结果合并到sites数组
            this.state.sites = this.state.sites.map(site => {
                const result = results.find(
                    r => r.service === site.service && r.name === site.name
                );

                if (result) {
                    return {
                        ...site,
                        available: result.available,
                        status_code: result.status_code,
                        response_time_ms: result.response_time_ms,
                        error: result.error,
                        error_type: result.error_type,
                        checked_at: result.checked_at
                    };
                }

                return site;
            });

            // 记录最后检测时间
            this.state.lastCheck = new Date();

            // T026: 重新渲染,显示检测结果
            this.render();

        } catch (error) {
            console.error('Site availability check failed:', error);
            alert('站点检测失败: ' + error.message);
        } finally {
            // 恢复状态
            this.state.checking = false;
            this.render(); // 更新按钮状态
        }
    },

    /**
     * 加载站点历史记录
     * User Story 3: 查看站点历史可用性记录
     */
    async loadHistory(service, name) {
        const cacheKey = `${service}-${name}`;

        // 如果已经加载过，直接返回缓存
        if (this.state.siteHistories[cacheKey]) {
            return this.state.siteHistories[cacheKey];
        }

        try {
            const response = await fetch(`/api/site-availability/history?service=${service}&name=${name}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const records = data.records || [];

            // 缓存历史记录
            this.state.siteHistories[cacheKey] = records;

            console.log(`Loaded ${records.length} history records for ${service}/${name}`);
            return records;

        } catch (error) {
            console.error(`Failed to load history for ${service}/${name}:`, error);
            return [];
        }
    },

    /**
     * 获取错误类型标签HTML
     * 显示SubStatus细分类型
     */
    getSubStatusBadge(subStatus) {
        if (!subStatus || subStatus === 'none') {
            return '';
        }

        const badges = {
            'slow_latency': '<span class="sub-status-badge slow">慢速</span>',
            'rate_limit': '<span class="sub-status-badge error">限流</span>',
            'auth_error': '<span class="sub-status-badge error">认证失败</span>',
            'invalid_request': '<span class="sub-status-badge error">参数错误</span>',
            'server_error': '<span class="sub-status-badge error">服务器错误</span>',
            'content_mismatch': '<span class="sub-status-badge error">内容不匹配</span>',
            'network_error': '<span class="sub-status-badge error">网络错误</span>',
            'client_error': '<span class="sub-status-badge error">客户端错误</span>'
        };

        return badges[subStatus] || '';
    },

    /**
     * T016: 渲染单个站点卡片
     * T020: 包含视觉状态指示器 (🟢/🔴/⚪)
     * User Story 3: 支持展开查看历史记录
     */
    renderSiteCard(site) {
        // 确定状态图标和文本
        let statusIcon = '⚪'; // 默认未检测
        let statusText = '未检测';
        let statusClass = '';
        let subStatusBadge = '';  // 新增：错误类型标签

        // 禁用检测的站点
        if (site.enable_check === false) {
            statusIcon = '🔵';
            statusText = '已禁用检测';
            statusClass = 'disabled';
        }
        else if (this.state.checking) {
            statusText = '检测中...';
            statusClass = 'checking';
        }
        else if (site.status === 1) {  // 绿色可用
            statusIcon = '🟢';
            statusText = site.response_time_ms
                ? `${Math.round(site.response_time_ms)}ms`
                : '可用';
            statusClass = 'available';
        }
        else if (site.status === 2) {  // 黄色（慢速或限流）
            statusIcon = '🟡';
            statusText = site.sub_status === 'slow_latency'
                ? `慢速 ${Math.round(site.response_time_ms)}ms`
                : '降级';
            statusClass = 'degraded';
            subStatusBadge = this.getSubStatusBadge(site.sub_status);
        }
        else if (site.status === 0) {  // 红色不可用
            statusIcon = '🔴';
            statusText = site.error || '不可用';
            statusClass = 'unavailable';
            subStatusBadge = this.getSubStatusBadge(site.sub_status);
        }
        // 向后兼容：旧的available字段
        else if (site.available === true) {
            statusIcon = '🟢';
            statusText = site.response_time_ms
                ? `${Math.round(site.response_time_ms)}ms`
                : '可用';
            statusClass = 'available';
        }
        else if (site.available === false) {
            statusIcon = '🔴';
            statusText = site.error || '不可用';
            statusClass = 'unavailable';
        }

        // 服务类型徽章样式
        const badgeClass = site.service === 'claude' ? 'claude-badge' : 'codex-badge';

        // 检查是否已展开
        const siteKey = `${site.service}-${site.name}`;
        const isExpanded = this.state.expandedSites.has(siteKey);
        const expandIcon = isExpanded ? '▼' : '▶';

        // 渲染历史记录区域 (如果已展开)
        let historyHTML = '';
        if (isExpanded) {
            const history = this.state.siteHistories[siteKey] || null;
            if (history === null) {
                // 正在加载
                historyHTML = `
                    <div class="site-history">
                        <div class="history-loading">加载历史记录中...</div>
                    </div>
                `;
            } else {
                historyHTML = `
                    <div class="site-history">
                        ${this.renderHistoryRecords(history)}
                    </div>
                `;
            }
        }

        return `
            <div class="site-card ${isExpanded ? 'expanded' : ''}" data-service="${site.service}" data-name="${site.name}">
                <div class="site-main" data-clickable="true">
                    <div class="site-header">
                        <span class="site-name">
                            <span class="expand-icon">${expandIcon}</span>
                            ${site.name}
                        </span>
                        <span class="service-badge ${badgeClass}">${site.service}</span>
                    </div>
                    <div class="site-status ${statusClass}">
                        <span class="status-icon">${statusIcon}</span>
                        <span class="status-text">${statusText}</span>
                        ${subStatusBadge}
                    </div>
                    <div class="site-url" title="${site.base_url}">${site.base_url}</div>
                </div>
                ${historyHTML}
            </div>
        `;
    },

    /**
     * T017: 渲染所有站点
     * T026: 实时更新检测结果
     */
    render() {
        const container = document.getElementById('sites-list');

        if (!container) {
            console.warn('Sites list container not found');
            return;
        }

        // 如果没有站点,显示空状态
        if (!this.state.sites || this.state.sites.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="el-icon-warning-outline"></i>
                    <p>暂无站点配置</p>
                </div>
            `;
            return;
        }

        // 渲染所有站点卡片
        const cardsHTML = this.state.sites.map(site => this.renderSiteCard(site)).join('');
        container.innerHTML = cardsHTML;

        // T027: 更新最后检测时间显示
        this.updateLastCheckTime();

        // T023: 更新按钮状态
        this.updateCheckButtonState();
    },

    /**
     * T027: 更新最后检测时间显示
     */
    updateLastCheckTime() {
        const timeElement = document.getElementById('last-check-time');

        if (timeElement) {
            if (this.state.lastCheck) {
                const timeStr = this.state.lastCheck.toLocaleTimeString('zh-CN');
                timeElement.textContent = `最后检测: ${timeStr}`;
                timeElement.style.display = 'inline';
            } else {
                timeElement.textContent = '';
                timeElement.style.display = 'none';
            }
        }
    },

    /**
     * T023: 更新检测按钮状态
     */
    updateCheckButtonState() {
        const checkBtn = document.getElementById('check-all-btn');

        if (checkBtn) {
            if (this.state.checking) {
                checkBtn.textContent = '检测中...';
                checkBtn.disabled = true;
                checkBtn.classList.add('checking');
            } else {
                checkBtn.textContent = '检测所有站点';
                checkBtn.disabled = false;
                checkBtn.classList.remove('checking');
            }
        }
    },

    /**
     * 渲染历史记录列表
     * User Story 3: 显示历史检测记录
     */
    renderHistoryRecords(records) {
        if (!records || records.length === 0) {
            return `
                <div class="history-empty">
                    <i class="el-icon-info"></i>
                    <p>暂无历史记录</p>
                </div>
            `;
        }

        // 计算可用率统计
        const availableCount = records.filter(r => r.available).length;
        const availabilityRate = ((availableCount / records.length) * 100).toFixed(1);

        // 渲染每条历史记录
        const recordsHTML = records.map(record => {
            const statusIcon = record.available ? '🟢' : '🔴';
            const statusClass = record.available ? 'available' : 'unavailable';
            const time = new Date(record.checked_at).toLocaleString('zh-CN', {
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });

            let detailText = '';
            if (record.available) {
                detailText = record.response_time_ms
                    ? `${Math.round(record.response_time_ms)}ms`
                    : '可用';
            } else {
                detailText = record.error || '不可用';
            }

            return `
                <div class="history-record ${statusClass}">
                    <span class="history-icon">${statusIcon}</span>
                    <span class="history-time">${time}</span>
                    <span class="history-detail">${detailText}</span>
                </div>
            `;
        }).join('');

        return `
            <div class="history-stats">
                <div class="stat-item">
                    <span class="stat-label">历史记录:</span>
                    <span class="stat-value">${records.length} 次</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">可用率:</span>
                    <span class="stat-value ${availabilityRate >= 80 ? 'good' : 'poor'}">${availabilityRate}%</span>
                </div>
            </div>
            <div class="history-list">
                ${recordsHTML}
            </div>
        `;
    },

    /**
     * 处理站点卡片点击事件
     * User Story 3: 点击站点卡片展开/收起历史记录
     */
    async handleSiteCardClick(event) {
        // 找到被点击的站点卡片
        const card = event.target.closest('.site-card');
        if (!card) return;

        // 只响应site-main区域的点击
        const mainArea = event.target.closest('.site-main');
        if (!mainArea) return;

        const service = card.dataset.service;
        const name = card.dataset.name;
        const siteKey = `${service}-${name}`;

        // 切换展开状态
        if (this.state.expandedSites.has(siteKey)) {
            // 收起
            this.state.expandedSites.delete(siteKey);
        } else {
            // 展开
            this.state.expandedSites.add(siteKey);

            // 如果还没加载历史，触发加载
            if (!this.state.siteHistories[siteKey]) {
                // 先重新渲染显示"加载中..."
                this.render();

                // 加载历史记录
                await this.loadHistory(service, name);
            }
        }

        // 重新渲染
        this.render();
    },

    /**
     * T025: 绑定事件监听器
     * User Story 3: 添加站点卡片点击事件
     */
    attachEventListeners() {
        // T025: 绑定刷新按钮
        const checkBtn = document.getElementById('check-all-btn');

        if (checkBtn) {
            checkBtn.addEventListener('click', () => {
                this.checkAllSites();
            });
            console.log('Check button event listener attached');
        } else {
            console.warn('Check button not found');
        }

        // User Story 3: 绑定站点卡片点击事件 (使用事件委托)
        const container = document.getElementById('sites-list');
        if (container) {
            container.addEventListener('click', (event) => {
                this.handleSiteCardClick(event);
            });
            console.log('Site card click listener attached');
        }
    }
};

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SiteAvailabilityChecker;
}
