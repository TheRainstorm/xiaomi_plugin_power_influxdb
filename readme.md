## 说明

从小米智能插座获取功率，然后写入到 InfluxDB。可用于 grafana 监控设备功率。

Feature:

- [x] 支持多个设备
- [x] 支持 docker 部署

效果

![grafana.png](https://imagebed.yfycloud.site/2026/01/25c489119c87b9416aa71765132b11b0.png)

## 使用

### 1. 获得设备 token

[update 2026.01.09] 目前 [Xiaomi-cloud-tokens-extractor](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor) 已经可以正常获得 token，推荐使用该方法。

~~可以使用 [python-miio](https://github.com/rytilahti/python-miio) 项目获得设备 token，但是该项目目前无法获得 token，且该 issue 已经被提出来 1 年了。~~

~~目前可以使用 Xiaomi-cloud-tokens-extractor [这里](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor/issues/43#issuecomment-3047232372)的方法获得 token~~

### 2. 设置环境变量

参考 `.env.template`， 填写设备 IP，token，InfluxDB 连接信息等，保存为 `.env`。

### 3.1 本地运行

```shell
pip install -r requirements.txt

# 导入环境变量
set -a
source .env
set +a

python main.py
```

成功时输出应该包含

```shell
设备初始化成功
连接 Influxdb 成功
```

### 3.2 docker 部署

- 参考 docker-compose 配置
  - 需要修改 `env_file` 的路径为你的环境变量文件路径

```yaml
version: '3.8'
services:
  xiaomi_plugin:
    image: rzero/xiaomi_plugin_power:latest
    container_name: xiaomi_plugin
    network_mode: host
    env_file: stack.env
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "1m"   # 单个日志文件最大 1MB
        max-file: "1"     # 最多保留 1 个文件
```
- 启动

```shell
docker-compose up -d
```

## 其它

### grafana 查询命令

```shell
SELECT mean("value") FROM "power_consumption" WHERE $timeFilter GROUP BY time(30s), "device"::tag fill(null)
```

### 跨网段使用 miio

我使用 wg 将两个局域网连接，虽然可以 ping 通小米智能插座，但是 miio 无法连接设备，报错：

```shell
miio.exceptions.DeviceException: Unable to discover the device 
```

可能是小米插座收到不是本地网段的请求时拒绝响应了，解决办法是在网关上做 SNAT，将请求伪装成本地网段的请求，示例：

- 在智能开关所在局域网路由器上执行
- 将来自远端 wg 网段的请求，伪装成本地路由 lan 口 IP 地址

```shell
nft insert rule inet fw4 srcnat ip saddr <remote_ip> ip daddr <device_ip> counter snat to <lan_ip>
```
