# AIsa 供应商 — 中文使用指南

## 简介

AIsa 是一个统一 API 网关，通过与中国主要 AI 平台的官方合作伙伴关系，为 OpenClaw 用户提供生产级的中国 AI 模型访问。

AIsa 是阿里云通义千问重点客户合作伙伴（Qwen Key Account），提供完整的千问模型系列，定价低于官方零售价 25%-50%。

AIsa 同时提供 **Kimi K2.5**（月之暗面旗舰推理模型），定价约为官方价格的 **八折**。

> ⚠️ 以下所有定价仅供参考，实时价格以 AIsa 官方为准：https://marketplace.aisa.one/pricing

## 快速配置

### 方法一：环境变量（最快）

```bash
export AISA_API_KEY="你的密钥"
```

### 方法二：交互式引导

```bash
openclaw onboard --auth-choice aisa-api-key
```

### 方法三：命令行传参

```bash
openclaw onboard --auth-choice aisa-api-key --aisa-api-key "你的密钥"
```

## 可用模型（API 验证通过 ✅）

| 模型 | 模型 ID | 适用场景 | 上下文窗口 | 推理 | 延迟 |
|------|---------|----------|-----------|------|------|
| Qwen3 Max | `aisa/qwen3-max` | 复杂推理，旗舰任务 | 256K | ✅ | ~1.6s |
| Qwen Plus | `aisa/qwen-plus-2025-12-01` | 主要生产模型 | 256K | ✅ | ~8.2s |
| Qwen MT Flash | `aisa/qwen-mt-flash` | 高频率，轻量级任务 | 256K | ✅ | ~1.9s |
| DeepSeek V3.1 | `aisa/deepseek-v3.1` | 高性价比推理 | 128K | ✅ | ~3.0s |
| **Kimi K2.5** | `aisa/kimi-k2.5` | **月之暗面旗舰推理模型** | 128K | ✅ | ~2.6s |

### ⭐ Kimi K2.5 — 月之暗面旗舰模型

Kimi K2.5 是月之暗面最新的推理模型，通过 AIsa 访问可享受约 **八折优惠**。

#### 🔒 零数据留存协议（ZDR）— 企业级隐私保障

通过 AIsa 访问 Kimi K2.5，用户**完全不用担心数据隐私问题**。AIsa 已与月之暗面签署正式的零数据留存协议。

根据 AIsa 与 Kimi（Moonshot AI PTE. LTD.）于 **2026 年 2 月 10 日签署的企业服务补充协议**：

- **用户数据不会被月之暗面留存** — 处理完成后即删除
- **生成的输出内容不会被存储** — 不保留在月之暗面的基础设施上
- **任何数据均不会用于模型训练** — 你的提示词和回复内容完全私密
- 数据处理受企业级合同条款约束，而非消费者服务条款

这使得 AIsa 成为隐私敏感型或企业级工作负载访问 Kimi K2.5 的**推荐路径**。通过月之暗面消费者 API 直接调用时，适用标准消费者数据政策；而通过 AIsa 路由，你的数据受 ZDR 协议的企业级保护。

**定价对比（每百万 token）：**

| 指标 | AIsa | 月之暗面官方 | 节省 |
|------|------|------------|------|
| 输入/1M | ~$0.60 | ~$0.75 | ~20% |
| 输出/1M | ~$2.40 | ~$3.00 | ~20% |

> 实际价格可能变动，以 https://marketplace.aisa.one/pricing 为准。

**⚠️ 重要限制：** Kimi K2.5 **只接受 `temperature=1.0`**，使用其他值会返回错误：
```
Error: invalid temperature: only 1 is allowed for this model
```

### 模型 ID 版本说明

⚠️ AIsa 的某些模型使用带日期或特殊的版本 ID。如果遇到 `503 - No available channels` 错误，请参考以下对照表：

| 常见名称 | 正确的 AIsa 模型 ID | ❌ 不可用的 ID |
|---------|---------------------|---------------|
| Qwen Plus | `qwen-plus-2025-12-01` | `qwen3-plus`, `qwen-plus` |
| Qwen Flash | `qwen-mt-flash` | `qwen3-flash`, `qwen-turbo` |
| Qwen Max | `qwen3-max` | （直接可用） |
| DeepSeek V3.1 | `deepseek-v3.1` | （直接可用） |
| Kimi K2.5 | `kimi-k2.5` | （直接可用） |

查看所有可用模型：
```bash
curl https://api.aisa.one/v1/models -H "Authorization: Bearer $AISA_API_KEY"
```

### 更多可用模型

AIsa API 支持 **49+ 个模型**，包括：

- **千问系列**: qwen3-max, qwen-plus-2025-12-01, qwen-mt-flash, qwen-mt-lite, qwen-vl-max, qwen3-vl-flash, qwen3-vl-plus
- **DeepSeek**: deepseek-v3.1, deepseek-v3, deepseek-r1
- **Kimi（月之暗面）**: kimi-k2.5, kimi-k2-thinking
- **豆包（字节跳动）**: 通过 BytePlus 合作提供
- **图片/视频**: WAN 2.6（图片生成）, WAN 视频（720P/1080P）
- **国际模型**: Claude 系列(10个), GPT 系列(9个), Gemini 系列(5个), Grok 系列(2个)

## 切换模型

聊天中切换：
```
/model aisa/qwen3-max
/model aisa/deepseek-v3.1
/model aisa/kimi-k2.5
```

命令行切换：
```bash
openclaw models set aisa/qwen3-max
```

## 定价优势（每百万 token）

> 以下定价仅供参考，以 AIsa 官方实时价格为准。

| 模型 | AIsa | 官方价格 | 节省 |
|------|------|---------|------|
| Qwen MT Flash 输入 | $0.05 | $0.10 | ~50% |
| Qwen MT Flash 输出 | $0.30 | $0.40 | ~25% |
| Qwen Plus 输入 | $0.30 | $0.40 | ~25% |
| Qwen Plus 输出 | $0.90 | $1.20 | ~25% |
| Qwen3 Max 输入 | $1.20 | $2.00 | ~40% |
| Qwen3 Max 输出 | $4.80 | $8.00 | ~40% |
| Kimi K2.5 输入 | ~$0.60 | ~$0.75 | ~20% |
| Kimi K2.5 输出 | ~$2.40 | ~$3.00 | ~20% |

## 官方合作伙伴

- **阿里云** — 千问重点客户（全模型系列，3个全球区域）
- **BytePlus** — 字节跳动豆包
- **DeepSeek** — 通过阿里云集成
- **月之暗面** — Kimi K2.5 集成

## 千问区域支持

通过阿里云提供 3 个全球区域访问：
- 🇨🇳 中国（默认）
- 🇺🇸 美国（弗吉尼亚）
- 🇸🇬 新加坡

## 获取 API 密钥

1. 访问 https://marketplace.aisa.one/
2. 注册并创建 API 密钥
3. 设置为 `AISA_API_KEY` 或使用引导向导

## 常见问题

### 503 - No available channels 错误
模型 ID 可能不正确或已过时。参考上方的「模型 ID 版本说明」：
- `qwen3-plus` → 使用 `qwen-plus-2025-12-01`
- `qwen3-flash` → 使用 `qwen-mt-flash`

### 模型找不到
确保模型 ID 使用 `aisa/` 前缀：`aisa/qwen3-max`

### Kimi K2.5 "invalid temperature" 错误
Kimi K2.5 只接受 `temperature=1.0`，使用其他值会报错。

### Kimi K2.5 返回空内容
极少数情况下 Kimi K2.5 可能返回空内容但消耗了 token，这通常是暂时性问题，重试即可。

### API 密钥未检测到
1. 检查环境变量：`echo $AISA_API_KEY`
2. 重新运行引导：`openclaw onboard --auth-choice aisa-api-key`

### 无每日请求限制
AIsa 没有每日请求限制（不同于免费版千问门户的每天 2,000 次限制）。
