"""
Gap 人际裂隙诊断 - Flask App
评分逻辑与前端 static/js/logic.js 完全一致
"""
from flask import Flask, render_template, request, jsonify, abort
import json
import sqlite3
import os
from datetime import datetime, timezone, timedelta
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = os.environ.get('SECRET_KEY', 'gap-secret-key-2026')

ACCESS_CODE = os.environ.get('ACCESS_CODE', 'gap')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'gapadmin')
DB_PATH = os.path.join(BASE_DIR, 'gap.db')

BJ_TZ = timezone(timedelta(hours=8))

DIM_ORDER = ['criticism', 'indifference', 'narcissism', 'forgetful', 'defensive', 'taking']
DIM_LABELS = {
    'criticism': '谦逊度', 'indifference': '关怀度',
    'narcissism': '自信度', 'forgetful': '细心度',
    'defensive': '开放度', 'taking': '慷慨度'
}
DIM_MAX = {'criticism': 14, 'indifference': 14, 'defensive': 12, 'taking': 12, 'narcissism': 12, 'forgetful': 10}

# ── 前端逻辑.js 完全一致 ───────────────────────────────
# MC[answer_index] → raw increment (负数→0)
MC = [-1, 0, 0, 1, 2]

# dimMap: question_num → dimension name (Q1-Q25, 与 logic.js dimMap 完全一致)
DIM_MAP = {
    1: 'criticism',    2: 'defensive',    3: 'indifference',  4: 'taking',
    5: 'criticism',    6: 'defensive',    7: 'indifference',  8: 'taking',
    9: 'criticism',   10: 'indifference', 11: 'indifference', 12: 'defensive',
   13: 'criticism',   14: 'narcissism',  15: 'narcissism',  16: 'forgetful',
   17: 'forgetful',   18: 'taking',       19: 'narcissism',
   # Q20-Q25: 量表题，原始分(0-6)直接作为维度得分
   20: 'criticism',   21: 'indifference', 22: 'narcissism',
   23: 'forgetful',   24: 'defensive',    25: 'taking',
}
# ──────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            answers TEXT NOT NULL,
            dims TEXT NOT NULL,
            main_dim TEXT,
            health_score INTEGER,
            ip TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('access_code', 'gap')")
    conn.commit()
    conn.close()

init_db()

def calc_dims(answers):
    """与前端 logic.js calcDims() 完全一致的计算逻辑"""
    dims = {d: 0 for d in DIM_ORDER}
    for q, ans in answers.items():
        q = int(q)
        ans = int(ans)
        dim = DIM_MAP.get(q)
        if not dim:
            continue
        if q <= 19:
            # MC题: 取MC[answer]，负数→0
            raw = MC[ans] if 0 <= ans < len(MC) else 0
            dims[dim] += max(0, raw)
        else:
            # 量表题: 原始分(0-6)直接累加
            dims[dim] += max(0, min(ans, 6))
    return dims

def health_of(dims):
    """与前端 logic.js healthOf() 完全一致: 得分越低越健康"""
    h = {}
    for k, v in dims.items():
        mx = DIM_MAX.get(k, 14)
        h[k] = max(0, min(100, round(100 - v / mx * 100)))
    return h

def overall_health(dims):
    """综合健康分，与前端 result.html 显示一致"""
    total = sum(dims.values())
    return max(0, min(100, round(100 - total / 70 * 100)))

def get_access_code():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key='access_code'")
    row = c.fetchone()
    conn.close()
    return row['value'] if row else 'gap'

def set_access_code(code):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO config (key, value, updated_at) VALUES ('access_code', ?, datetime('now'))",
        (code,)
    )
    conn.commit()
    conn.close()

# ══════════════════ 页面路由 ══════════════════

@app.route('/')
def index():
    error = request.args.get('error', '')
    return render_template('index.html', error=error)

@app.route('/test')
def test():
    code = request.args.get('code', '')
    if code != get_access_code():
        return render_template('index.html', error='通行码错误，请重新输入'), 403
    return render_template('test.html', code=code)

@app.route('/result')
def result():
    answers = {}
    for i in range(1, 26):
        val = request.args.get(f'q{i}')
        if val is not None:
            try:
                answers[i] = int(val)
            except:
                answers[i] = 0

    dims = calc_dims(answers)
    h = health_of(dims)
    overall = overall_health(dims)
    main_dim = max(dims, key=dims.get)
    ip = request.remote_addr

    try:
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO submissions (answers, dims, main_dim, health_score, ip) VALUES (?, ?, ?, ?, ?)",
            (json.dumps(answers), json.dumps(dims), main_dim, overall, ip)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB error: {e}")

    return render_template('result.html', answers=answers, dims=dims, health_score=overall, main_dim=main_dim)

# ══════════════════ API ══════════════════

@app.route('/api/verify_code', methods=['GET'])
def api_verify_code():
    code = request.args.get('code', '')
    if code == get_access_code():
        return jsonify({'valid': True})
    return jsonify({'valid': False, 'message': '通行码错误'}), 401

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """看板统计数据"""
    conn = get_db()
    c = conn.cursor()

    c.execute('SELECT COUNT(*) as n FROM submissions')
    total = c.fetchone()['n']

    # 近24小时每小时的提交次数（北京时间）
    now_bj = datetime.now(BJ_TZ)
    hourly = []
    for h in range(24):
        t_start = (now_bj - timedelta(hours=23 - h)).replace(minute=0, second=0, microsecond=0)
        t_end = t_start + timedelta(hours=1)
        utc_start = t_start - timedelta(hours=8)
        utc_end = t_end - timedelta(hours=8)
        c.execute(
            "SELECT COUNT(*) as n FROM submissions WHERE submitted_at >= ? AND submitted_at < ?",
            (utc_start.isoformat(), utc_end.isoformat())
        )
        hourly.append({'hour': t_start.strftime('%H:00'), 'count': c.fetchone()['n']})

    # 最近20条（北京时间）
    c.execute(
        'SELECT id, answers, dims, main_dim, health_score, ip, submitted_at FROM submissions ORDER BY id DESC LIMIT 20'
    )
    rows = c.fetchall()
    recent = []
    for row in rows:
        submitted = row['submitted_at']
        if isinstance(submitted, str):
            try:
                submitted = datetime.fromisoformat(submitted.replace('Z', '+00:00'))
            except:
                submitted = datetime.now(timezone.utc)
        submitted_bj = submitted + timedelta(hours=8)
        dims = {}
        try:
            dims = json.loads(row['dims']) if row['dims'] else {}
        except:
            pass
        recent.append({
            'id': row['id'],
            'main_dim': row['main_dim'],
            'main_dim_label': DIM_LABELS.get(row['main_dim'], row['main_dim'] or '-'),
            'health_score': row['health_score'],
            'dims': dims,
            'ip': row['ip'],
            'submitted_at': submitted_bj.strftime('%m-%d %H:%M')
        })

    # 各维度聚合统计
    dim_sums = defaultdict(int)
    dim_counts = defaultdict(int)
    main_dim_counts = defaultdict(int)
    health_sum = 0

    c.execute('SELECT dims, main_dim, health_score FROM submissions')
    for row in c.fetchall():
        try:
            d = json.loads(row['dims']) if row['dims'] else {}
            for k, v in d.items():
                if k in DIM_ORDER:
                    dim_sums[k] += v
                    dim_counts[k] += 1
        except:
            pass
        if row['main_dim']:
            main_dim_counts[row['main_dim']] += 1
        if row['health_score'] is not None:
            health_sum += row['health_score']

    dim_avg = {d: round(dim_sums[d] / dim_counts[d], 1) if dim_counts[d] > 0 else 0 for d in DIM_ORDER}
    top_main_dim = max(main_dim_counts, key=main_dim_counts.get) if main_dim_counts else None
    avg_health = round(health_sum / total) if total > 0 else 0

    conn.close()

    return jsonify({
        'total': total,
        'dim_avg': dim_avg,
        'dim_counts': dict(dim_counts),
        'top_main_dim': top_main_dim,
        'top_main_dim_label': DIM_LABELS.get(top_main_dim, top_main_dim or '-'),
        'hourly': hourly,
        'recent': recent,
        'current_code': get_access_code(),
        'avg_health': avg_health,
        'main_dim_counts': dict(main_dim_counts),
    })

@app.route('/api/change_code', methods=['POST'])
def api_change_code():
    data = request.get_json()
    admin_pwd = data.get('admin_password', '')
    new_code = data.get('new_code', '').strip()

    if admin_pwd != ADMIN_PASSWORD:
        return jsonify({'success': False, 'message': '管理密码错误'}), 403
    if len(new_code) < 3:
        return jsonify({'success': False, 'message': '通行码至少3个字符'}), 400

    set_access_code(new_code)
    return jsonify({'success': True, 'message': f'通行码已更新为：{new_code}'})

@app.route('/admin')
def admin():
    return render_template('admin.html')

if __name__ == '__main__':
    print(f"Starting Gap app from {BASE_DIR}")
    print(f"DB: {DB_PATH}")
    app.run(host='0.0.0.0', port=5002, debug=False)
