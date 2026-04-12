# QuantumultX 链式代理配置指南

## Reference1:

[![视频讲解](https://img.youtube.com/vi/ggBtMM7hoy8/0.jpg)](https://www.youtube.com/watch?v=ggBtMM7hoy8)

### 基本原理

```
设备 → 中转节点（机场） → 落地 VPS → 目标网站
```

### 配置步骤

#### 1. 配置资源解析器

在 `[general]` 中添加：

```ini
[general]
resource_parser_url = https://raw.githubusercontent.com/KOP-XIAO/QuantumultX/master/Scripts/resource-parser.js
```

#### 2. 配置落地 VPS 节点

在 `[server_local]` 中添加你的落地 VPS 节点，tag 命名为 `vps`：

```ini
[server_local]
shadowsocks=your_domain:5443,method=2022-blake3-aes-256-gcm,password=DgrOjcmCMEr97iLy2V99BUelOI2b08vApCrR+osYsJs=, fast-open=true, udp-relay=true, tag=vps-落地节点
```

#### 3. 配置分流规则

在 `[filter_local]` 中，将落地 VPS 的 IP 指向中转节点策略组：

```ini
[filter_local]
# 让访问 VPS 的流量走机场中转
ip-cidr, vps_ip/32, 节点选择
```

> **说明**：`vps_ip` 替换为你实际的 VPS IP 地址，`节点选择` 是你的机场策略组名称。

#### 4. 配置远程分流规则

在 `[filter_remote]` 中，使用 `#via=` 参数指定代理链：

```ini
[filter_remote]
# OpenAI 规则走代理链
https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/OpenAI/OpenAI.list#via=%TUN%, tag=🤖OpenAI, force-policy=OpenAI, update-interval=172800, opt-parser=true, enabled=true
```

#### 5. 配置策略组

在 `[policy]` 中配置策略组：

```ini
[policy]
# 机场节点选择策略组
static=节点选择, 自动选择, 香港, 台湾, 日本, 韩国, 新加坡, 美国, PROXY, DIRECT, img-url=https://raw.githubusercontent.com/Orz-3/mini/master/Color/Static.png

# OpenAI 专用策略组，选择 vps 即可走代理链
static=OpenAI, vps-落地节点, DIRECT, 香港, 台湾, 日本, 韩国, 新加坡, 美国, 节点选择, img-url=https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/Bot.png
```

### 注意事项

- 确保 VPS 节点的 tag 名称与策略组中引用的名称一致
- `ip-cidr` 规则中的 IP 必须是 VPS 的实际公网 IP
- 中转节点需要能够正常访问你的 VPS

### 自定义规则

在 `[filter_local]` 中可以添加自定义分流规则，实现指定域名走代理链：

```ini
[filter_local]
host-suffix, xxx.com, vps, via-interface=%TUN%
```

**规则格式说明**：

- `host-suffix`：匹配域名后缀
- `xxx.com`：要匹配的域名
- `vps`：使用的策略（即落地 VPS 节点）
- `via-interface=%TUN%`：通过 TUN 接口实现链式代理

## Reference2

根据[Reference2](https://linux.do/t/topic/1404742/44)，在 Quantumult X (QX) 中实现链式代理（例如通过机场节点中转连接到你自己的 VPS 落地节点，用于解锁特定服务）的配置方法主要包含以下几个步骤：

### 1. 基础解析器配置

首先，在配置文件的 `[general]` 模块中添加/确保有资源解析器：

**Ini, TOML**

```
resource_parser_url= https://raw.githubusercontent.com/KOP-XIAO/QuantumultX/master/Scripts/resource-parser.js
```

### 2. 添加落地节点

在 `[server_local]` 模块中配置你的落地 VPS 节点，并为其设置一个专门的标签（tag），例如命名为 `vps`。

### 3. 本地分流规则（核心中转逻辑）

在 `[filter_local]` 模块中添加一条规则，将你落地 VPS 的真实 IP 地址强制路由给你的中转节点策略组（例如名为 `节点选择` 的机场策略组）：

**Ini, TOML**

```
ip-cidr, vps_ip/32, 节点选择
```

*（将 `vps_ip` 替换为你落地 VPS 的实际 IP 地址。这一步的作用是：当 QX 尝试连接你的 VPS 时，会先通过机场节点出去，形成链条的第一环。）*

### 4. 策略组配置

在 `[policy]` 模块中，设置好你的中转节点策略组以及需要走链式代理的应用策略组（例如 `OpenAI`）：

**Ini, TOML**

```
static=节点选择, 自动选择, 香港, 台湾, 日本, 韩国, 新加坡, 美国, PROXY, DIRECT
static=OpenAI, vps, DIRECT, 香港, 台湾, 日本, 韩国, 新加坡, 美国, 节点选择
```

配置完成后，在 QX 面板中将 `OpenAI` 这个策略组的出口选择为 `vps`。

### 5. 规则指定与 TUN 参数（触发代理链）

最后一步是让目标流量走你的 `vps` 节点，并且必须带上 TUN 相关的参数，否则代理链无法正常工作。

* **如果使用远端订阅规则（在 `[filter_remote]` 中）** ：
  在订阅链接的末尾加上 `#via=%TUN%`，并关联到刚才设定的策略组。例如：
  **Ini, TOML**

```
  https://raw.githubusercontent.com/.../OpenAI.list#via=%TUN%, tag=🤖OpenAI, force-policy=OpenAI, opt-parser=true, enabled=true
```

* **如果使用本地自定义规则（在 `[filter_local]` 中，楼主补充的方法）** ：
  在自定义规则的末尾加上 `via-interface=%TUN%` 参数。例如：
  **Ini, TOML**

```
  host-suffix, xxx.com, vps, via-interface=%TUN%
```

**原理解析：**

这一套配置的核心逻辑在于 **流量的二次路由** 。目标域名（如 `xxx.com`）被规则捕获并加上 TUN 标记后，交给 `vps` 节点处理；而 QX 发现要连接 `vps` 节点的 IP 时，又命中了刚才写的 `ip-cidr` 规则，最终把连接 `vps` 的这部分流量塞进了机场节点（`节点选择` 策略组）里，从而成功连成了“设备 -> 机场节点 -> 落地 VPS -> 目标网站”的代理链。

## Reference3


https://blog.itswincer.com/posts/quantumult-x-chain-proxy-setup/

最近因为 Clash for Windows 作者被请喝茶的缘故，Clash 从内核到各平台客户端的仓库大部分都删库或者归档了，这也不能怪开发者太过风声鹤唳，毕竟还身在国内，写开源而已，犯不上和自己的人身安全作对。之前我一直都是使用 Clash 作为主要的科学上网工具，不过经此一役后我也在考虑是否应该放弃 Clash，于是我仔细梳理了一下目前对科学上网的需求，最终决定将 Clash 切换成 Quantumult X。

### Clash 的缺点

其实我很早就觉得 Clash 在 macOS 上使用有一些不便：

1. 如果想要修改订阅加上分流规则或者自定义的服务器，需要更改机场的配置文件，但是机场的订阅一般又会定时更新去覆盖掉；使用第三方的工具转化或者合并机场的订阅文件算是一个解决方案，但是机场一般出于隐私考虑都会禁止使用第三方工具转换订阅；
2. 本质上 Clash 只是一个代理工具，无法确保在电脑上运行的各个程序的流量都由代理转发——很多软件的网络设置是不经由系统代理的，尤其是在终端的应用：pnpm，go get，curl，brew，ssh，这在软件开发的时候其实还挺烦人的，还需要单独为每一个应用设置代理，不同应用的配置方式还不一样。Clash X Pro 提供的增强模式算是一个解决方案，不过同样也已经下架了。

对于第一点，其实 Quantumult X 就做得很好，分流的规则以及机场的节点是分开配置的，而且无论你有多少不同机场的节点，你都可以通过新建一份分流规则来在所有节点之中切换，而且新建的分流规则并不会被机场本身定时更新的订阅所覆盖。

对于第二点，其实是代理工具和 VPN 的区别，像是 Cisco Anyconnect 这种 VPN 工具，会新建一个虚拟网卡，并新增一条路由规则让所有应用的流量都流经此网卡，也就不再需要单独为不同的应用设置代理选项了。Clash X Pro 的增强模式也是使用这样的解决方案。

> 注意，这种强制所有应用走代理与 Clash 提供的全局代理是不一样的概念，Clash 的全局代理意思是所有通过 Clash 的流量不经分流直接转发到机场节点。

### 机场的审计

对于稍微大一些的机场，都会添加各种各样的审计规则，也就是在服务条款里写的禁止访问政治敏感或者新闻等类型的网站。大部分的机场并不会写明具体是哪些网站被禁止访问，甚至也有些正常的网站会被「误伤」。

对于机场的审计规则我在一开始时表示很不理解，毕竟科学上网就是为了突破 GFW 封锁，怎么机场还又给上了一道锁。后来我想明白了，这类机场一般都是在国内有中转入口的机场，而中转服务器架设在国内受到的监管会比家宽更加严格，本质上也只是机场主规避风险的一种手段。所以目前没有审计规则的机场，要么是直连境外的机场，要么是机场的规模不大，或者机场主愿意承担这种风险。对于前者，访问速度比不上中转机场，对于后者，我只能说： ~而你，我的朋友，你才是真正的英雄~ 。

不过，机场的审计规则对用户来说，也确实也有隐私泄露的风险存在。有审计规则，那必然就有记录审计日志，也就意味着你访问的浏览记录都会被机场所记录，最坏情况下，机场因为某些不可抗力的因素或者是被黑了，流出了所有用户的浏览记录……

> **免责声明：本文并不是要教唆大家通过链式代理的方式去访问被机场封锁的网站，而是仅从技术的角度，探讨如何让自己的网络浏览更安全、隐私。**

### 链式代理的原理

那么，何为链式代理？

其实和机场本身提供的中转类似，我们可以在机场线路外，再加上一层中转，也就是把机场的落地节点也当作是二次中转，而由我们自己的境外 VPS 提供真正的落地。网上有很多关于如何配置 Clash 的链式代理的教程，不过 Quantumult X 的却很少，所以我就来抛砖引玉了。

以日常使用的中转机场来举例：

![原理图](https://ae03.alicdn.com/kf/Sae910277fb994c92af9c418a36b1ea55y.jpg)

先看不加上 VPS 的情况，我们的电脑到机场国内的中转服务器（Relay Proxy）是通过公网通信，中转服务器通常是国内的公有云（阿里云，华为云），然后再由中转服务器通过 IPLC/IEPL 等内网专线连接到海外落地服务器上，从而实现科学上网的功能。

需要注意的是，虽然 IPLC/IEPL 不会被墙，但是因为它仍然有一端是处于国内，因此从你的所在地到中转服务器的线路也直接影响到了科学上网的使用体验。而当你请求被机场封锁的域名时，连接在中转服务器时就会被丢掉，根本不会再往专线另一端发了，因为中转服务器才是运行 Shadowsocks 的服务端，它可以直接拿到访问请求的域名。

而在有 VPS 的情况下，我们就可以把机场线路的整体当成是中转服务器，由 VPS 来做落地（Final Proxy）。这样做的好处就是，流量会被加密两次，一次是中转机的加密，另一次是 VPS 的加密，而中转机拿到流量后，因此还存在一次加密，所以也根本看不到你具体的访问，只能看到是对 VPS 的访问，只有 VPS，才能看到你真正访问的域名。这样也能解决机场审计记录的隐私问题。

经过了两次加密和转发，性能可能会有些损耗，不过这在浏览网页时一般是感知不到的（跑测速可能有细微差异。

### 链式代理的配置

Quantumult X 配置链式代理不复杂，而且配置完成后，并不会被机场的定时更新的规则所覆盖：

#### VPS 配置

VPS 的服务端并不需要开启什么流量伪装或者混淆等复杂的配置，因为 VPS 与机场节点之间的连接并不过墙，设置一个稍微复杂一点的密码，选一个安全的加密方法即可，因此 Shadowsocks 就够用了，你可以参考[我的配置](https://github.com/WincerChan/QXRelayConv/blob/master/sample_shadowsocks.json)。

#### 添加 VPS 节点

在 Quantumult X 点击设置 -> 节点 -> 添加，把以上配置填进去，标签可以随意，我填的是 hh-jp。

或者在 Quantumult X 的 设置 -> 节点 -> 节点资源，这里可以加上 fast-open 和 udp-relay 参数：

ini复制代码

```ini
shadowsocks=xx.xx.xxx.xxx:xxxxx, method=aes-256-gcm, password=xxxxxxxxx, fast-open=true, udp-relay=true, tag=hh-jp
```

#### 修改分流配置

在 Quantumult X 设置 -> 配置文件 -> 编辑，会弹出一个编辑框，在分流规则部分的尾部加入以下规则：

bash复制代码

```bash
ip-cidr, xx.xx.xxx.xxx/32, ♾️ Relay
# 有两种选择，直接给 final 加上中转
final, hh-jp, via-interface=%TUN%
# 或者针对特定域名加上中转，我比较推荐这种
host-suffix, xxx.xxx, hh-jp, via-interface=%TUN%
```

其中第一行 ip-cidr 的规则，是为了让所有流经 VPS 的流量，都通过机场的节点进行中转，`♾️ Relay` 这个策略组是我新建的，你可以把它重命名为你目前现有的规则策略或者新增一个策略组来专门做转发。

我比较推荐后者，选择新建一个策略组并把与 VPS 在同一个地区的节点都加进来，这样从中转节点到 VPS 的延迟就会更低。

如果你觉得一个域名一个域名加比较麻烦，也可以直接针对 final 添加中转，需要注意如果已经存在 final 的规则，把原有的删掉。不过我并不推荐直接给 final 规则加上中转，因为我觉得 final 规则应该设置成距离自己最近、延迟最低的节点。

> 我为此写了一个[简单的工具](https://github.com/WincerChan/QXRelayConv)，可以更方便的管理需要链式代理的域名，可自行部署在 VPS 上。

### 如何确认配置成功

有两种方式：

#### 在 Quantumult X 查看流量日志

在 Quantumult X 的网络活动菜单栏，请求配置后的中转域名，应该会有两条流量记录产生：一条记录的目标服务器是 HH-JP，也就是我配置的 VPS 节点名称；另一条记录的目标服务器就是 JAPAN 17，也就是机场的节点。

![流量日志](https://ae05.alicdn.com/kf/Sa9b8b3428d4a46b8b2527bb7e8daae74Q.jpg)

#### 在 VPS 节点查看

在 VPS 运行命令：

bash复制代码

```bash
$ lsof -i:[listen_port]
COMMAND    PID        USER   FD   TYPE SIZE/OFF NODE NAME
ssserver 21286 shadowsocks   11u  IPv4      0t0  TCP [listen_ip]:[listen_port] (LISTEN)
ssserver 21286 shadowsocks   13u  IPv4      0t0  UDP [listen_ip]:[listen_port]
ssserver 21286 shadowsocks   14u  IPv4      0t0  TCP [listen_ip]:[listen_port]->[relay_ip]:[port] (ESTABLISHED)
```

你需要查看，与 VPS 建立连接的这个 relay_ip 是否是你选择的中转策略的 IP，或者确认它不是你目前宽带的 IP 就行。

### 机场的选择

最后，还是谈谈机场的选择，我并不建议把机场是否有审计规则作为评价机场好坏的标准，因为可能科学上网 99% 的情况下都不会碰到被审计规则封锁的网站。而我在过去一年自费购买了差不多 10 家机场，其中只有一家规模不是很大的机场没有审计规则，这家机场的线路比较少但是流量又比较贵，因此我并不会推荐这家。

如果你不知道机场有审计规则这回事，那你就继续安心用；如果你目前的机场用的挺满意但是带有审计规则有点膈应，所以想换一个没有审计规则的机场，请慎重考虑。

目前的科学上网工具大部分都是支持链式代理的，我也比较推荐你用链式代理 + VPS 来绕过审计规则，如果你用的科学上网工具不支持链式代理，那么我更推荐你换掉工具而不是机场。

https://www.v2ex.com/t/1081206

圈 x 使用起来很舒心，基本上打开就不用管了，但是发现很多机场都有审计策略，有一些网站（甚至是新闻网站）都无法访问，也不能怪机场审计太严格，尤其是中转机场，国内入口是要担风险的。

再加上既然机场有审计，那么势必会分析我们的访问网址，设置会进行日志记录，那么，懂得都懂。 所以就想起来使用链式代理，小火箭实现链式代理很容易，但是缺点就是规则自定义非常不容易。圈 x 的规则非常好用，但是链式代理一直都是很难设置，网上找了各种方法，对于订阅规则指定链式代理一直都不成功。

后来经过网上各种大神指点，自己各种摸索终于搞定了方法，写一个简明的教程，主要是给自己作为指引使用，另外发出来希望给有需要的兄弟们作为参考。 这个方法经过我的测试，可以随意指定需要的订阅规则走链式代理。

#### 方法如下：

1.资源解析器 一定要先在配置文件中添加好资源解析器，如下： [general] resource_parser_url=[https://raw.githubusercontent.com/KOP-XIAO/QuantumultX/master/Scripts/resource-parser.js](https://raw.githubusercontent.com/KOP-XIAO/QuantumultX/master/Scripts/resource-parser.js)

2.准备 2.1 假设自己的 vps 网址为 8.8.8.8 ，且已经配置好 ss 服务。 2.2 在 Quantumult X 点击设置 -> 节点 -> 添加，把 vps 的节点配置填进去，标签可以随意，比如 vps 2.3 分流设置

---

在分流菜单添加分流 类型：IP-CIDR 参数：8.8.8.8/32 策略：选择想要通过的机场策略

或者直接编辑配置文件： [filter_local] ip-cidr, 8.8.8.8/32, 自己想要通过的机场策略

---

3.链式代理使用

3.1 如果想要某个域名走链式代理： host-suffix, [xxx.xxx](http://xxx.xxx/), vps, via-interface=%TUN%

3.2 如果想要 final 走链式代理： final, vps, via-interface=%TUN%

3.3 如果想要某个引用资源-分流走链式代理：

3.3.1 自定义策略新建策略组名字例如 myvps ，在该策略组中添加一个节点即可，自己的 vps 节点

3.3.2 引用资源-分流中，添加分流订阅，以 google 规则举例： [https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/Google/Google.list](https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/Google/Google.list)

3.3.3 资源路径填写 google 的订阅地址，后方加上#via=%TUN%，也就是： [https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/Google/Google.list#via=%TUN%](https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/Google/Google.list#via=%TUN%)

3.3.4 策略偏好选择 myvps

3.3.5 打开资源解析器

3.3.6 确定后更新资源即可。

4.验证成功 在 Quantumult X 的网络活动菜单栏，请求配置后的中转域名，应该会有两条流量记录产生：一条记录的目标服务器是 vps ，也就是配置的 VPS 节点名称；另一条记录的目标服务器就是选择通过的机场策略节点。
