# QuantumultX 自用配置目录说明

这个目录用于存放我的 Quantumult X 自用配置、分流规则和阶段性说明文档。

当前目录里的文件可以分成两类：

- 仍在使用的规则与当前主配置
- 不同时间点保存下来的自用配置版本

## 当前在用

如果只看目前仍在实际使用、需要维护的内容，优先关注以下文件：

| 文件                         | 作用             | 说明                                                                               |
| ---------------------------- | ---------------- | ---------------------------------------------------------------------------------- |
| `quantumult_20261015195519.conf` | 当前主配置       | 最新维护入口；保留连接、策略组、规则引用与基础分流。 |
| `academy.list`             | 学术站点分流规则 | GitHub 订阅，内容很小，单独维护更方便。                             |
| `Gmail.list`               | Gmail 分流规则   | GitHub 订阅，用于 Gmail 相关域名强制走代理。                        |
| `GitHub.list`              | GitHub 分流规则  | 覆盖 GitHub 网页、Git 传输、静态资源、Pages 与容器镜像域名。                         |
| `Meta.list`                | Meta 分流规则    | X、Facebook、Instagram 等社交媒体。 |
| `ClaudeAI.list`            | Claude 分流规则  | Claude、Anthropic 与 Persona，由主配置绑定 `美国IP`。 |
| `ChinaDigitalTimes.list`   | 中国数字时代规则 | 中国数字时代及相关站点，使用 `全球加速`。 |
| `MinerU.list`              | MinerU 下载规则  | 结果下载 CDN 的精确直连例外。 |
| `DirectExceptions.list`    | 网站直连例外     | 集中维护零散的网站直连例外。 |
| `OpenCode.list`            | OpenCode 分流规则 | 绑定 `IP中转节点`，已替换原本机 snippet 引用。 |
| `Readymag.list`            | Readymag 分流规则 | 绑定 `中转`，已替换原本机 snippet 引用。 |
| `USPreferred.list` | 美国IP优先 | 国际 AI、Google 登录和搜索共用手动开关。 |

### 当前主配置的结构

`quantumult_20261015195519.conf` 是目前的本地主配置，核心思路见[链式代理](https://github.com/im-xjh/QuantumultX/blob/master/quantumultx-proxy-chain-guideline.md)。文件名日期不代表最近修改日期。策略组 `直连` 是自建代理池，内置策略 `direct` 才表示直接连接。

分流资源通过 HTTPS 订阅。Claude 和 Persona 只用住宅出口。切换 `美国IP优先` 会同时改变国际 AI、Google 登录和搜索的出口。默认选住宅，备用选固定的 RackNerd-CF-A。GitHub、中国数字时代、网盘和一般 Google 流量走全球加速，X 与 Meta 社交流量走国际媒体。

AI 清单的注释记录来源和核对日期。更新时比较上游差异，并通过请求日志核对登录、对话、附件与共享主机。小红书保留原有净化重写。

2026-10-25 已完成 Meta 恢复与业务分流迁移的文件检查，尚未在 Quantumult X 中更新或验证实际命中。备份、批次记录与恢复方式见 [业务规则迁移记录](20261025-business-rules-migration.md)。

同日已读取并处理四份本机分流 snippet：三份迁到云端，腾讯云的重复引用移除；主配置的分流资源已无本机 snippet 引用。原文件保留，软件尚未更新。详见 [本机分流迁移记录](20261025-local-snippets-migration.md)。

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
