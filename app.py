"""
测测你的人性弱点 (Weak) - Flask App
基于卡内基《人性的弱点》的人际弱点测试
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'weak-secret-key-2026')

# Load config
WEEK_CODE = os.environ.get('WEEK_CODE', 'weak2026')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'weakadmin')

def get_db():
    conn = sqlite3.connect('weak.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS test_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            answers TEXT,
            scores TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS weekly_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_code TEXT UNIQUE,
            week_number INTEGER,
            year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    code = request.args.get('code', '')
    return render_template('test.html', code=code)

@app.route('/result')
def result():
    answers = {}
    for i in range(1, 26):
        val = request.args.get(f'q{i}')
        if val is not None:
            answers[i] = int(val)
    
    # Calculate scores
    scores = calculate_scores(answers)
    
    # Save to DB
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO test_submissions (answers, scores) VALUES (?, ?)',
              (json.dumps(answers), json.dumps(scores)))
    conn.commit()
    conn.close()
    
    return render_template('result.html', answers=answers, scores=scores)

def calculate_scores(answers):
    """Calculate dimension scores based on answers"""
    # Score mapping for each question
    # Each option maps to -1, 0, 1, or 2 points
    score_map = {
        1: [2, 0, 1, 2],   # criticism
        2: [0, 1, 2, 1],   # indifference
        3: [0, 2, 0, -1],  # narcissism
        4: [0, 2, 2, -1],  # forgetful
        5: [2, 0, 1, 0],   # criticism
        6: [-1, 2, 1, 0],  # defensive
        7: [0, 2, 0, 2],   # taking
        8: [0, 1, 2, 1],   # indifference
        9: [0, 1, 2, -1],  # narcissism
        10: [2, 0, 1, -1], # criticism
        11: [-1, 2, 1, 0], # forgetful
        12: [0, 2, 2, 1],  # defensive
        13: [0, 2, 1, 0],  # indifference
        14: [0, 0, 2, 1],  # narcissism
        15: [0, 2, 0, 1],  # taking
        16: [2, 0, 1, -1], # criticism
        17: [-1, 0, 2, 1], # forgetful
        18: [-1, 2, 1, 0], # defensive
        19: [0, 1, 2, 2],  # indifference
        20: [-1, 1, 1, 0], # narcissism
        21: [0, 2, 1, -1], # taking
        22: [0, 0, 0, 0],  # balance question (no score)
        23: [-1, 2, 1, 0], # forgetful
        24: [-1, 2, 2, 1], # defensive
        25: [-1, 2, 0, 1]   # taking
    }
    
    # Dimension mapping
    dim_map = {
        1: 'criticism', 2: 'indifference', 3: 'narcissism', 4: 'forgetful',
        5: 'criticism', 6: 'defensive', 7: 'taking', 8: 'indifference',
        9: 'narcissism', 10: 'criticism', 11: 'forgetful', 12: 'defensive',
        13: 'indifference', 14: 'narcissism', 15: 'taking', 16: 'criticism',
        17: 'forgetful', 18: 'defensive', 19: 'indifference', 20: 'narcissism',
        21: 'taking', 23: 'forgetful', 24: 'defensive', 25: 'taking'
    }
    
    scores = {dim: 0 for dim in ['criticism', 'indifference', 'narcissism', 'forgetful', 'defensive', 'taking']}
    
    for q_num, answer in answers.items():
        if q_num in score_map and q_num in dim_map:
            score = score_map[q_num][answer]
            dim = dim_map[q_num]
            scores[dim] += score
    
    return scores

@app.route('/api/verify_week_code')
def verify_week_code():
    code = request.args.get('code', '')
    if code == WEEK_CODE or code == 'demo':
        return jsonify({'valid': True, 'message': '验证成功'})
    return jsonify({'valid': False, 'message': '通行码错误'})

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/api/stats')
def stats():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) as total FROM test_submissions')
    total = c.fetchone()['total']
    conn.close()
    return jsonify({'total': total})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002, debug=True)
