# 站点可用性检测功能 - 测试检查清单

## 快速测试流程

### 1. UI配置测试 (5分钟)

```bash
# 启动服务器
uv run clp server

# 打开浏览器
http://localhost:3300
```

**检查项**:
- [ ] 点击"配置数量" → "交互模式"
- [ ] 验证看到"检测配置"区域（6个字段）
- [ ] 修改"预期内容"为"hello"
- [ ] 点击"保存配置"
- [ ] 看到"配置保存成功"提示

---

### 2. 配置文件验证 (1分钟)

```bash
# 查看配置文件
cat ~/.clp/claude.json

# 应该看到:
# "enable_check": true,
# "check_message": "hi",
# "check_max_tokens": 1,
# "success_contains": "hello"
```

**检查项**:
- [ ] 新字段已保存到JSON文件
- [ ] JSON格式正确（无语法错误）

---

### 3. 基础检测测试 (2分钟)

**操作**:
1. 在主页面点击"检测所有站点"按钮
2. 等待检测完成（约5-10秒）

**预期结果**:
- [ ] 按钮变为"检测中..."并禁用
- [ ] 站点状态图标变为⚪"检测中..."
- [ ] 检测完成后显示🟢/🟡/🔴状态
- [ ] 显示响应时间（如"2417ms"）
- [ ] "最后检测"时间更新

---

### 4. 禁用检测测试 (2分钟)

**操作**:
1. 进入"配置编辑" → "交互模式"
2. 找到任意站点，关闭"启用检测"开关
3. 保存配置
4. 返回主页面，点击"检测所有站点"

**预期结果**:
- [ ] 该站点显示🔵蓝色
- [ ] 状态文本为"已禁用检测"
- [ ] 该站点不会被实际检测

---

### 5. 慢速检测测试 (2分钟)

**操作**:
1. 进入"配置编辑" → "交互模式"
2. 设置"慢速阈值"为100ms
3. 保存配置
4. 执行检测

**预期结果**:
- [ ] 站点显示🟡黄色
- [ ] 状态文本为"慢速 XXXXms"
- [ ] 可能显示"慢速"标签

---

### 6. 内容校验测试 (2分钟)

**操作**:
1. 进入"配置编辑" → "交互模式"
2. 设置"预期内容"为"IMPOSSIBLE_xyz123"
3. 保存配置
4. 重启服务器（重要！）
5. 执行检测

**预期结果**:
- [ ] 站点显示🔴红色
- [ ] 错误信息为"内容不匹配"
- [ ] 显示红色"内容不匹配"标签

**注意**: 内容校验需要重启服务器才能生效！

---

### 7. 历史记录测试 (1分钟)

**操作**:
1. 点击任意站点卡片的 "▶" 图标
2. 查看展开的历史记录

**预期结果**:
- [ ] 显示历史检测记录列表
- [ ] 显示"历史记录: X次"
- [ ] 显示"可用率: XX.X%"
- [ ] 每条记录显示时间、状态、响应时间

---

### 8. 向后兼容性测试 (3分钟)

**操作**:
```bash
# 1. 备份现有配置
cp ~/.clp/claude.json ~/.clp/claude.json.bak

# 2. 创建旧格式配置（不含新字段）
cat > ~/.clp/claude.json << 'EOF'
{
  "test-old": {
    "base_url": "https://api.anthropic.com",
    "auth_token": "your-token-here",
    "active": true
  }
}
EOF

# 3. 重启服务器
# 按Ctrl+C停止，然后重新运行: uv run clp server

# 4. 刷新浏览器页面
```

**预期结果**:
- [ ] 配置正常加载
- [ ] 进入"交互模式"看到新字段使用默认值
- [ ] 执行检测功能正常
- [ ] 保存配置后新字段添加到JSON

**恢复配置**:
```bash
mv ~/.clp/claude.json.bak ~/.clp/claude.json
```

---

## 完整测试清单

### UI功能
- [ ] 交互模式显示检测配置
- [ ] 合并模式显示检测配置
- [ ] JSON模式手动编辑
- [ ] 配置保存成功
- [ ] 配置加载正确

### 检测功能
- [ ] 基础检测（绿色）
- [ ] 慢速检测（黄色）
- [ ] 内容校验失败（红色）
- [ ] 禁用检测（蓝色）
- [ ] 错误类型标签显示

### 数据持久化
- [ ] 配置保存到JSON文件
- [ ] 历史记录保存
- [ ] 统计数据更新

### 兼容性
- [ ] 旧配置升级
- [ ] 新字段默认值
- [ ] API向后兼容

---

## 性能测试

### Token消耗测试

```bash
# 1. 记录检测前token数
curl http://localhost:3300/api/stats | jq .total_tokens

# 2. 执行一次检测（假设2个站点）

# 3. 记录检测后token数
curl http://localhost:3300/api/stats | jq .total_tokens

# 4. 计算消耗
# 预期: 每站点约20-30 tokens，2个站点约40-60 tokens
```

### 响应时间测试

```bash
# 测试检测接口响应时间
time curl -X POST http://localhost:3300/api/site-availability/check \
  -H "Content-Type: application/json" \
  -d '{
    "sites": [...],
    "timeout": 10,
    "max_concurrent": 5
  }'

# 预期: 总时间 ≈ 最慢站点的响应时间（并发执行）
```

---

## 故障排查

### 问题1: 内容校验不生效

**症状**: 设置了success_contains但检测仍显示绿色

**原因**: Python模块在服务启动时加载，修改代码后需要重启

**解决**:
```bash
# 停止服务器（Ctrl+C）
# 重新启动
uv run clp server
```

### 问题2: 检测按钮点击无响应

**症状**: 点击"检测所有站点"后没有反应

**解决**:
1. 检查浏览器控制台是否有错误
2. 检查是否有站点启用了检测（enable_check=true）
3. 检查服务器日志是否有错误
4. 刷新页面重试

### 问题3: 所有站点显示红色

**症状**: 检测后所有站点都显示不可用

**可能原因**:
1. 网络连接问题
2. API密钥无效
3. success_contains配置错误
4. 模型名称不支持

**解决**:
1. 检查网络连接
2. 验证API密钥有效性
3. 移除success_contains配置
4. 使用默认模型名称

### 问题4: JSON配置保存失败

**症状**: 修改配置后保存，但重新打开仍是旧值

**解决**:
1. 检查~/.clp/目录权限
2. 检查JSON语法是否正确
3. 检查浏览器控制台错误信息
4. 手动编辑JSON文件验证

---

## 测试完成标准

全部测试项通过，即可认为功能正常：

- ✅ UI配置界面显示正确
- ✅ 配置保存到文件成功
- ✅ 基础检测功能正常
- ✅ 状态显示正确（绿/黄/红/蓝）
- ✅ 错误类型标签显示
- ✅ 历史记录功能正常
- ✅ 向后兼容性良好
- ✅ 性能符合预期

---

## 快速测试脚本

```bash
#!/bin/bash

echo "=== 站点可用性检测功能测试 ==="

# 1. 检查服务器运行状态
echo "1. 检查服务器..."
if curl -s http://localhost:3300 > /dev/null; then
    echo "   ✓ 服务器运行正常"
else
    echo "   ✗ 服务器未运行，请先启动: uv run clp server"
    exit 1
fi

# 2. 检查配置文件
echo "2. 检查配置文件..."
if [ -f ~/.clp/claude.json ]; then
    echo "   ✓ 配置文件存在"

    # 检查新字段
    if grep -q "enable_check" ~/.clp/claude.json; then
        echo "   ✓ 新字段已添加"
    else
        echo "   ! 未找到新字段（可能是首次运行）"
    fi
else
    echo "   ✗ 配置文件不存在"
    exit 1
fi

# 3. 测试API端点
echo "3. 测试API端点..."
if curl -s http://localhost:3300/api/site-availability/sites > /dev/null; then
    echo "   ✓ API端点响应正常"
else
    echo "   ✗ API端点无响应"
    exit 1
fi

# 4. 执行检测
echo "4. 执行检测测试..."
RESULT=$(curl -s -X POST http://localhost:3300/api/site-availability/check \
    -H "Content-Type: application/json" \
    -d '{"timeout": 10}')

if echo "$RESULT" | jq -e '.results' > /dev/null 2>&1; then
    echo "   ✓ 检测执行成功"
    COUNT=$(echo "$RESULT" | jq '.results | length')
    echo "   检测了 $COUNT 个站点"
else
    echo "   ✗ 检测执行失败"
    exit 1
fi

echo ""
echo "=== 基础功能测试通过 ==="
echo "请继续手动测试UI功能"
```

保存为`test.sh`并执行：
```bash
chmod +x test.sh
./test.sh
```

---

**文档版本**: 1.0
**最后更新**: 2025-12-07
