# LLM API 测试项目

独立的LLM API测试工具，用于开发、调试和测试OpenAI兼容的API调用功能。

## 项目结构

```
llm_api_test/
├── llm_client.py      # LLM客户端核心代码
├── test_api.py        # 综合测试工具
├── debug_stream.py    # 流式响应调试工具
├── config.json        # 配置文件（需自行创建）
├── config.example.json # 配置文件示例
├── requirements.txt   # 依赖包
└── README.md          # 本说明文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

复制配置文件示例并填入您的API密钥：

```bash
cp config.example.json config.json
```

编辑 `config.json`，将 `YOUR_xxx_API_KEY` 替换为实际的API密钥。

### 3. 运行测试

```bash
# 运行所有API测试
python test_api.py

# 测试指定API
python test_api.py --api DeepSeek

# 开启调试模式
python test_api.py --debug

# 快速测试（仅非流式）
python test_api.py --quick
```

## 工具说明

### test_api.py - 综合测试工具

执行完整的API测试套件：

| 测试项 | 说明 |
|--------|------|
| 模型列表 | 测试 `GET /v1/models` 接口 |
| 非流式生成 | 测试 `POST /v1/chat/completions` 非流式模式 |
| 流式生成 | 测试流式SSE响应 |
| 错误处理 | 测试无效密钥、无效模型、无效URL等场景 |

**命令行参数：**

```
--config, -c    配置文件路径（默认: config.json）
--api, -a       指定要测试的API名称
--debug, -d     开启调试模式，输出详细信息
--quick, -q     快速测试模式，仅测试非流式生成
```

### debug_stream.py - 流式响应调试工具

专门用于调试流式API响应问题，输出原始数据：

```bash
# 调试指定API的流式响应
python debug_stream.py --api DeepSeek

# 使用自定义消息测试
python debug_stream.py --api "GG公益站" --message "你好"
```

**输出内容包括：**
- HTTP状态码和响应头
- 每行原始数据
- JSON解析结果
- 内容块提取过程
- 统计信息（总行数、有效块数、内容长度）

## 配置文件格式

```json
{
  "apis": [
    {
      "name": "API名称",
      "base_url": "https://api.example.com",
      "api_key": "your-api-key",
      "model": "model-name",
      "stream": true
    }
  ],
  "test_settings": {
    "timeout": 60,
    "test_message": "请回复：测试成功"
  }
}
```

## 支持的API

任何兼容OpenAI API格式的服务：

- OpenAI
- DeepSeek
- Claude (通过兼容层)
- 本地部署模型 (Ollama, vLLM等)
- 其他第三方API

## 常见问题排查

### 1. 流式生成返回空内容

使用 `debug_stream.py` 查看原始响应：

```bash
python debug_stream.py --api "问题API名称"
```

检查输出中：
- 是否有 `choices` 字段
- `delta` 中是否有 `content`
- 响应格式是否符合OpenAI标准

### 2. 连接超时

- 检查网络连接
- 确认 `base_url` 正确
- 尝试增加超时时间

### 3. 认证失败

- 确认API密钥正确
- 检查密钥是否有足够权限
- 确认账户余额

## 核心代码说明

### llm_client.py

提供两个主要函数：

```python
# 获取模型列表
models = list_models(base_url, api_key)

# 非流式生成
text, _ = chat_completion(base_url, api_key, model, messages, stream=False)

# 流式生成
_, generator = chat_completion(base_url, api_key, model, messages, stream=True)
for delta in generator:
    print(delta, end='')
```

## 独立运行

此测试项目完全独立，可以复制到任何位置运行：

```bash
# 复制整个目录
cp -r llm_api_test /path/to/destination/

# 在新位置运行
cd /path/to/destination/llm_api_test
pip install -r requirements.txt
python test_api.py
```
