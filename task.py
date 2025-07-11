from miio import DeviceFactory
from influxdb import InfluxDBClient
import time
import os

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
    global DEVICE_IP, DEVICE_TOKEN, INFLUX_HOST, INFLUX_PORT, INFLUX_USER, INFLUX_PASS, INFLUX_DB, DEBUG, MEASUREMENT, DEVICE_NAMES
    try:
        DEVICE_IP = os.environ["DEVICE_IP"]
        DEVICE_TOKEN = os.environ["DEVICE_TOKEN"]
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
    print(f"读取环境变量: DEVICE_IP={DEVICE_IP}, DEVICE_TOKEN={DEVICE_TOKEN[:5]}xxx{DEVICE_TOKEN[-5:]}, INFLUX_HOST={INFLUX_HOST}, INFLUX_PORT={INFLUX_PORT}, INFLUX_USER={INFLUX_USER}, INFLUX_DB={INFLUX_DB}, DEBUG={DEBUG}, MEASUREMENT={MEASUREMENT}, DEVICE_NAMES={DEVICE_NAMES}")

def setup_devices():
    global dev_list, dev_names
    ip_list = DEVICE_IPS.split(",")
    token_list = DEVICE_TOKENS.split(",")
    dev_names = DEVICE_NAMES.split(",")
    for ip, token in zip(ip_list, token_list):
        if ip and token:
            dev = DeviceFactory.create(ip.strip(), token.strip())
            dev_list.append(dev)
            print(f"设备已添加: {ip.strip()} (Token: {token.strip()[:5]}xxx{token.strip()[-5:]})")

def write_to_influxdb(power, dev_name):
    json_body = [{
        "measurement": MEASUREMENT,
        "tags": {"device": dev_name},
        "fields": {"value": power}
    }]
    influx_client.write_points(json_body)
    if DEBUG:
        print(f"写入数据: {power} W")

def task():
    global is_init, dev_list
    if is_init is None:
        print("设备未初始化，正在读取环境变量并设置设备...")
        read_env()
        print("环境变量读取成功，正在初始化设备...")
        setup_devices()  # 初始化设备
        print("设备初始化成功")
        influx_client = InfluxDBClient(INFLUX_HOST, INFLUX_PORT, INFLUX_USER, INFLUX_PASS, INFLUX_DB)
        print("连接 Influxdb 成功")
        is_init = True
    def get_power(dev):
        return dev.get_property_by(11, 2)[0]["value"]  # 获取功率值
    for dev, dev_name in zip(dev_list, dev_names):
        power = get_power(dev)
        write_to_influxdb(power, dev_name)