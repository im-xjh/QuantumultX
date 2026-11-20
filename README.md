# QuantumultX 自用配置目录说明

这个目录用于存放我的 Quantumult X 自用配置、分流规则和阶段性说明文档。

当前目录里的文件可以分成两类：

- 仍在使用的规则与当前主配置
- 不同时间点保存下来的自用配置版本

## 当前配置

[自用规则目录](rules/)按策略分文件。主配置逐份通过 HTTPS 引用，同一文件内的规则共用一个出口。

| 自用清单 | 内容 | 策略 |
| --- | --- | --- |
| [ClaudePersona.list](rules/ClaudePersona.list) | Claude、Anthropic、Persona | 美国IP |
| [USPreferred.list](rules/USPreferred.list) | 国际 AI（含 Cursor、Perplexity、Poe、Midjourney、Copilot 等）、Google 登录与搜索 | 美国IP优先 |
| [Direct.list](rules/Direct.list) | DeepSeek、MinerU、学术站点和直连例外 | direct |
| [InternationalMedia.list](rules/InternationalMedia.list) | X、Meta 普通社交流量 | 国际媒体 |
| [GlobalProxy.list](rules/GlobalProxy.list) | GitHub、Gmail、中国数字时代 | 全球加速 |
| [OpenCode.list](rules/OpenCode.list) | OpenCode | IP中转节点 |
| [Readymag.list](rules/Readymag.list) | Readymag | 中转 |

`美国IP` 仅包含 `落地IP-美国`，`美国IP优先` 可手选 `美国IP` 或 `直连`。第三方订阅中的 Spotify 走国际媒体，Apple 和哔哩哔哩走 `direct`。

`直连` 是 RackNerd、ccwu 自建代理节点池；`direct` 是设备直接访问。OpenCode 沿用 `IP中转节点`，Readymag 沿用 `中转`。详情见[链式代理说明](quantumultx-proxy-chain-guideline.md)。

## 说明文档

目录里还有两份说明性质的 Markdown 文档：

| 文件                                     | 作用               |
| ---------------------------------------- | ------------------ |
| `20260419note.md`                      | 当前方案说明       |
| `quantumultx-proxy-chain-guideline.md` | 链式代理原理与教程 |

## 历史配置版本

下面这些 `.conf` 文件主要是不同时间点保存下来的自用规则版本，用于回溯、对比和借鉴写法：

| 文件                               | 定位             | 说明                                                                     |
| ---------------------------------- | ---------------- | ------------------------------------------------------------------------ |
| `quantumult_20260409.conf`       | 链式代理初版     | 2026 年 4 月阶段的三池结构配置，保留用于对比。                               |
| `quantumult_20260314161921.conf` | 过渡版本         | 2026 年 3 月阶段的自用配置，可用于和当前版本对比链式代理改造前后的变化。 |
| `quantumult_20250808115326.conf` | 旧版自用配置     | 较早保存的一份自用配置快照，保留当时的策略组和重写结构。                 |
| `墨鱼2025.8.12.conf`             | 墨鱼原始参考配置 | https://ddgksf2013.top/Profile/QuantumultX.conf                          |
