import time
import logging
import json
import os
from curl_cffi import requests
from requests.exceptions import RequestException
from curl_cffi.curl import CurlError
from multiprocessing import Event

def setup_logger(task_id):
    """
    配置日志记录器以输出到特定的文件。
    """
    logger = logging.getLogger(f"task_{task_id}")
    handler = logging.FileHandler(f'logs/{task_id}.json')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

# 初始化全局 pow_id 变量
pow_id = ""

def run_script(config_file, stop_event):
    """
    根据配置文件运行任务，并在停止事件触发时停止任务。
    """
    global pow_id  # 使用全局变量 pow_id
    task_id = os.path.splitext(os.path.basename(config_file))[0]  # 从配置文件名中提取 task_id

    logger = setup_logger(task_id)  # 使用从文件名中提取的任务ID设置日志记录器

    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
        return

    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'authorization': config.get('authorization'),
        'cookie': config.get('cookie'),
        'origin': 'https://blockjoker.org',
        'priority': 'u=1, i',
        'referer': 'https://blockjoker.org/home',
        'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
    }

    post_data = {
        "cf_response": config.get('cf_response')
    }


    while not stop_event.is_set():
        try:
            logger.info("开始 POST 请求")
            response = requests.post('https://blockjoker.org/api/v2/missions', headers=headers, json=post_data)
            response.raise_for_status()
            data = response.json()
            logger.info(f"POST 响应: {data}")

            # 处理数据
            result = data.get('result', {})
            payload = result.get('payload')
            require = result.get('require')

            if payload and require:
                logger.info("开始 GET 请求")
                nonce = get_nonce(payload, require, headers)
                if nonce:
                    logger.info(f"获取到 nonce: {nonce}")
                    new_pow_id = post_nonce(nonce, headers, logger)
                    if new_pow_id:
                        pow_id = new_pow_id  # 更新 pow_id
                else:
                    logger.warning("未能获取到 nonce")
            else:
                logger.warning("POST 请求返回的数据不完整")
        except (RequestException, CurlError) as e:
            logger.error(f"请求失败: {e}")
            time.sleep(5)  # 等待后重试

def get_nonce(payload, require, headers):
    """
    发起 GET 请求获取 nonce 值。
    """
    url = f"http://127.0.0.1:8080/api/msg?data={payload}&thnum=4&prifix={require}"
    start_time = int(time.time())
    attempt = 0

    while attempt < 3:
        attempt += 1
        try:
            logging.info("开始 GET 请求")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            elapsed_time = int(time.time()) - start_time
            logging.info(f'耗时：{elapsed_time}s')

            nonce = data.get('nonce')
            if nonce:
                return nonce
            else:
                logging.warning("JSON 响应中缺少 'nonce'")
                return None
        except (RequestException, CurlError, ValueError) as e:
            logging.error(f"请求失败或解析错误: {e}")
            time.sleep(1)  # 等待后重试

    return None

def post_nonce(nonce, headers, logger):
    """
    发起 POST 请求提交 nonce，并获取新的 pow_id。
    """
    global pow_id
    url = 'https://blockjoker.org/api/v2/missions/nonce'
    data = {
        'nonce': nonce,
        'pow_id': pow_id
    }

    attempt = 0
    while attempt < 3:
        attempt += 1
        try:
            logger.info("开始 POST 请求")
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            logger.info(f"POST 响应内容: {response.text}")
            json_response = response.json()
            result = json_response.get('result')

            if result:
                new_pow_id = result[0].get('pow_id')
                if new_pow_id:
                    logger.info(f"pow_id 已更新为: {new_pow_id}")
                    return new_pow_id  # 返回新的 pow_id
                else:
                    logger.warning("result 中未包含 pow_id")
            else:
                logger.warning("result 为空，pow_id 未更新")
            break
        except (RequestException, CurlError) as e:
            logger.error(f"请求失败: {e}")
            time.sleep(1)  # 等待后重试
    return None

