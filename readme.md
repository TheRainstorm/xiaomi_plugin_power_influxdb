## 说明

从小米智能插座获取功率，然后写入到 InfluxDB。

Feature:

- [x] 支持多个设备

## 使用

### 获得设备 token

可以使用 [python-miio](https://github.com/rytilahti/python-miio) 项目获得设备 token，但是该项目目前无法获得 token，且该 issue 已经被提出来 1 年了。

目前可以使用这里的方法获得 token：
https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor/issues/43#issuecomment-3047232372

### 设置环境变量

设置好 `.env.template` 中的环境变量

参考以下 docker-compose 配置（需要修改 `env_file` 的路径）：

```yaml
version: '3.8'
services:
  xiaomi_plugin:
    image: rzero/xiaomi_plugin_power:latest
    container_name: xiaomi_plugin
    network_mode: host
    env_file: stack.env
    restart: unless-stopped
```

### grafana 查询命令

```shell
SELECT mean("value") FROM "power_consumption" WHERE $timeFilter GROUP BY time(30s), "device"::tag fill(null)
```