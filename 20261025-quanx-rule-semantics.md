# Quantumult X 规则语义核对

核对日期：2026-10-25。仅检查公开一手资料，未读取节点凭据，未修改配置或规则。

## 已确认

- `force-policy` 会覆盖远程规则各行原有的策略。因此，远程 Meta.list 内写 `Meta`，而引用处明确指定 `force-policy=美国IP`，不能单凭 `Meta` 策略组不存在就断言该远程引用会报错。相同规则直接放入本地时没有这层覆盖。官方原文："the policy in filter of remote resource will be ignored"。[官方 sample.conf](https://github.com/crossutility/Quantumult-X/blob/master/sample.conf)
- 官方原生示例采用 `host`、`host-suffix`、`host-keyword`、`host-wildcard`、`ip-cidr`、`ip6-cidr`、`geoip` 等名称。原生远程规则示例没有节标题，每行保留策略字段，例如 `host-suffix, instagram.com, proxy`。本次未找到官方材料明确允许省略策略字段；迁移时保留第三列 `proxy`，由引用处的 `force-policy` 绑定实际策略，是与官方示例一致的方案。[官方 filter.snippet](https://github.com/crossutility/Quantumult-X/blob/master/filter.snippet)
- 官方示例支持规则行附加 `via-interface=pdp_ip0`。资源解析器通过 `$resource.link` 取得完整资源路径，再输出修改后的原生文本；URL fragment 可用于脚本自定义参数。因而 `#via=%TUN%` 的具体处理必须追到当前解析器实现，不能将其视为原生列表的自足配置。[官方 sample.conf](https://github.com/crossutility/Quantumult-X/blob/master/sample.conf)、[官方 resource-parser.js](https://github.com/crossutility/Quantumult-X/blob/master/resource-parser.js)
- Quantumult X 存在规则类型优先级。官方 README 明确 User-Agent 的优先级低于 Host。不能把整个引擎概括为“按文本从上到下，第一条命中即结束”。[官方 README](https://github.com/crossutility/Quantumult-X/blob/master/README.md)

## 插入资源与匹配顺序的证据边界

官方 sample.conf 使用 `inserted-resource=true`，但未解释 true/false 的完整排序算法。官方仓库 Issue #251 的提交者报告，本地 `host-keyword, ., proxy` 会盖住远程规则，给远程引用加 `inserted-resource=true` 后解决；截至核对时，该 issue 没有维护者回复。这是一手用户报告，证明了现实迁移风险，不能升级为维护者确认的完整语义规范。[官方示例](https://github.com/crossutility/Quantumult-X/blob/master/sample.conf)、[Issue #251](https://github.com/crossutility/Quantumult-X/issues/251)

Quantumult X News 在 2022-05-31 的公告说明，关闭“分流匹配优化”后，host 相关规则可按顺序匹配；开启时，先按类型优先级，再按同类规则顺序，举例为 host > host-suffix > host-keyword。该资料补充了设置依赖，当前设备开关状态仍需要在 App 中核对。[Quantumult X News 公告所在页](https://t.me/s/quanxnews?before=432)

## 本次没有取得充分官方证据的部分

- `inserted-resource=false` 的完整顺序，多个插入资源之间的顺序，以及不同类型规则跨资源的排序细节。
- `host-suffix` 的边界匹配细节、`DOMAIN`/`DOMAIN-SUFFIX` 的原生兼容性、`no-resolve` 对每种 IP 规则的准确影响。原生示例没有给出后两类语法，不能仅据示例缺失断言绝对不支持。
- `%TUN%` 特殊接口值的官方定义，远程原生行携带该值的实机行为，以及开启 `force-policy` 时，解析器前后的未定义策略校验顺序。

## 对整理方案的直接约束

迁移域名列表时使用官方原生格式和明确的策略占位；每个引用处绑定现有策略组。旧本地规则改为远程资源后，要验证它们与其他资源、本地例外的覆盖关系。首轮保持第三方资源的顺序、解析器开关及 URL 参数；尤其包含 `#via=%TUN%` 的资源，不能仅为精简而关闭解析器。IP/CIDR、GEOIP、最终规则与网络引导例外保留在原位，减少同时变更的语义。Meta 恢复应仅保留一份域名列表，以现存策略组绑定，并由 App 导入检查和实际命中日志验收。
