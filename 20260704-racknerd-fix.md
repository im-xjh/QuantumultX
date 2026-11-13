# RackNerd VPS 修复记录（2026-07-04）

## 背景

RackNerd VPS（`192.3.80.199`）之前通过 sing-box-yg 脚本搭建了翻墙节点，使用 Cloudflare Argo 临时隧道暴露服务。临时隧道域名 `being-paths-shadow-deadline.trycloudflare.com` 已过期（NXDOMAIN），导致 QuantumultX 中 RackNerd 订阅完全失效。

第一次修复（改成裸 IP 直连）没有解决问题，又经过两轮排查和尝试，最终确认裸 IP 方案在当前网络环境下不可靠，改回 Cloudflare Argo 隧道并加了自愈机制，验证连接恢复正常。完整过程见下文。

## VPS 基本信息

- IP: `192.3.80.199`
- 系统: Ubuntu 24.04 LTS
- 主机名: `racknerd-c4854d5`
- sing-box 配置路径: `/etc/s-box/sb.json`
- NerdVM 面板: https://nerdvm.racknerd.com/（用户名 `vmuser331187`，面板密码与 root SSH 密码独立）

## SSH 登录

面板密码和 root SSH 密码不同。需要在 NerdVM 面板中执行「Root/Admin Password」重置才能获取 root SSH 密码。重置后获得：

- 用户名: `root`
- SSH 端口: `22`

## VPS 上 sing-box 运行状态

sing-box 通过 systemd 管理，进程正常运行：

```
/etc/s-box/sing-box run -c /etc/s-box/sb.json
```

### 监听端口（当前）

| 端口 | 协议 | 说明 |
|------|------|------|
| 22 | SSH | OpenSSH |
| 8080 | VMess-WS | 已启用 TLS（自签证书），保留作直连备用，**未包含在当前订阅中** |
| 443 | Trojan | TLS，保留作直连备用，**未包含在当前订阅中** |
| 127.0.0.1:8001 | VMess-WS | 无 TLS，仅监听本地回环，专供 Cloudflare Argo 隧道转发使用，不对公网暴露 |
| 63939 | VLESS-Reality | TLS + Reality，SNI: apple.com（QuantumultX 不支持，未使用） |
| 18564 | AnyTLS | TLS（QuantumultX 不支持，未使用） |
| 27611 | Hysteria2 | TLS + QUIC（QuantumultX 不支持，未使用） |
| 31539 | TUIC | TLS + QUIC（QuantumultX 不支持，未使用） |
| 9900 | HTTP | 订阅文件服务（python http.server），systemd 管理 |

另有 `cf-argo.service`（systemd 管理 cloudflared，出站隧道，本机不监听端口）。

### 共用参数

- UUID / password: `99503883-f3a2-4ab9-9732-47f9beda837a`（vmess UUID 与 trojan password 复用同一个值）
- VLESS-Reality private_key: `KKi7Bt_pQebYBR0PAjgQwcVVN2JvISsupM7iEgIdOHo`
- VLESS-Reality public_key: `ZagCcr7ecphvlIGQlvM5t5sdY1f_r2W4fYasCedPEyg`
- VLESS-Reality short_id: `36cc20bf`
- TLS 证书路径: `/etc/s-box/cert.pem`、`/etc/s-box/private.key`（自签名，CN=www.bing.com，有效期到 2126 年，vmess/trojan 共用同一张）

## 已有的分享链接 / 相关文件

VPS 上 `/etc/s-box/` 目录下：

| 文件 | 内容 |
|------|------|
| `vl_reality.txt` | VLESS-Reality 直连（QX 不支持，未使用） |
| `vm_ws.txt` | VMess-WS 直连（旧文件，无 TLS，已弃用） |
| `vm_ws_argols.txt` | 旧 Argo 分享链接，域名早已失效，仅作历史存档 |
| `hy2.txt` / `tuic5.txt` | 对应协议直连（QX 不支持，未使用） |
| `jhsub.txt` | 全部协议汇总（旧） |
| `qxsub.txt` | **当前实际订阅内容**，由 `gen_qxsub.py` 自动生成/覆写，内容是当前 Argo 隧道域名对应的 vmess:// 链接 |
| `argo_current_host.txt` | 记录 cloudflared 当前生成的隧道域名，供 `argo-watch.sh` 判断域名是否变化 |
| `argo-watch.sh` | 包装 cloudflared 的 systemd 启动脚本，监听输出中的新域名并触发订阅重写 |
| `gen_qxsub.py` | 根据域名/UUID/path 生成 vmess:// 链接并写入 `qxsub.txt` |
| `sb.json.bak-*` / `qxsub.txt.bak-*` | 每一步修改前的备份，按时间戳命名 |

## 第一次尝试：裸 IP 直连（已确认失败）

### 方案选择（当时的判断）

- **Cloudflare Argo 临时隧道**：域名会变，需保活，不适合长期使用
- **直连 VPS IP**：最简单可靠，VMess-WS 端口 8080 可直接连接
- **QuantumultX 不支持 VLESS-Reality 协议**，因此选择 VMess-WS 直连

### 具体操作

在 VPS 上搭建 HTTP 订阅服务（`qxsub.service`，监听 9900），内容为不带 TLS 的 vmess:// URI（`tls` 字段为空），只改了 QuantumultX 配置里 RackNerd 的订阅 URL 一行。

### 排查结论

VPS 侧服务、端口、订阅本身全部正常（外部 curl/nc 反复验证无误），且确认 VPS 没有任何操作系统级防火墙（未装 ufw，iptables 三条链策略均为 ACCEPT 且无规则），NerdVM 面板本身也不提供服务器级防火墙功能——问题不在"漏开端口"。

登录 VPS 看 sing-box 日志后发现：真实连接（手机公网 IP 发起）建立后很快收到 `EOF` 或握手阶段的 `bad "Sec-WebSocket-Key" header`（说明请求在传输途中被中间设备篡改），只有 QuantumultX 内置测速用的极小请求（连到 `www.gstatic.com:80`）能成功。判断是国内网络对**明文、无 TLS 的 vmess-ws** 识别率极高，直接干扰/阻断——这是该方案失败的根本原因，而不是订阅或端口配置的问题。

## 第二次尝试：TLS 化 + Trojan（有缓解，仍不稳定，已放弃）

1. 给 8080 端口的 vmess-ws 入站启用 TLS（复用已有自签证书），订阅同步更新为 `tls=tls`。
2. 效果：比明文好很多，但仍不稳定——日志显示相当比例的真实连接在建立后 **5~7 秒左右**收到 `EOF`，且和目标网站无关（`check-host.net`、`1.1.1.1`、`api.github.com` 等各种网站都出现过成功和失败两种情况）。这个"允许连接建立、跑几秒再掐断"的模式符合国内 DPI 对 vmess 协议做流量特征识别（而非单纯端口/IP 封锁）——vmess 自身的帧结构即使套了 TLS，在包长分布和时序上仍有一定辨识度。
3. 因此追加部署了 Trojan（443 端口，专门设计用来对抗这类特征识别，认证后就是裸传输，没有 vmess 那种额外帧结构）。
4. 实测结果：vmess+TLS 和 Trojan **两个节点均无法稳定连接**。

结论：在当前网络路径下，直连这台 VPS 的裸 IP，无论套什么协议/加不加 TLS，都无法稳定使用。具体是这个 IP 本身被针对性干扰，还是国内出口对该数据中心/IP 段整体不友好，未能完全查证，但现象很一致，不建议继续在裸 IP 方向排查。

调试期间还有一次插曲：VPS 一度整体失联（SSH 和订阅端口 9900 同时出现"三次握手成功、应用层无响应/连接被重置"的现象），持续约十几分钟后自行恢复，原因未完全确认（怀疑是短时间内高频重连触发了上游异常流量检测），但不影响上面的结论。

## 最终方案：恢复 Cloudflare Argo 隧道 + 自愈脚本（当前生效）

放弃裸 IP 方向，改回最初的 Cloudflare Argo 隧道思路——客户端连接的是 Cloudflare 边缘节点（真实证书、真实 IP，Cloudflare 体量巨大，国内没有整体封锁的先例），而不是这台 VPS 的 IP，从根源上避开裸 IP 被针对性干扰的问题。

### 架构

```
QuantumultX --(HTTPS/443, 域名走 Cloudflare)--> Cloudflare 边缘
                                                     |
                                              cloudflared（VPS 上，出站连接，不监听端口）
                                                     |
                                     127.0.0.1:8001 vmess-ws（无 TLS，本地回环）
```

- 新增了一个只监听 `127.0.0.1:8001` 的 vmess 入站（`tag: vmess-argo`），不加 TLS（Argo 隧道本身已经是加密的），且不对公网暴露，只有 cloudflared 能连到。
- `cloudflared tunnel --url http://localhost:8001` 通过免费的临时隧道（不挂 Cloudflare 账号）把这个本地端口暴露到 `*.trycloudflare.com`。

### 解决"域名会变"的老问题：自愈脚本

最初就是因为临时隧道域名过期没人发现导致订阅失效。这次没有回避这个问题，而是自动化掉：

- `/etc/s-box/argo-watch.sh`：systemd 的 `ExecStart` 实际跑的是这个脚本，它启动 cloudflared 并实时读取其输出。
- 一旦检测到新的 `*.trycloudflare.com` 域名（每次 cloudflared 重启都会拿到一个新的随机域名），立即调用 `gen_qxsub.py` 重新生成 vmess:// 链接并覆写 `/etc/s-box/qxsub.txt`，同时把当前域名记录到 `argo_current_host.txt`。
- systemd 服务 `cf-argo.service` 配置了 `Restart=always`，进程崩溃/VPS 重启都会自动拉起，域名变化会在几秒内自动同步进订阅，不需要人工介入。
- 已实测验证：手动重启 `cf-argo.service` 后，新域名确实自动写入了 `qxsub.txt`，无需任何人工操作。

### 节点命名

新节点的 `ps`（节点名）沿用了原来的 `vm-argo-racknerd-c4854d5`，这样 QuantumultX 配置里 `[policy]` 下 `美国IP` 策略组（`static=美国IP, 落地IP-美国, vm-argo-racknerd-c4854d5`）对这个节点名的引用不用改，链式代理和强制走"美国IP"的 AI/Google 相关规则也一并恢复。

### 当前订阅内容

订阅地址不变：`http://192.3.80.199:9900/qxsub.txt`，内容为单个 vmess:// 链接（Argo 隧道域名 + 443 + tls）。原本的裸 IP vmess（8080/TLS）和 Trojan（443）已从订阅里移除（避免 QX 按延迟自动选中一个不稳定的节点），但配置本身还留在 `sb.json` 里，需要的话随时可以加回订阅。

**用户已实测确认连接恢复正常。**

## 踩坑记录

### 1. NerdVM 面板密码 ≠ root SSH 密码

面板密码只能登录 NerdVM Web 面板，不能用于 SSH（密码本身不记录在此文档中）。必须在面板中重置 Root Password 才能获得 SSH 密码。

### 2. QuantumultX 不支持 VLESS-Reality

尝试在 `[server_local]` 中手写 `vless=` 行会报语法错误。Reality 协议需要专门的客户端支持，QuantumultX 目前不支持。

### 3. QuantumultX vmess 行内格式容易出错

在 `[server_local]` 中手写 `vmess=...` 行，`method=auto` 等参数会导致语法错误。更可靠的方式是使用远程订阅 + `opt-parser=true`，让 resource_parser 自动转换 vmess:// URI。resource_parser 默认 `tls-verification=false`（除非订阅 URL 带 `#cert=1`），自签证书不需要额外参数就能被接受。

### 4. systemd 端口冲突

首次部署时用 `nohup` 启动了 Python HTTP 服务，之后改为 systemd 管理时因端口占用导致 crash-loop（`Address already in use`）。解决：先 `fuser -k 9900/tcp` 杀掉残留进程，再启动 systemd 服务。

### 5. 不应改动无关配置

修改过程中不小心改动了花云 token、直连 regex、美国IP 策略组等无关项，导致配置出错。正确做法：只改目标行，其他保持原样。

### 6. 裸 IP + 任何协议在当前网络下都不可靠

即使加了 TLS、甚至换成专门抗特征识别的 Trojan，从当前网络路径访问这台 VPS 的裸 IP 仍会被间歇性掐断（日志证据：连接建立后 5~7 秒左右收到 EOF，和目标网站无关）。符合主动流量特征识别/概率性阻断的特征，而非简单端口封锁。裸 IP 方案判定不可行，只作为本地调试/备用配置保留，不建议作为主力线路。

### 7. `pkill -f` 要避免自我匹配

执行 `pkill -f 'cloudflared tunnel'` 时，如果发起这条命令的 shell 命令行本身包含相同的字符串（比如通过 SSH 把整条命令当参数原样传递过去的情况），会连同发起命令的这个 SSH 会话一起杀掉。应改用更精确的匹配（比如绝对路径 `/etc/s-box/cloudflared`），或者先 `ps aux` 确认目标 PID 再精确 kill。

### 8. cloudflared 申请临时隧道不是总能秒级成功

历史日志里有一次 `context deadline exceeded` 的注册超时失败记录。这次重试就成功了，说明这类失败可能是偶发的（网络抖动或 Cloudflare 侧临时问题），遇到隧道注册失败应该先重试几次，不必立刻怀疑架构或环境有问题。

## 当前状态

- VPS 端口 9900 订阅服务正常运行（systemd 管理，开机自启）
- Cloudflare Argo 隧道正常运行（`cf-argo.service`，systemd 管理，崩溃/重启自动恢复并自愈订阅）
- QuantumultX 订阅内容为 Argo 隧道节点，**已实测连接恢复正常**
- 裸 IP 的 vmess-TLS（8080）和 Trojan（443）保留在 VPS 配置中作为备用，未包含在当前订阅

## 如果以后又出问题，排查方向

1. **订阅刷新失败或内容为空**：SSH 上去看 `systemctl status cf-argo`，以及 `cat /etc/s-box/qxsub.txt` 和 `/etc/s-box/argo_current_host.txt` 是否一致；再看 `journalctl -u cf-argo -n 50` 里最近一次生成的域名，确认自愈脚本是否正常工作。
2. **订阅正常但节点连不上**：先用 `curl -I https://<argo_current_host.txt 里的域名>/` 确认 Cloudflare 边缘本身能不能连通；如果连不通，大概率是这台 VPS 的出站到 Cloudflare 或者 cloudflared 进程本身的问题，而不是国内网络的问题。
3. **cloudflared 反复重启导致域名频繁变化**：查 `journalctl -u cf-argo` 里是否有连接错误；也可能是本地 8001 端口的 vmess-argo 入站配置或 sing-box 本身出了问题（`systemctl status sing-box`）。
4. **想要更稳定、域名永久不变的方案**：见下面"未来计划"。

## 未来计划：绑定自有域名的固定隧道

当前方案用的是不挂 Cloudflare 账号的免费临时隧道，域名是 cloudflared 每次启动随机生成的 `*.trycloudflare.com`。虽然现在有自愈脚本兜底，域名变化不会再导致订阅失效，但这类临时隧道本质上仍是 Cloudflare 官方声明"no uptime guarantee"的服务。如果想要域名永久固定、不再依赖"重启后自动重新生成"这层兜底，需要：

1. 准备一个域名，把它的 DNS 托管迁移到 Cloudflare（免费版即可）。
2. 在 VPS 上执行 `cloudflared tunnel login`（会给一个链接，在浏览器里用 Cloudflare 账号授权），然后 `cloudflared tunnel create <随便起个名字>`，会生成一个隧道 ID 和一份凭证文件（保存在 `~/.cloudflared/`）。
3. 执行 `cloudflared tunnel route dns <隧道名> <子域名>`（比如 `vpn.你的域名.com`），把这个子域名指向刚创建的隧道。
4. 写一份 `~/.cloudflared/config.yml`，内容大致是：
   ```yaml
   tunnel: <隧道ID>
   credentials-file: /root/.cloudflared/<隧道ID>.json
   ingress:
     - hostname: vpn.你的域名.com
       service: http://localhost:8001
     - service: http_status:404
   ```
5. 把 `cf-argo.service` 的 `ExecStart` 从 `/bin/bash /etc/s-box/argo-watch.sh` 换成 `/etc/s-box/cloudflared tunnel run <隧道名>`（域名固定了，不再需要监听输出解析域名这层自愈逻辑，`argo-watch.sh`/`gen_qxsub.py` 可以停用）。
6. 手动生成一次 vmess:// 分享链接（host/sni 都填 `vpn.你的域名.com`，端口 443），写入 `qxsub.txt`，之后除非主动改动，不需要再变。

好处：域名永久不变，比免费临时隧道更符合 Cloudflare 官方支持的用法。唯一前提是需要一个域名——如果手上已有域名（哪怕是别的用途），匀出一个子域名给这个隧道用就行，不需要整个域名专门用于此事。
