# Call-Use PRD v1

## 1. 产品定义

### 一句话

**Call-Use 是给 agent 用的电话执行层。**

### 更完整一点

像 browser-use 让 agent 会用网页、computer-use 让 agent 会操作电脑一样，**Call-Use 让 agent 会打电话办事**。

它不是一个具体业务 agent。
它不直接做退款、预订、保险、催收这些上层 application。
它做的是一层**标准化电话执行基础设施**，让上层 agent 可以方便地构建各种基于电话的 application agent。

---

## 2. 产品定位

### 我们是什么

Call-Use 是一个：

* phone-use runtime
* call execution layer
* 给 agent 的电话基础设施
* 可插拔、可集成、可扩展的执行模块

### 我们不是什么

Call-Use 不是：

* 通用 AI 助手
* 某个退款产品
* 某个预订产品
* 企业客服系统
* 传统呼叫中心软件
* 单纯 telephony API wrapper

### 核心位置

在整个 agent stack 里，Call-Use 位于：

* 上层：Claude Code / OpenClaw / 各类 orchestrator / application agent
* 中层：Call-Use
* 下层：Telephony / voice / speech / provider

也就是说：

**上层决定"为什么打、打给谁、目标是什么"；Call-Use 负责"把电话执行掉"。**

---

## 3. 愿景

### 长期愿景

未来如果是 agent 的世界，agent 必须具备三类现实执行能力：

* web-use
* computer-use
* call-use

Call-Use 的目标，是成为这三者中的：

**电话执行标准层。**

### 中期愿景

让任何上层 agent 都能低成本获得：

* 拨号能力
* 电话流程执行能力
* 语音交互能力
* 人工接管能力
* 电话结果回传能力

### 短期愿景

先把 Call-Use 做成一个**开源、易集成、抽象清晰、对 application agent builder 非常顺手**的电话执行 runtime。

---

## 4. 问题定义

### 当前问题

现在 agent 越来越会：

* 浏览网页
* 操作电脑
* 调工具
* 读写文件
* 搜邮箱

但大量真实世界任务依然会卡在一个地方：

**电话。**

例如：

* 退款必须打电话
* 取消服务必须打电话
* 预约、改期、确认必须打电话
* 跟客服追 case number 必须打电话
* 复杂流程需要电话确认

### 本质问题

不是没有 telephony，也不是没有 voice model。
问题是：

**电话世界还没有被很好地抽象成 agent 可调用的标准执行层。**

今天的上层 agent 要想"会打电话"，通常要自己面对：

* 拨号
* 音频流
* IVR
* DTMF
* hold
* transfer
* 语音输入输出
* 人工接管
* transcript
* outcome extraction

这对大多数 application agent builder 来说太重了。

---

## 5. 产品目标

## 核心目标

让上层非常方便地构建各种**基于电话的 application agent**。

### 具体目标

1. 提供统一的电话执行抽象
2. 让上层无需理解 telephony 细节
3. 支持多种接入方式
4. 支持本地 agent 与云端 agent
5. 支持人机协作和安全边界
6. 成为 agent 生态中的标准组件

### 非目标

1. 不内置垂直业务逻辑
2. 不做最终 consumer product
3. 不一开始追求重商业化
4. 不绑定单一模型或单一电话供应商

---

## 6. 目标用户

### 第一层用户：开发者 / agent builder

这是最核心的用户。

包括：

* Claude Code 用户
* OpenClaw 用户
* 本地 agent 开发者
* workflow / orchestrator 开发者
* AI infra 团队
* 各种 application agent builder

他们的核心诉求不是"我要一个会打电话的 app"，而是：

**"我已经有一个 agent，我想让它会打电话。"**

### 第二层用户：上层产品团队

这些团队可能在做：

* refund agent
* booking agent
* cancellation agent
* insurance follow-up agent
* customer service automation agent
* productivity agent

他们未必想自己做 call runtime，但想快速获得电话能力。

### 最终用户

最终用户不会直接理解 Call-Use。
他们只会感知到：

**"我的 AI 现在不仅会网页和电脑，也会打电话办事。"**

---

## 7. 核心价值主张

### 对开发者

**让 agent 获得电话能力，像获得网页能力一样简单。**

### 对上层应用

**极大降低构建电话类 application agent 的复杂度。**

### 对最终用户

**把必须自己打的电话，变成 AI 可以替你执行的流程。**

### 对生态

**把电话世界标准化为 agent 基础设施的一部分。**

---

## 8. 核心能力

Call-Use 的能力不应该围绕某个业务场景组织，而应该围绕电话执行本身组织。

## A. Call Session

负责电话基本生命周期：

* 发起电话
* 接听电话
* 结束电话
* 转接电话
* 插入人工
* 管理通话状态

## B. Call Navigation

负责电话流程推进：

* 识别 IVR
* 发送 DTMF 按键
* 检测 hold
* 检测 voicemail
* 识别 transfer

## C. Realtime Voice

负责电话中的实时交互：

* 听对方说话
* 说出 agent 回复
* 实时打断与切换
* transcript 流式输出

## D. Voice Identity

负责声音形态：

* 默认 agent voice
* cloned user voice
* branded assistant voice
* 可按任务或场景切换

## E. Human Handoff

负责关键节点的人机协作：

* OTP
* 本人确认
* 敏感披露
* 金额选择
* 部分退款 / 变更条件确认
* 一键接入用户本人

## F. Structured Outcome

负责把电话结果变成标准结果：

* transcript
* case number
* outcome
* ETA
* next step
* follow-up signal

---

## 9. 产品边界

### 我们负责什么

* 电话执行
* 通话控制
* 电话流程抽象
* 事件流
* 审批与 handoff 机制
* 结果结构化输出
* 对上层 agent 的标准接口

### 我们不负责什么

* 不决定业务策略
* 不自动拥有全部用户上下文权限
* 不替 application agent 写业务脑
* 不构建所有垂直场景模板
* 不做"万能 AI 助手"

---

## 10. 产品形态

Call-Use 必须是一个**多接口兼容**的 runtime，不能只有一种接入方式。

### 支持的接入形态

* CLI
* MCP
* Skill
* SDK
* API / WebSocket / event stream

### 为什么必须多接口

因为上层 agent 生态本身就是分裂的：

* 有人用 Claude Code
* 有人用 OpenClaw
* 有人喜欢 MCP
* 有人喜欢 SDK
* 有人只想接 API
* 有人需要 CLI 本地化 workflow

如果只支持一种接入方式，Call-Use 很难成为标准基础设施。

---

## 11. 统一抽象模型

不管是 CLI、MCP、Skill 还是 SDK/API，底层都应该基于同一套抽象对象。

### 核心对象

* **Task**：这通电话任务是什么
* **State**：当前执行到哪里
* **Event**：过程中发生了什么
* **Approval**：哪些节点需要人工决策
* **Outcome**：最终结果是什么

### 设计原则

* 同一套语义
* 不让上层碰 telephony 细节
* 不同接口只是不同包装，不是不同逻辑

---

## 12. 使用方式

### 上层 agent 的典型使用方式

上层 agent 只需要做四件事：

1. 创建电话任务
2. 启动电话任务
3. 监听事件流
4. 在需要时提交审批
5. 获取最终结果

### 上层的视角

上层不应该看到：

* SIP
* audio frames
* raw telephony logic

上层应该只看到：

* start
* observe
* approve
* join human
* outcome

这才是真正的"phone-use"抽象。

---

## 13. MVP 范围

第一版不要做大，重点是把抽象做对。

### MVP 必须有

1. 发起电话
2. IVR / DTMF
3. 基础实时通话
4. transcript / event stream
5. approval pause / resume
6. structured outcome
7. CLI 接入
8. SDK/API 接入
9. MCP 或 Skill 至少有一种正式接入
10. Claude Code / OpenClaw 至少一个官方 adapter

### MVP 不必有

* 复杂 dashboard
* 企业 admin
* 全行业模板
* 重度 analytics
* 大规模托管平台能力
* 复杂 billing

---

## 14. 成功标准

### 对开发者

* 10 分钟理解产品
* 30 分钟接入基本 demo
* 1 小时跑通第一通真实任务电话

### 对上层 agent

* 很容易集成
* 很容易监听电话状态
* 很容易插入审批与人工接管
* 很容易拿到结构化结果

### 对生态

* 容易写 adapter
* 容易写 skill
* 容易和 browser/computer-use 组合
* 逐渐形成"agent 打电话就用 Call-Use"的心智

---

## 15. 核心差异化

### 不是普通 telephony API

Telephony API 解决的是"怎么接电话网络"。
Call-Use 解决的是"怎么让 agent 使用电话世界"。

### 不是普通 voice assistant 平台

voice assistant 平台往往卖的是一个完整语音产品。
Call-Use 卖的是一个**给任意 agent 用的执行层**。

### 不是垂直场景产品

退款、预约、保险都可以建立在 Call-Use 之上，但 Call-Use 本身不等于这些产品。

### 核心差异

**Call-Use 的真正差异化，是 agent-facing 的电话抽象层。**

---

## 16. 竞品视角下的位置

### 上层产品

* Pine
* DoNotPay

这些证明需求存在，但它们是上层产品，不是你们的位置。

### 底层能力

* LiveKit
* Twilio
* 各类 speech/voice providers

这些解决能力来源，但不是最终抽象层。

### 相邻平台

* Vapi
* Retell
* 其他 voice platform

这些更像完整 voice 平台，与你们部分重叠，但你们如果坚持"agent 的 call-use runtime"定位，会更清晰。

### 真正对标逻辑

* browser-use
* computer-use

这是最像你们该占的抽象层位置。

---

## 17. 开源策略

既然当前第一目标不是商业化，而是成为 top 开源项目，那么：

### 开源优先原则

1. 抽象清晰
2. README 一眼看懂
3. 上手快
4. 本地可跑
5. 默认 BYO
6. 易于做 adapter
7. 易于与现有 agent 生态组合

### 开源阶段不追求

* 重付费逻辑
* 重企业功能
* 大而全 SaaS
* 复杂套餐设计

### 第一目标

形成心智：
**Call-Use = 电话版 browser-use / computer-use**

---

## 18. 长期发展路径

### Phase 1

做成最清楚的开源 runtime：

* 核心抽象
* 核心接口
* 基础 demo
* Claude/OpenClaw 接入

### Phase 2

形成生态：

* adapters
* skills
* templates
* examples
* community integrations

### Phase 3

形成标准：

* 统一 task schema
* 统一 event schema
* 统一 approval model
* 成为 agent 电话执行事实标准

### Phase 4

再考虑：

* 托管
* 云服务
* 企业版
* 管理与计费

---

## 19. 最大风险

### 风险 1：做成"又一个 voice app"

会失去基础设施定位。

### 风险 2：做成 telephony wrapper

会失去产品层价值。

### 风险 3：接口太重

会失去开发者 adoption。

### 风险 4：边界不清

如果同时做上层场景和底层 runtime，会导致定位混乱。

### 风险 5：过早商业化

会牺牲开源增长和生态势能。

---

## 20. 最终产品定义

**Call-Use 是一个面向 agent 的电话执行基础设施。**
**它把拨号、通话、IVR、DTMF、voice identity、human handoff 和 outcome extraction 抽象成统一的 phone-use runtime，让 Claude Code、OpenClaw 和其他 application agent 即插即用地获得"打电话办事"的能力。**
