# 本机分流 snippet 迁移记录

执行日期：2026-10-25，Asia/Shanghai。

已读取四份原始分流 snippet，逐批核对、发布、验证后处理主配置。四份本机分流引用已全部清理，Quantumult X 软件未更新，原始 snippet 文件保留未动。

## 原件与备份

四份原件位于 `/Users/jhx/Library/Mobile Documents/iCloud~com~crossutility~quantumult-x/Documents/Profiles/`。

本轮备份目录：`/Users/jhx/Library/Application Support/QuantumultX-backups/20261025-150841-snippets`。

`baseline/` 保存本轮开始时的最新主配置与 README，`baseline/snippets/` 保存四份原件。`manifest.json` 记录源路径与 SHA-256，所有副本通过哈希核对。`stages/` 保存每批完成后的配置快照、迁移后的规则和检查记录。原件与备份的哈希在最终检查时再次核对通过。

## 逐批结果

| 批次 | 原文件与实际规则 | 处理结果 |
| --- | --- | --- |
| 01 腾讯云 | `0B1B58F10465.snippet`：`81.70.21.43/32` 直连，共 1 条 | 主配置的基础本地规则已包含完全等价的 IP 直连规则；删除重复 snippet 引用，基础规则保留，无需增加云端副本 |
| 02 OpenCode | `633A34E0CD0A.snippet`：`opencode.ai` 后缀，共 1 条 | 迁入 `OpenCode.list`，继续绑定 `IP中转节点` 并启用 |
| 03 Readymag | `A971A15CB322.snippet`：`readymag.com` 后缀，共 1 条 | 迁入 `Readymag.list`，继续绑定 `中转` 并启用 |
| 04 小红书 | `8D02B1E1ADF7.snippet`：`xiaohongshu` 与 `rednote` 关键词，共 2 条 | 迁入 `Xiaohongshu.list`，继续绑定 `美国IP`，保持停用 |

三份迁移后的列表采用原生规则语法与内置 `proxy` 占位，实际策略仍由主配置中的 `force-policy` 绑定。原规则类型与策略字段的大小写、分隔空格做了规范化，匹配条件保持一致。读取到的内容均为上述分流规则，未含凭据或脚本。

每份列表先发布并读取确认远端内容完全一致，再替换主配置中对应的文件路径。替换保留原引用的位置、tag、策略、更新间隔、解析器开关和启用状态；没有增加接口参数或插入资源参数。

## 发布记录

| 云端规则 | 提交 |
| --- | --- |
| [OpenCode.list](https://github.com/im-xjh/QuantumultX/blob/master/OpenCode.list) | [`ad44a9f`](https://github.com/im-xjh/QuantumultX/commit/ad44a9f72d5f980476bd1803a58ae31eb70fd037) |
| [Readymag.list](https://github.com/im-xjh/QuantumultX/blob/master/Readymag.list) | [`e6726cb`](https://github.com/im-xjh/QuantumultX/commit/e6726cbb817e320e90602fb91c72807afef0b5fe) |
| [Xiaohongshu.list](https://github.com/im-xjh/QuantumultX/blob/master/Xiaohongshu.list) | [`2e3d3e5`](https://github.com/im-xjh/QuantumultX/commit/2e3d3e5619aca824c17c561b38a0639afc797cfb) |

三次提交均只包含对应的新规则文件。主配置与本轮说明修改保存在本地。

## 最终文件检查

本轮主配置的允许改动集合为三处引用 URL 替换和一行腾讯云重复引用删除，整份文件与这一预期完全一致。

- 远程分流资源由 29 项变为 28 项，其中 1 项继续停用。
- `filter_remote` 中本机 `.snippet` 引用数量为 0。
- 剩余 13 条本地基础分流保持原样。
- 除 `filter_remote` 外，所有配置节与本轮基线逐字节一致，涵盖节点、订阅、DNS、策略、重写、MITM。
- 三份列表的匹配条件与原件一致，强制策略均存在，启用状态保持一致。
- 原始四份 snippet 的内容未变；无需通过软件导出或刷新完成本轮操作。

执行前主配置 SHA-256：`d694b5acfd0c0e3e8860223dc6e6a80fb1ccebb3fc2a5eb52c47d572417b52e6`。

执行后主配置 SHA-256：`1395a8f9beaeb5da9f0e84dc0c04c95a4c2f3d2ff5a4d86646f9f94559b09597`。

## 恢复与后续验收

恢复本轮改动时，先另存当前配置，再以本轮备份中的 `baseline/quantumult_20261015195519.conf` 覆盖本地主配置。原始 snippet 文件仍在原路径，旧引用可继续使用。新建的三个云端列表没有改变旧配置依赖的资源，可以保留。

本轮通过文件与远端内容检查。软件内资源加载、实际匹配与出口尚未验证；后续更新时分别检查 OpenCode、Readymag，并确认小红书仍停用，同时回归腾讯云 SSH。软件内更新继续等待用户指令。
