# 2026-07-05 手机热点 + Quantumult X TUN 代理测速记录

## 测试环境

- 时间：2026-07-05 12:17 左右（Asia/Shanghai）
- 接入网络：Mac 连接手机热点，手机为中国移动 5G
- 代理工具：Quantumult X，全局代理/TUN 使用中的真实路径
- TUN 证据：测速样本里的 `local_ip` 均为 `198.19.0.1`
- 方法：命令行 `curl` 不指定 `--proxy` 或 SOCKS 端口，依赖系统路由进入 Quantumult X TUN

## 当前先验和修正

- 初始假设：三条链路可以通过 Quantumult X 策略切换后重复同一组 HTTP 测试。
- 观察修正：本地 HTTP/SOCKS 端口未监听，不能用本地代理端口做可控切换；真实使用环境应保留 TUN 路由。
- 执行策略：每次手动切换 Quantumult X 当前节点后，重复同一组测试命令并记录。

## 花云香港节点

- Quantumult X 当前 proxy：花云香港节点
- 出口 IP：`212.107.28.57`
- 出口归属：Hong Kong，Kirino LLC / AS41378
- 成功率：测试目标均成功，`5/5` 或 `3/3`

### 延迟和页面请求

| 目标 | 样本数 | 平均总耗时 | 最小 | 最大 | 备注 |
|---|---:|---:|---:|---:|---|
| `http://www.gstatic.com/generate_204` | 5 | 214.1 ms | 193.7 ms | 223.0 ms | HTTP 204，非 TLS |
| `https://www.cloudflare.com/cdn-cgi/trace` | 5 | 403.5 ms | 377.2 ms | 473.8 ms | TLS 建连平均 260.2 ms |
| `https://www.google.com/generate_204` | 5 | 641.6 ms | 376.3 ms | 1432.5 ms | 有一次 TLS 建连明显抖动 |
| `https://github.com/` | 5 | 626.4 ms | 539.1 ms | 762.9 ms | 首页约 565 KB |

### 吞吐

| 测试 | 样本数 | 平均速度 | 最小 | 最大 | 备注 |
|---|---:|---:|---:|---:|---|
| Cloudflare 25MB 下载 | 3 | 157.90 Mbps | 129.35 Mbps | 186.78 Mbps | 有效样本 |
| Cloudflare 8MB 上传 | 3 | 18.71 Mbps | 17.28 Mbps | 19.53 Mbps | 有效样本 |
| Cachefly 10MB 下载 | 3 | 废弃 | 废弃 | 废弃 | 实际只返回 24 bytes，不能代表下载速度 |

### 当前判断

花云香港节点在这次中国移动 5G 热点环境下表现稳定。延迟层面，普通 204 探测约 200 ms，TLS 站点首包多在 380-760 ms 区间；Google 出现一次 1.4 s 级抖动。吞吐层面，Cloudflare 下载峰值接近 187 Mbps，上传约 19 Mbps，整体足够支撑日常网页、开发下载和一般视频流。

## RackNerd

- Quantumult X 当前 proxy：RackNerd
- 出口 IP：`192.3.80.199`
- 出口归属：United States，Seattle，RackNerd LLC / AS36352 HostPapa
- 成功率：测试目标均成功，`5/5` 或 `3/3`
- TUN 证据：样本 `local_ip` 均为 `198.19.0.1`

### 延迟和页面请求

| 目标 | 样本数 | 平均总耗时 | 最小 | 最大 | 备注 |
|---|---:|---:|---:|---:|---|
| `http://www.gstatic.com/generate_204` | 5 | 1716.2 ms | 1173.2 ms | 2748.6 ms | HTTP 204，非 TLS |
| `https://www.cloudflare.com/cdn-cgi/trace` | 5 | 1965.2 ms | 1614.4 ms | 2432.9 ms | TLS 建连平均 1518.2 ms |
| `https://www.google.com/generate_204` | 5 | 2350.5 ms | 1822.1 ms | 2850.8 ms | TLS 建连平均 1881.3 ms |
| `https://github.com/` | 5 | 4098.8 ms | 2724.6 ms | 5781.6 ms | 首页约 565 KB |

### 吞吐

| 测试 | 样本数 | 平均速度 | 最小 | 最大 | 备注 |
|---|---:|---:|---:|---:|---|
| Cloudflare 25MB 下载 | 3 | 9.74 Mbps | 5.54 Mbps | 18.02 Mbps | 有效样本，波动很大 |
| Cloudflare 8MB 上传 | 3 | 7.74 Mbps | 7.18 Mbps | 8.15 Mbps | 有效样本 |

### 当前判断

RackNerd 在这次中国移动 5G 热点环境下能用，但体感会明显慢。核心问题不是连通性，而是链路质量：TLS 建连普遍在 1.2-2.3 秒，普通 204 请求也要 1.1-2.7 秒；下载吞吐低且不稳，25MB 下载最快约 18 Mbps，最慢约 5.5 Mbps。和花云香港相比，RackNerd 更适合作为低频备用或美国落地需求，不适合作为当前移动热点下的主力日用节点。

## 暂时对比

| 链路 | 出口 | gstatic 204 平均 | Cloudflare trace 平均 | GitHub 首页平均 | 下载平均 | 上传平均 |
|---|---|---:|---:|---:|---:|---:|
| 花云香港 | `212.107.28.57` | 214.1 ms | 403.5 ms | 626.4 ms | 157.90 Mbps | 18.71 Mbps |
| RackNerd | `192.3.80.199` | 1716.2 ms | 1965.2 ms | 4098.8 ms | 9.74 Mbps | 7.74 Mbps |

## 自有域名挂 Cloudflare/CDN 链路

- Quantumult X 当前 proxy：自有域名挂 Cloudflare/CDN 链路
- 出口识别：
  - `api.ipify.org`：`178.128.16.74`
  - `178.128.16.74` 归属：Singapore，DigitalOcean / AS14061
  - `ip-api.com` 当前请求识别为 Cloudflare WARP 香港：`104.28.163.49`
  - `ifconfig.me` 返回 IPv6 Cloudflare 段：`2a09:bac5:398e:2646::3d0:d`
- TUN 证据：样本 `local_ip` 均为 `198.19.0.1`
- 成功率：普通网页/204 请求均成功；`speed.cloudflare.com` 下载和上传均在 TLS 阶段失败

### 延迟和页面请求

| 目标 | 样本数 | 平均总耗时 | 最小 | 最大 | 备注 |
|---|---:|---:|---:|---:|---|
| `http://www.gstatic.com/generate_204` | 5 | 420.7 ms | 298.1 ms | 475.7 ms | HTTP 204，非 TLS |
| `https://www.cloudflare.com/cdn-cgi/trace` | 5 | 633.0 ms | 558.1 ms | 733.0 ms | TLS 建连平均 449.1 ms |
| `https://www.google.com/generate_204` | 5 | 577.7 ms | 535.8 ms | 621.2 ms | TLS 建连平均 453.3 ms |
| `https://github.com/` | 5 | 1246.3 ms | 1101.7 ms | 1575.9 ms | 首页约 565 KB |

### 吞吐

| 测试 | 样本数 | 平均速度 | 最小 | 最大 | 备注 |
|---|---:|---:|---:|---:|---|
| Cloudflare 25MB 下载 | 3 | 失败 | 失败 | 失败 | `SSL_ERROR_SYSCALL` |
| Cloudflare 8MB 上传 | 3 | 失败 | 失败 | 失败 | `SSL_ERROR_SYSCALL` |
| OVH 10MB 下载 | 2 | 11.78 Mbps | 9.96 Mbps | 13.60 Mbps | 备用下载样本 |
| ThinkBroadband 10MB 下载 | 2 | 13.39 Mbps | 11.71 Mbps | 15.07 Mbps | 备用下载样本 |
| Hetzner 10MB 下载 | 2 | 失败 | 失败 | 失败 | TLS handshake failure |
| 备用上传 | 4 | 无有效样本 | 无有效样本 | 无有效样本 | 端点返回 400/500，不作为有效上传测速 |

### 当前判断

这条链路的延迟表现介于花云香港和 RackNerd 之间，明显好于 RackNerd，但慢于花云香港。它的问题集中在大流量/特定 TLS 端点：`speed.cloudflare.com` 的下载和上传全部失败，Hetzner 下载也 TLS 握手失败；普通网页、Google 204、GitHub 均可用。当前可把它判断为“浏览可用、吞吐测试兼容性一般”的链路，不适合作为大文件下载或稳定测速链路。

### 复测记录

用户反馈日常体验并不差后，重新测试第三条链路，重点排查 `speed.cloudflare.com` 是否因为其他原因失败。

出口识别在第二次测试中变为：

- `api.ipify.org -4`：`45.197.12.118`
- `api.ipify.org` 自动协议：`128.199.255.242`
- `www.cloudflare.com/cdn-cgi/trace`：`ip=128.199.255.242`，`colo=SIN`，`loc=SG`，`warp=off`，`tls=TLSv1.3`

普通使用类请求复测结果：

| 目标 | 样本数 | 平均总耗时 | 最小 | 最大 | 备注 |
|---|---:|---:|---:|---:|---|
| `http://www.gstatic.com/generate_204` | 8 | 505.1 ms | 377.2 ms | 982.5 ms | 有一次接近 1 秒 |
| `https://www.cloudflare.com/cdn-cgi/trace` | 8 | 925.8 ms | 612.1 ms | 2200.7 ms | 有一次 TLS 抖动到 2 秒 |
| `https://www.google.com/generate_204` | 8 | 572.7 ms | 461.9 ms | 646.9 ms | 稳定 |
| `https://github.com/` | 8 | 1180.4 ms | 1058.4 ms | 1469.0 ms | 稳定 |

备用下载复测结果：

| 测试 | 样本数 | 平均速度 | 最小 | 最大 | 备注 |
|---|---:|---:|---:|---:|---|
| OVH 10MB 下载 | 3 | 13.26 Mbps | 10.05 Mbps | 17.17 Mbps | 有效样本 |
| ThinkBroadband 10MB 下载 | 3 | 15.27 Mbps | 12.34 Mbps | 16.84 Mbps | 有效样本 |
| Cachefly 10MB 下载 | 3 | 废弃 | 废弃 | 废弃 | 实际只返回 24 bytes |

上传复测结果：

| 测试 | 样本数 | 平均速度 | 最小 | 最大 | 备注 |
|---|---:|---:|---:|---:|---|
| `https://httpbin.org/post` 2MB 上传 | 3 | 1.58 Mbps | 0.62 Mbps | 2.20 Mbps | 有效样本，但该端点会回传大响应体，结果偏保守 |
| Cloudflare 2MB 上传 | 3 | 失败 | 失败 | 失败 | TLS 握手失败 |
| Cloudflare 2MB 上传，HTTP/1.1 | 3 | 失败 | 失败 | 失败 | TLS 握手失败 |

`speed.cloudflare.com` 专项排查：

- `https://speed.cloudflare.com/`：TLS 失败，`SSL_ERROR_SYSCALL`
- `https://speed.cloudflare.com/meta`：TLS 失败，`SSL_ERROR_SYSCALL`
- `https://speed.cloudflare.com/__down?bytes=100000`：TLS 失败，`SSL_ERROR_SYSCALL`
- `https://speed.cloudflare.com/__down?bytes=1000000`：TLS 失败，`SSL_ERROR_SYSCALL`
- `--http1.1` 后仍失败
- `openssl s_client -connect speed.cloudflare.com:443 -servername speed.cloudflare.com` 返回 `unexpected eof while reading`
- 失败时 `curl` 的 `local_ip=198.19.0.1`，`remote_ip=198.18.25.173`

复测后的判断修正：

上一次“第三条链路很糟糕”的判断需要收窄。更准确的结论是：这条链路日常网页体验可以解释为“还可以”，因为 Google、GitHub、Cloudflare 普通页面稳定可用，延迟多在 0.5-1.2 秒；但它不适合用 `speed.cloudflare.com` 测速，这个端点在当前 Quantumult X TUN + 第三条链路下存在稳定的 TLS 握手失败。可用备用下载源看，第三条链路下载大致在 13-15 Mbps，比 RackNerd 稳定，也远低于花云香港。

## 三条链路对比

| 链路 | 出口 | gstatic 204 平均 | Cloudflare trace 平均 | GitHub 首页平均 | 下载平均 | 上传平均 |
|---|---|---:|---:|---:|---:|---:|
| 花云香港 | `212.107.28.57` | 214.1 ms | 403.5 ms | 626.4 ms | 157.90 Mbps | 18.71 Mbps |
| 自有 Cloudflare/CDN | `128.199.255.242` / 新加坡 | 505.1 ms | 925.8 ms | 1180.4 ms | 13.26-15.27 Mbps | 1.58 Mbps |
| RackNerd | `192.3.80.199` | 1716.2 ms | 1965.2 ms | 4098.8 ms | 9.74 Mbps | 7.74 Mbps |

当前排序：花云香港最适合当前中国移动 5G 热点下的日常主力；自有 Cloudflare/CDN 链路适合浏览备用，但吞吐和 TLS 兼容性需要继续排查；RackNerd 能用但明显慢，适合需要美国落地时短时使用。
