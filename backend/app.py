import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
# Allow requests from your local machine and your upcoming Render frontend URL
CORS(app)

# Automatically switch between Render Cloud DB (PostgreSQL) and local DB (MySQL)
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if DATABASE_URL:
        # Running in Render Cloud (using PostgreSQL)
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        # Running locally (using MySQL)
        import mysql.connector
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD', 'password'),
            database=os.environ.get('DB_NAME', 'todo_db')
        )
        return conn

# Helper function to create the table if it doesn't exist
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    if DATABASE_URL:
        # PostgreSQL syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                completed BOOLEAN DEFAULT FALSE
            );
        ''')
    else:
        # MySQL syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                completed BOOLEAN DEFAULT FALSE
            );
        ''')
    conn.commit()
    cursor.close()
    conn.close()

# Initialize the database table right away
try:
    init_db()
except Exception as e:
    print(f"Database initialization error: {e}")

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DATABASE_URL:
            # PostgreSQL fetch
            cursor.execute('SELECT id, title, completed FROM tasks ORDER BY id ASC;')
            rows = cursor.fetchall()
            tasks = [{'id': row[0], 'title': row[1], 'completed': row[2]} for row in rows]
        else:
            # MySQL fetch
            cursor.execute('SELECT id, title, completed FROM tasks ORDER BY id ASC;')
            rows = cursor.fetchall()
            tasks = [{'id': row[0], 'title': row[1], 'completed': bool(row[2])} for row in rows]
            
        cursor.close()
        conn.close()
        return jsonify(tasks), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DATABASE_URL:
            # PostgreSQL insert with returning ID
            cursor.execute('INSERT INTO tasks (title) VALUES (%s) RETURNING id;', (data['title'],))
            task_id = cursor.fetchone()[0]
        else:
            # MySQL insert
            cursor.execute('INSERT INTO tasks (title) VALUES (%s);', (data['title'],))
            task_id = cursor.lastrowid
            
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'id': task_id, 'title': data['title'], 'completed': False}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use port assigned by Render or default to 5000 locally
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)