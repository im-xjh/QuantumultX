# 2026-05-09 VPS + QuanX 移动流量测试卡点记录

本文记录本轮 RackNerd VPS、sing-box-yg、Quantumult X、青海移动流量测试过程中遇到的主要卡点。目标是作为本地存档，方便后续继续排查或改成固定 Argo/CDN 方案。

## 1. 单条节点链接不能当作订阅链接导入

最开始拿到的是 `vmess://...` 单条节点 URI。这个链接不能直接填到 QuanX 的“资源 - 节点 - 资源路径”里。

原因：

- QuanX 的“资源路径”期望的是 `https://...txt` 这种远程订阅文件。
- 把 `vmess://...` 填进去时，QuanX 会把它当成远程文件地址读取，所以报“该文件不存在”。
- 如果走“手动添加节点”页面，但页面默认协议是 `shadowsocks`，就会出现要求填写“加密方法 / 密码”的情况。这不是 VMess 节点缺字段，而是入口协议选错。

后续处理：

- 为了便于 QuanX 导入，在 VPS 上临时开了只读 HTTP 订阅文件服务。
- 对外订阅通过临时 Cloudflare Tunnel 暴露，例如：
  `https://being-paths-shadow-deadline.trycloudflare.com/vmess-argo.txt`
- QuanX 中应填 `https://...txt` 订阅链接，而不是单条 `vmess://...`。

## 2. 临时 Argo 域名会失效，不能手动随便固定

测试中出现过 `grade-wiley-permitted-pick.trycloudflare.com` 在任何网络环境下都无法访问的情况。

排查结果：

- 该域名曾经是有效的 Cloudflare quick tunnel 域名。
- 但 VPS 上对应的 `cloudflared tunnel --url http://localhost:8080` 进程已经退出。
- Cloudflare 返回 `404` 或无法正常代理，说明请求没有落到当前 VPS 的 VMess-WS 入站。

关键结论：

- `trycloudflare.com` 是临时 Argo 域名，不是长期固定入口。
- 手动把 VMess 节点的 `host` / `sni` 改成某个 `trycloudflare.com` 域名没有意义，除非 VPS 上正运行着对应的 cloudflared 隧道。
- 临时 Argo 适合短期测试，不适合作为稳定生产方案。

后续处理：

- 重启 VMess-Argo 对应的 cloudflared 隧道。
- 获取新的有效域名，例如：
  `norfolk-liabilities-sheets-strikes.trycloudflare.com`
- 同步更新 `vmess-argo.txt` 订阅文件中的 `host` 和 `sni`。

## 3. 订阅服务和代理服务是两个不同的 Argo 隧道

本轮测试中实际存在两类 Cloudflare Tunnel：

1. 订阅文件隧道
   - 指向本地 `127.0.0.1:18081`
   - 用于给 QuanX 提供 `.txt` 订阅文件
   - 例如 `being-paths-shadow-deadline.trycloudflare.com`

2. VMess-WS 代理隧道
   - 指向本地 `localhost:8080`
   - 用于 VMess-WS + Argo/CDN 节点本身
   - 例如后续生成的 `norfolk-liabilities-sheets-strikes.trycloudflare.com`

容易混淆的点：

- 能打开订阅链接，只能说明“订阅文件隧道”可用。
- 订阅能打开，不代表“VMess 代理隧道”也可用。
- VMess 节点里的 `host` / `sni` 必须对应代理隧道，而不是订阅隧道。

## 4. 浏览器打不开 Argo 节点域名不一定代表节点不可用

VMess-WS 的 WebSocket path 不是普通网页。直接在浏览器打开 Argo 域名，不能用是否显示网页来判断节点可用性。

更合理的判断：

- 访问 `https://<argo-domain>/<ws-path>`。
- 如果返回 `HTTP/2 405`，通常说明请求已经到达 sing-box 的 WebSocket 入站，只是浏览器不是 VMess 客户端，所以方法不匹配。
- 如果返回 `404`，更可能是 Cloudflare 隧道域名没有对应到当前 VPS 服务。
- 如果 TLS 连接失败或超时，需要继续排查 Cloudflare 隧道、运营商路径或本地网络。

## 5. WiFi 丝滑、移动流量不可用，不一定是 QuanX 配置问题

用户观察到同样配置下 WiFi 可用，但切换到青海移动流量后访问异常。

当前判断：

- 这更像接入网络路径差异，而不是 QuanX 配置本身错误。
- WiFi 和青海移动流量的出口完全不同。
- 青海移动流量可能经过本地移动核心网、CGNAT、跨省骨干和不同国际出口。
- RackNerd 美东 VPS 对青海移动不一定友好。

进一步验证中发现：

- 青海移动流量可以快速打开订阅链接。
- 这说明青海移动到 Cloudflare 并非完全不可达。
- 真正的问题一度集中在 VMess-Argo 节点里的临时 Argo 域名已经失效。

因此后续排查要区分：

- 订阅文件是否能拉取。
- Argo 代理域名是否仍然有效。
- VMess 节点中的 `host` / `sni` 是否匹配当前运行中的 tunnel。
- 中国移动到 Cloudflare 优选入口或 VPS 的路径是否稳定。

## 6. 中国移动下这台 VPS 的合理定位

本轮结论不是“继续盲目换协议”，而是要明确这台 RackNerd VPS 的角色。

更合理的用法：

```text
手机移动流量
-> 更适合中国移动的前置入口
-> RackNerd VPS
-> 目标网站
```

也就是说，这台 VPS 更适合做最终落地出口，而不是让青海移动流量直接连接。

优先路线：

1. Cloudflare/Argo/CDN 前置，VPS 做落地。
2. 机场或其他中转节点前置，VPS 做落地。
3. VLESS-Reality、AnyTLS、Hysteria2、TUIC 等直连协议只作为备用测试。

不建议优先押注：

- Hysteria2 / TUIC 这类 UDP 协议。中国移动流量下 UDP/QUIC 质量可能不稳定。
- 临时 Argo 域名。它会变化，不能长期依赖。
- 单纯频繁更换协议。若移动到 VPS 或 Cloudflare 入口的路径差，协议收益有限。

## 7. 后续建议

短期：

- 继续测试当前 VMess-WS + Argo/CDN 订阅。
- 每次测试前确认订阅中的 `host` / `sni` 对应当前 VPS 上仍在运行的 cloudflared 代理隧道。
- 如果订阅能打开但节点不能用，优先检查代理隧道，而不是先怀疑 QuanX。

中期：

- 改为固定 Argo Tunnel，绑定自己的 Cloudflare 域名。
- 不再依赖 `trycloudflare.com` 临时域名。
- 用固定域名作为 QuanX 节点的 `host` / `sni`。

长期：

- 如果主要使用青海移动流量，下一台 VPS 优先考虑更适合中国移动的地区或线路，例如洛杉矶、圣何塞、日本、新加坡、香港，或明确标注移动 CMI/优化线路的商家。
- 当前 RackNerd 美东 VPS 更适合继续作为低成本测试机或最终落地出口，不宜直接作为移动流量主力入口。

