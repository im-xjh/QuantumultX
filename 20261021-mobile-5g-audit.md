# 中国移动 5G 热点线路复测

日期：2026-10-21，Asia/Shanghai。用户确认切换至中国移动5G热点；本机en0地址由172.22.181.253变为172.20.10.7，Quantumult X TUN仍存在。

## 方法

复用当天Wi-Fi测试的现有服务参数，使用临时Mihomo代理，所有基础节点出站绑定en0，跳过现有TUN业务分流；本地监听仅127.0.0.1。未改动Quantumult X或服务器。域名测试显式指定真实入口IP，避免Fake IP影响。

RackNerd与hankxu实时订阅获取失败，测试复用此前成功验证的节点参数；hankxu入口列表来自当天较早的订阅记录。Argo域名经223.5.5.5的HTTPS解析接口重新查询，返回104.16.231.132与104.16.230.132。

HTTPS目标：Cloudflare trace三次、Google 204一次、Claude trace一次。以HTTP 200/204且curl成功作为通过条件。Claude trace只能验证对应站点网络出口，不代表账号登录、对话或Claude Code完整可用。

## 首轮结果

| 路径 | HTTPS成功次数 |
|---|---|
| Trojan直连 | 0/5 |
| VMess直连 | 0/5 |
| Reality直连 | 0/5 |
| RackNerd-Argo | 0/5 |
| 家宽经Trojan直连 | 0/5 |
| 家宽经VMess直连 | 0/5 |
| 家宽经Reality直连 | 0/5 |
| 家宽经RackNerd-Argo | 0/5 |

日志显示RackNerd代理端口及Argo默认IP连接超时，失败发生在入口连接阶段。VPS的22端口早期曾TCP成功，稍后对22、443、8080、63939进行15秒超时复测全部超时，说明裸IP路径存在变化，不能报告SSH始终可达。

## Argo更换入口后的完整验证

入口A：104.18.33.166；入口B：104.17.99.199。两者直接访问Argo域名的trace均返回Cloudflare香港HKG机房。这里只替换临时客户端的server地址，TLS servername、WebSocket Host、path及认证参数保持原样。

| 路径 | HTTPS成功次数 | Claude trace秒 | Claude出口 |
|---|---|---|---|
| Argo-入口A | 5/5 | 1.148608 | 192.3.80.199 |
| Argo-入口B | 5/5 | 1.121316 | 192.3.80.199 |
| 家宽经Argo-入口A | 5/5 | 2.538966 | 204.252.84.84 |
| 家宽经Argo-入口B | 5/5 | 2.532581 | 204.252.84.84 |

四条路径额外进行1MiB HTTPS下载，人为限速100KiB/s，均持续约10秒并完整接收1048576字节。此项用于短时持续传输检查，不代表带宽速度或长期稳定。

| 路径 | 下载HTTP状态 | 秒 | 接收字节 |
|---|---|---|---|
| Argo-入口A | 200 | 10.131018 | 1048576 |
| Argo-入口B | 200 | 10.250755 | 1048576 |
| 家宽经Argo-入口A | 200 | 10.017857 | 1048576 |
| 家宽经Argo-入口B | 200 | 10.011173 | 1048576 |

## Cloudflare入口与hankxu域名的区别

18个Argo入口TLS探测中，13个返回HTTP200，4个连接超时，1个TLS internal error。其中13个仅证明入口TLS与trace可用；只有上表两个入口另做了完整代理认证和家宽串联验证。

hankxu当天已知的16个入口全部未通过该域名的HTTPS trace检查：14个连接重置，2个连接超时。没有取得当前订阅，未进行这16个节点的VLESS认证测试。

同IP控制实验如下；通过固定IP并只改变TLS域名，排除“所有Cloudflare IP均不可达”的解释。

| 固定IP | TLS域名 | 结果 |
|---|---|---|
| 104.17.99.199 | www.cloudflare.com | HTTP 200 |
| 104.18.33.166 | www.cloudflare.com | HTTP 200 |
| 104.16.231.132 | www.cloudflare.com | 连接超时 |
| 104.17.99.199 | hankxu.ccwu.cc | 连接重置 |
| 104.17.99.199 | districts-federal-iron-implemented.trycloudflare.com | HTTP 200 |

证据提示hankxu存在域名相关的TLS连接重置问题，单纯更换已知入口IP未解决。尚未确认重置来自路径中的具体设备或服务。

## 判断与限制

移动5G下应保留Argo，同时为其设置经过验证的备用入口。当前裸IP直连只在此前Wi-Fi环境验证成功，无法覆盖本轮移动5G场景。hankxu暂不适合作为此次移动5G下的直连备用。

正式配置未修改；新入口只在临时测试客户端生效。未来正式配置应维持Argo域名的SNI/WebSocket Host，单独管理连接入口，并以“中转→家宽→Claude”的完整路径检查可用性。

本轮和此前Wi-Fi样本来自不同时段，短时并发探测只能比较当次可用性。未测试Quantumult X原生加载、长时间流式会话或高带宽。临时进程已关闭，临时配置与凭据已清理。

## Cloudflare 后台与 Pages 核对

同日用户登录Cloudflare后只读检查。当前电脑回到校园网en0地址172.22.181.253，因此本节结果不能替代移动5G验证。

- 代理项目为Cloudflare Pages `xjh-vps`，没有Git连接，当前生产部署ID前缀8960b2c3，后台状态success，部署时间显示2026-04-30 00:39。
- 正式自定义域名只有hankxu.ccwu.cc，绑定状态Active，SSL enabled。
- DNS根域名CNAME指向xjh-vps.pages.dev，Proxied。另有hankxu.hankxu.ccwu.cc CNAME指向同一Pages域名，但未列入Pages自定义域名绑定，实际HTTPS /sub请求返回522。该别名不是当前订阅使用的域名。
- Universal SSL覆盖hankxu.ccwu.cc及*.hankxu.ccwu.cc，状态Active，到期2026-11-23；备用证书已签发，到期2027-01-04。TLS1.3已启用。
- Pages函数绑定KV，命名空间xjh。项目有一个管理相关环境变量，值不记录。

实际通过当前配置中的完整订阅URL获取了16个VLESS节点。订阅包含认证参数，正文与URL不记录。直接把旧订阅URL的域名替换成pages.dev并不返回有效订阅，不能将该替换方式当成可用订阅发布方案；独立节点的认证与订阅URL认证应分别处理。

## Pages默认域名候选测试

复用原订阅中的VLESS认证参数，固定入口104.18.33.166，只修改TLS SNI和WebSocket Host为xjh-vps.pages.dev。通过临时Mihomo、绑定en0测试；未改动正式节点、DNS或Pages配置。

| 路径 | HTTPS检查 | Claude trace秒 | 最终出口 |
|---|---|---|---|
| 原域名 | 5/5 | 0.516063 | 157.230.244.86 |
| Pages默认域名 | 5/5 | 0.482594 | 157.230.244.86 |
| 家宽经原域名 | 5/5 | 2.140407 | 204.252.84.84 |
| 家宽经Pages默认域名 | 5/5 | 2.142652 | 204.252.84.84 |

候选Pages默认域名的VLESS代理与家宽串联在校园网下可用。下一步在移动5G下用同一临时节点验证，可先于购买/新增域名；若成功，再处理正式订阅输出与节点切换。此前新增代理域名的建议应视为候选修复方向，目前仍缺少移动5G验证。

## 移动5G：原域名与Pages默认域名对照验证

用户再次确认切换到中国移动5G热点，en0为172.20.10.7。入口固定104.18.33.166，复用相同VLESS UUID、端口与WebSocket路径，仅更改TLS SNI和WebSocket Host。全程使用临时Mihomo出站绑定en0，正式配置与Cloudflare后台未修改。

| 节点域名 | 路径 | 成功次数 | Claude trace秒 | Claude出口 |
|---|---|---|---|---|
| hankxu.ccwu.cc | 原域名 | 0/5 | 失败 | — |
| xjh-vps.pages.dev | Pages默认域名 | 5/5 | 2.643588 | 157.230.244.86 |
| hankxu.ccwu.cc | 家宽经原域名 | 0/5 | 失败 | — |
| xjh-vps.pages.dev | 家宽经Pages默认域名 | 5/5 | 2.996046 | 204.252.84.84 |

原域名错误为连接重置/SSL_ERROR_SYSCALL及握手超时；Pages默认域名在校园网和移动5G两个样本环境中均通过相同HTTPS请求以及家宽串联。此对照支持将客户端连接域名切换为Pages默认域名作为当前修复方案，但正式切换尚未实施。

持续传输补测：

| 路径 | 下载目标 | 状态 | 秒 | 字节 |
|---|---|---|---|---|
| Pages默认域名 | speed.cloudflare.com | 000 | 0.697870 | 0 |
| 家宽经Pages默认域名 | speed.cloudflare.com | 200 | 10.197466 | 1048576 |
| Pages默认域名 | speed.cloudflare.com | 000 | 1.823908 | 0 |
| Pages默认域名 | www.gstatic.com | 200 | 21.802586 | 44891 |
| 家宽经Pages默认域名 | www.gstatic.com | 200 | 20.457264 | 44891 |

Google静态图片人为限速2KiB/s，直接Pages代理与串联家宽两条路径都完整接收44891字节，持续约20～22秒。家宽路径Cloudflare 1MiB下载限速100KiB/s，约10.2秒完整完成。

Pages代理直接访问speed.cloudflare.com两次均TLS失败；通过家宽访问该目标成功。因此本方案已验证主要测试目标与家宽业务路径，不能宣称全部站点兼容或长期稳定。

正式落地注意：需要同时处理节点TLS SNI、WebSocket Host和订阅发布。旧订阅的token不能直接复制到pages.dev订阅URL；前一节已验证这种替换只返回伪装网页。可以先在现有订阅生成逻辑中输出已验证的pages.dev节点，或另外确认pages.dev适用的订阅认证；移动5G下旧域名订阅本身的可达性仍需解决。

临时代理进程已关闭，临时订阅、UUID、家宽认证及测试配置已删除。


## 正式切换与客户端验证

用户授权后已实施，2026-10-21完成。

- hankxu的Pages项目保持原部署，KV中的节点域名改为xjh-vps.pages.dev；同步重算域名对应的订阅token。订阅使用target=mixed，经现有Quantumult X解析器导入。
- Pages关闭随机入口，从ADD.txt固定生成Pages-CF-A和Pages-CF-B，分别使用104.18.33.166和104.17.99.199。客户端缓存已确认是两个VLESS节点，TLS与WebSocket域名正确。
- RackNerd保留原Argo入口，新增RackNerd-CF-A和RackNerd-CF-B，使用上述两个验证入口。修改现有订阅生成器，Argo主机名刷新时仍会生成这三个节点；现有服务保持运行。
- Pages订阅通过固定DNS入口直接刷新；RackNerd订阅经自建线路刷新，减少对机场的依赖。两个订阅通过系统路径获取均返回HTTP 200。
- 新增“自动兜底”，纳入机场常用地区节点和四个自建入口；“IP中转节点”已选择自动兜底，最终家宽出口保持原配置。

### 隔离故障验证

第一次仅取消机场资源勾选仍保留了缓存节点，日志显示请求经过机场，因此该次结果不作为兜底证明。

随后临时把自动策略限定为一个本地断线节点及四个自建入口，完全排除机场节点。直接通过Quantumult X系统代理访问Claude trace连续5次成功，耗时2.275、2.254、2.254、2.300、2.274秒。客户端请求日志确认实际选择RackNerd-CF-A，五次出口均为204.252.84.84。

验证后已恢复正式配置、删除断线模拟节点、恢复机场资源启用，并把内置PROXY恢复为原来的香港-01。客户端显示IP中转节点选择自动兜底。正式配置最终Claude trace复测成功，出口204.252.84.84。

自动策略依据节点可用性切换；这是当前网络的实际验证，尚未覆盖长期运行和家宽供应商自身故障。

### 回退资料

Mac切换前后配置与KV原始备份保存在`/Users/jhx/.config/quantumultx/backups/20261021-network-cutover/`，其中包含认证信息，不应公开。

RackNerd原订阅生成器和订阅备份位于`/opt/newapi-stack/backups/20261021-qx-proxy-101306/`。

正式文件为`quantumult_20261015195519.conf`，客户端实际文件为`/Users/jhx/Library/Group Containers/group.com.crossutility.quantumult-x/Documents/configuration/default.conf`。最终已逐字比较实际配置与预备的正式配置一致，机场资源启用，临时测试节点不存在。
