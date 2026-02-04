## 说明

从小米智能插座获取功率，然后写入到 InfluxDB。可用于 grafana 监控设备功率。

Feature:

- [x] 支持多个设备
- [x] docker 部署

效果

![grafana.png](https://imagebed.yfycloud.site/2026/01/25c489119c87b9416aa71765132b11b0.png)

## 使用

### 1. 获得设备 token

[update 2026.01.09] 目前 [Xiaomi-cloud-tokens-extractor](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor) 已经可以正常获得 token，推荐使用该方法。

~~可以使用 [python-miio](https://github.com/rytilahti/python-miio) 项目获得设备 token，但是该项目目前无法获得 token，且该 issue 已经被提出来 1 年了。~~

~~目前可以使用 Xiaomi-cloud-tokens-extractor [这里](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor/issues/43#issuecomment-3047232372)的方法获得 token~~

### 2. 设置环境变量

参考 `.env.template`， 填写设备 IP，token，InfluxDB 连接信息等，保存为 `.env`。

| Variable | Description | Example |
| :--- | :--- | :--- |
| `DEVICE_IPS` | Comma-separated list of device IP addresses | `192.168.1.10,192.168.1.11` |
| `DEVICE_TOKENS` | Comma-separated list of device tokens | `token1,token2` |
| `DEVICE_NAMES` | Comma-separated list of device names (for tagging) | `pc_plug,monitor_plug` |
| `INFLUX_HOST` | InfluxDB Host | `localhost` |
| `INFLUX_PORT` | InfluxDB Port | `8086` |
| `INFLUX_USER` | InfluxDB Username | `admin` |
| `INFLUX_PASS` | InfluxDB Password | `password` |
| `INFLUX_DB` | InfluxDB Database Name | `xiaomi_power` |
| `MEASUREMENT` | InfluxDB Measurement Name (Optional) | `power_consumption` (default) |
| `INTERVAL` | Polling interval in seconds (Optional) | `5` (default) |
| `DEBUG` | Enable debug logging (Optional) | `True` or `False` (default) |


### 3. 运行

docker：

```bash
docker run -it \
  --name xiaomi_plugin \
  --network host \
  --env-file .env \
  rzero/xiaomi_plugin_power
```

本地：
```shell
# pip install -r requirements.txt
uv sync

# 导入环境变量
set -a && source .env && set +a

python main.py
```

docker-compose 配置

```yaml
version: '3.8'
services:
  xiaomi_plugin:
    image: rzero/xiaomi_plugin_power:latest
    container_name: xiaomi_plugin
    network_mode: host
    env_file: .env
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "1m"   # 单个日志文件最大 1MB
        max-file: "1"     # 最多保留 1 个文件
```

示例输出

```shell
任务执行间隔: 5 秒
任务将于 2026-02-04 15:39:35 开始执行
设备未初始化，正在读取环境变量并设置设备...
读取环境变量: DEVICE_IPS=192.168.1.1, INFLUX_HOST=influx.lan, INFLUX_PORT=8086, INFLUX_USER=user, INFLUX_DB=db, DEBUG=True, MEASUREMENT=power_consumption, DEVICE_NAMES=foo
环境变量读取成功，正在初始化设备...
设备已添加: foo 192.168.1.1 (Token: d951exxx29bbf)
设备初始化成功
连接 Influxdb 成功
foo: 199 W
```

## 其它


### grafana + influxdb 部署

同时部署 grafana 和 influxdb，请按需修改环境变量和数据卷路径

```yaml
version: '3'
services:
  influxdb:
    image: influxdb:1.8  # 使用 1.x 版本兼容简单
    container_name: influxdb
    ports:
      - "8086:8086"
    volumes:
      - /var/lib/docker/docker_data/influxdb/data:/var/lib/influxdb
    environment:
      - INFLUXDB_DB=xxx
      - INFLUXDB_ADMIN_USER=xxx
      - INFLUXDB_ADMIN_PASSWORD=xxx
    restart: unless-stopped
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - /var/lib/docker/docker_data/grafana/data:/var/lib/grafana  # 配置持久化
      - /var/lib/docker/docker_data/grafana/etc/grafana/grafana.ini:/etc/grafana/grafana.ini
    environment:
      - GF_SECURITY_ADMIN_USER=xxx
      - GF_SECURITY_ADMIN_PASSWORD=xxx
    user: "0:0"
    depends_on:
      - influxdb
    restart: unless-stopped
```

### grafana 查询命令

```shell
SELECT mean("value") FROM "power_consumption" WHERE $timeFilter GROUP BY time(30s), "device"::tag fill(null)
```

### 跨网段使用 miio

通过 wireguard 三层组网时，虽然可以 ping 通插座，但是会遇到 miio 无法连接设备的报错：

```shell
miio.exceptions.DeviceException: Unable to discover the device 
```

可能是小米插座会拒绝响应非 LAN 网段的请求，解决办法是在网关上做 SNAT，将请求伪装成 LAN 网段的请求，示例：

- 在智能开关所在局域网路由器上执行
- 将来自远端 wg 网段的请求，伪装成本地路由 lan 口 IP 地址

```shell
nft insert rule inet fw4 srcnat ip saddr <remote_ip> ip daddr <device_ip> counter snat to <lan_ip>
```
