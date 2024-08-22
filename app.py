from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import json
import logging
from task_manager import start_task, stop_task, delete_task, get_task_status

app = Flask(__name__)

@app.route('/')
def index():
    task_files = [f for f in os.listdir('tasks') if f.endswith('.json')]
    task_list = []
    for file_name in task_files:
        task_id = file_name.split('.')[0]
        task_list.append({
            'id': task_id,
            'name': f"任务 {task_id}",
            'file': file_name,
            'status': get_task_status(task_id)
        })
    return render_template('index.html', tasks=task_list)

@app.route('/start/<task_id>', methods=['POST'])
def start(task_id):
    config_file = f'tasks/{task_id}.json'
    if os.path.exists(config_file):
        if start_task(task_id, config_file):
            return redirect(url_for('index'))
        else:
            return "任务已经在运行", 400
    return "配置文件不存在", 404

@app.route('/stop/<task_id>', methods=['POST'])
def stop(task_id):
    if stop_task(task_id):
        return redirect(url_for('index'))
    return "任务不存在", 404

@app.route('/delete/<task_id>', methods=['POST'])
def delete(task_id):
    if delete_task(task_id):
        os.remove(f'tasks/{task_id}.json')
        return redirect(url_for('index'))
    return "任务不存在", 404

@app.route('/logs/<task_id>')
def logs(task_id):
    log_file = f'logs/{task_id}.json'
    if os.path.exists(log_file):
        return send_file(log_file, mimetype='text/plain')
    return "日志文件不存在", 404

@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        data = request.form
        task_id = str(len(os.listdir('tasks')) + 1)
        config = {
            'authorization': data['authorization'],
            'cookie': data['cookie'],
            'cf_response': data['cf_response']
        }
        config_file = f'tasks/{task_id}.json'
        with open(config_file, 'w') as file:
            json.dump(config, file)
        return redirect(url_for('index'))
    return render_template('add_task.html')

if __name__ == '__main__':
    if not os.path.exists('tasks'):
        os.makedirs('tasks')
    if not os.path.exists('logs'):
        os.makedirs('logs')
    app.run(host='0.0.0.0',port=3303,debug=True)



