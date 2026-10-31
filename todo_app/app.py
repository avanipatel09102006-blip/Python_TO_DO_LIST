"""To-Do List: Flask REST API + SQLite."""
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, render_template, request

DB_PATH = Path(__file__).with_name("todo.db")
PRIORITIES = ("low", "medium", "high")
app = Flask(__name__)


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'medium',
                due_date TEXT,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
        )


def clean_title(value):
    value = (value or "").strip()
    return value[:120] if value else None


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/tasks")
def list_tasks():
    flt = request.args.get("filter", "all")
    q = request.args.get("q", "").strip()
    sql, args = "SELECT * FROM tasks WHERE 1=1", []
    if flt == "active":
        sql += " AND done=0"
    elif flt == "done":
        sql += " AND done=1"
    if q:
        sql += " AND title LIKE ?"
        args.append(f"%{q}%")
    sql += """ ORDER BY done ASC,
        CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
        due_date IS NULL, due_date, id DESC"""
    with db() as conn:
        tasks = [dict(r) for r in conn.execute(sql, args)]
        total, done = conn.execute("SELECT COUNT(*), COALESCE(SUM(done),0) FROM tasks").fetchone()
    return jsonify(tasks=tasks, total=total, done=done)


@app.post("/api/tasks")
def add_task():
    data = request.get_json(silent=True) or {}
    title = clean_title(data.get("title"))
    priority = data.get("priority", "medium")
    if not title:
        return jsonify(error="Task title is required"), 400
    if priority not in PRIORITIES:
        return jsonify(error="Invalid priority"), 400
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, priority, due_date) VALUES (?,?,?)",
            (title, priority, data.get("due_date") or None),
        )
    return jsonify(id=cur.lastrowid), 201


@app.patch("/api/tasks/<int:task_id>")
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    fields, args = [], []
    if "title" in data:
        title = clean_title(data["title"])
        if not title:
            return jsonify(error="Task title is required"), 400
        fields.append("title=?"); args.append(title)
    if "done" in data:
        fields.append("done=?"); args.append(1 if data["done"] else 0)
    if "priority" in data:
        if data["priority"] not in PRIORITIES:
            return jsonify(error="Invalid priority"), 400
        fields.append("priority=?"); args.append(data["priority"])
    if not fields:
        return jsonify(error="Nothing to update"), 400
    with db() as conn:
        cur = conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id=?", (*args, task_id))
    if cur.rowcount == 0:
        return jsonify(error="Task not found"), 404
    return jsonify(ok=True)


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    with db() as conn:
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    return jsonify(ok=True)


@app.delete("/api/tasks/completed")
def clear_completed():
    with db() as conn:
        conn.execute("DELETE FROM tasks WHERE done=1")
    return jsonify(ok=True)


init_db()
if __name__ == "__main__":
    app.run(debug=True)
