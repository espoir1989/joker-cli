import multiprocessing
import os
import logging
from script import run_script

# 用于保存所有任务的状态
tasks = {}

def start_task(task_id, config_file):
    """启动任务"""
    if task_id in tasks and tasks[task_id]['process'].is_alive():
        logging.info(f"任务 {task_id} 已经在运行")
        return False

    stop_event = multiprocessing.Event()
    process = multiprocessing.Process(target=run_script, args=(config_file, stop_event))
    process.start()
    tasks[task_id] = {'process': process, 'stop_event': stop_event}
    logging.info(f"启动任务 {task_id}")
    return True

def stop_task(task_id):
    """停止任务"""
    if task_id in tasks:
        tasks[task_id]['stop_event'].set()
        tasks[task_id]['process'].join()
        del tasks[task_id]
        logging.info(f"停止任务 {task_id}")
        return True
    logging.warning(f"任务 {task_id} 不存在")
    return False

def delete_task(task_id):
    """删除任务"""
    if task_id in tasks:
        stop_task(task_id)  # 确保任务停止
        logging.info(f"删除任务 {task_id}")
        return True
    logging.warning(f"任务 {task_id} 不存在")
    return False

def get_task_status(task_id):
    """获取任务状态"""
    if task_id in tasks:
        process = tasks[task_id]['process']
        status = '运行中' if process.is_alive() else '已停止'
        return status
    return '任务不存在'

