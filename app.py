import argparse
import mariadb
import sys
import os
from flask import Flask, request, jsonify, make_response
from werkzeug.serving import make_server

app = Flask(__name__)
db_config = {}

def get_db_connection():
    try:
        return mariadb.connect(**db_config)
    except mariadb.Error:
        return None

def format_response(data_list, columns):
    accept = request.headers.get('Accept', '')
    if 'text/html' in accept:
        html = "<!DOCTYPE html><html><head><meta charset=\"UTF-8\"><title>Task Tracker</title></head><body><table border='1'><tr>"
        for col in columns: html += f"<th>{col}</th>"
        html += "</tr>"
        for row in data_list:
            html += "<tr>"
            for col in columns: html += f"<td>{row.get(col, '')}</td>"
            html += "</tr>"
        html += "</table></body></html>"
        response = make_response(html)
        response.headers['Content-Type'] = 'text/html'
        return response
    return jsonify(data_list)

@app.route('/health/alive', methods=['GET'])
def health_alive():
    return "OK", 200

@app.route('/health/ready', methods=['GET'])
def health_ready():
    conn = get_db_connection()
    if conn:
        conn.close()
        return "OK", 200
    return "Database connection failed", 500

@app.route('/', methods=['GET'])
def root():
    html = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>API Endpoints</title></head><body><h1>Список ендпоінтів бізнес-логіки:</h1><ul><li>GET /tasks — вивести усі задачі</li><li>POST /tasks — створити нову задачу</li><li>POST /tasks/&lt;id&gt;/done — змінити статус задачі на виконано</li></ul></body></html>"""
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html'
    return response

@app.route('/tasks', methods=['GET'])
def get_tasks():
    conn = get_db_connection()
    if not conn: return "Database error", 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, title, status, created_at FROM tasks")
    tasks = cursor.fetchall()
    conn.close()
    return format_response(tasks, ['id', 'title', 'status', 'created_at'])

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json() if request.is_json else request.form
    title = data.get('title')
    if not title: return "Title is required", 400
    conn = get_db_connection()
    if not conn: return "Database error", 500
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO tasks (title, status) VALUES (?, ?)", (title, 'pending'))
        conn.commit()
    except mariadb.Error:
        conn.close()
        return "Error creating task", 500
    conn.close()
    return "Task created successfully", 201

@app.route('/tasks/<int:task_id>/done', methods=['POST'])
def mark_task_done(task_id):
    conn = get_db_connection()
    if not conn: return "Database error", 500
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", ('done', task_id))
        conn.commit()
    except mariadb.Error:
        conn.close()
        return "Error updating task", 500
    conn.close()
    return "Task marked as done", 200

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-host', required=True)
    parser.add_argument('--db-user', required=True)
    parser.add_argument('--db-password', required=True)
    parser.add_argument('--db-name', required=True)
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--host', default='127.0.0.1')
    args = parser.parse_args()
    
    db_config['host'] = args.db_host
    db_config['user'] = args.db_user
    db_config['password'] = args.db_password
    db_config['database'] = args.db_name
    
    listen_fds = os.environ.get('LISTEN_FDS')
    if listen_fds and int(listen_fds) > 0:
        server = make_server(args.host, args.port, app, fd=3)
        server.serve_forever()
    else:
        app.run(host=args.host, port=args.port)