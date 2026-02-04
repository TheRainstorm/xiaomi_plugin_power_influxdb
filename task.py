from miio import DeviceFactory
from influxdb import InfluxDBClient
import time
import os
import socket

# 设置全局默认超时
socket.setdefaulttimeout(10)

is_init = False  # 是否已初始化设备
dev_list = []  # 设备列表
dev_names = []  # 设备名称列表
influx_client = None  # InfluxDB客户端

DEVICE_IPS = ""
DEVICE_TOKENS = ""
DEVICE_NAMES= ""

INFLUX_HOST = ""
INFLUX_PORT = 0
INFLUX_USER = ""
INFLUX_PASS = ""
INFLUX_DB = ""

MEASUREMENT= ""

DEBUG = False  # 是否开启调试模式

def read_env():
    global DEVICE_IPS, DEVICE_TOKENS, INFLUX_HOST, INFLUX_PORT, INFLUX_USER, INFLUX_PASS, INFLUX_DB, DEBUG, MEASUREMENT, DEVICE_NAMES
    try:
        DEVICE_IPS = os.environ["DEVICE_IPS"]
        DEVICE_TOKENS = os.environ["DEVICE_TOKENS"]
        DEVICE_NAMES = os.environ["DEVICE_NAMES"]
        INFLUX_HOST = os.environ["INFLUX_HOST"]
        INFLUX_PORT = int(os.environ["INFLUX_PORT"])
        INFLUX_USER = os.environ["INFLUX_USER"]
        INFLUX_PASS = os.environ["INFLUX_PASS"]
        INFLUX_DB = os.environ["INFLUX_DB"]
        MEASUREMENT = os.getenv("MEASUREMENT", "power_consumption")
        DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    except KeyError as e:
        print(f"环境变量缺失: {e}")
        raise RuntimeError("请确保所有环境变量已设置")
    print(f"读取环境变量: DEVICE_IPS={DEVICE_IPS}, INFLUX_HOST={INFLUX_HOST}, INFLUX_PORT={INFLUX_PORT}, INFLUX_USER={INFLUX_USER}, INFLUX_DB={INFLUX_DB}, DEBUG={DEBUG}, MEASUREMENT={MEASUREMENT}, DEVICE_NAMES={DEVICE_NAMES}")

def setup_devices():
    global dev_list, dev_names
    ip_list = DEVICE_IPS.split(",")
    token_list = DEVICE_TOKENS.split(",")
    dev_names = DEVICE_NAMES.split(",")
    for ip, token, dev_name in zip(ip_list, token_list, dev_names):
        if ip and token:
            dev = DeviceFactory.create(ip.strip(), token.strip())
            dev_list.append(dev)
            print(f"设备已添加: {dev_name} {ip.strip()} (Token: {token.strip()[:5]}xxx{token.strip()[-5:]})")

def write_to_influxdb(power, dev_name):
    json_body = [{
        "measurement": MEASUREMENT,
        "tags": {"device": dev_name},
        "fields": {"value": power}
    }]
    influx_client.write_points(json_body)
    if DEBUG:
        print(f"{dev_name}: {power} W")

def task():
    global is_init, dev_list, influx_client
    if not is_init:
        try:
            print("设备未初始化，正在读取环境变量并设置设备...")
            read_env()
            print("环境变量读取成功，正在初始化设备...")
            setup_devices()  # 初始化设备
            print("设备初始化成功")
            influx_client = InfluxDBClient(INFLUX_HOST, INFLUX_PORT, INFLUX_USER, INFLUX_PASS, INFLUX_DB)
            print("连接 Influxdb 成功")
            is_init = True
        except Exception as e:
            print(f"初始化失败: {e}")
            return  # 初始化失败直接退出本次任务，等待下一次
    
    from concurrent.futures import ThreadPoolExecutor

    def get_power(dev):
        return dev.get_property_by(11, 2)[0]["value"]  # 获取功率值
    
    def process_one_device(dev, dev_name):
        try:
            power = get_power(dev)
            write_to_influxdb(power, dev_name)
        except Exception as e:
            # 捕获所有异常（超时、连接拒绝、找不到设备等）
            print(f"设备 [{dev_name}] 读取失败: {e}")

    # 使用线程池并发请求，避免单个设备网络延迟影响整体耗时
    # max_workers 设置为设备数量，确保能同时处理
    if dev_list:
        with ThreadPoolExecutor(max_workers=len(dev_list)) as executor:
            executor.map(process_one_device, dev_list, dev_names)