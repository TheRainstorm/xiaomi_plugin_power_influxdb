from miio import DeviceFactory
from influxdb import InfluxDBClient
import time
import os

dev = None  # 全局设备变量

DEVICE_IP = ""
DEVICE_TOKEN = ""
INFLUX_HOST = ""
INFLUX_PORT = 0
INFLUX_USER = ""
INFLUX_PASS = ""
INFLUX_DB = ""
DEBUG = False  # 是否开启调试模式

def read_env():
    global DEVICE_IP, DEVICE_TOKEN, INFLUX_HOST, INFLUX_PORT, INFLUX_USER, INFLUX_PASS, INFLUX_DB, DEBUG
    try:
        DEVICE_IP = os.environ["DEVICE_IP"]
        DEVICE_TOKEN = os.environ["DEVICE_TOKEN"]
        INFLUX_HOST = os.environ["INFLUX_HOST"]
        INFLUX_PORT = int(os.environ["INFLUX_PORT"])
        INFLUX_USER = os.environ["INFLUX_USER"]
        INFLUX_PASS = os.environ["INFLUX_PASS"]
        INFLUX_DB = os.environ["INFLUX_DB"]
        DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    except KeyError as e:
        print(f"环境变量缺失: {e}")
        raise RuntimeError("请确保所有环境变量已设置")
    print(f"读取环境变量: DEVICE_IP={DEVICE_IP}, DEVICE_TOKEN={DEVICE_TOKEN[:5]}xxx{DEVICE_TOKEN[-5:]}, INFLUX_HOST={INFLUX_HOST}, INFLUX_PORT={INFLUX_PORT}, INFLUX_USER={INFLUX_USER}, INFLUX_DB={INFLUX_DB}")

def setup_device():
    global dev
    dev = DeviceFactory.create(DEVICE_IP, DEVICE_TOKEN)

def get_power():
    return dev.get_property_by(11, 2)[0]["value"]  # 获取功率值

def write_to_influxdb(power):
    json_body = [{
        "measurement": "power_consumption",
        "tags": {"device": "smart_plug"},
        "fields": {"value": power}
    }]
    client = InfluxDBClient(INFLUX_HOST, INFLUX_PORT, INFLUX_USER, INFLUX_PASS, INFLUX_DB)
    client.write_points(json_body)
    if DEBUG:
        print(f"写入数据: {power} W")

def task():
    if dev is None:
        print("设备未初始化，正在读取环境变量并设置设备...")
        read_env()
        print("环境变量读取成功，正在初始化设备...")
        print("设备IP:", DEVICE_IP)
        setup_device()  # 初始化设备
        print("设备初始化成功")
    power = get_power()
    write_to_influxdb(power)