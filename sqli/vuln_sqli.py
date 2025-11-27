import sqlite3
import time
from flask import Flask, request, render_template_string, redirect, url_for, g
import re

app = Flask(__name__)

# --- DATABASE CONFIG ---
DATABASE = ':memory:'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, check_same_thread=False)
        # FIX: Sleep function now returns 1 (True) after sleeping.
        # Old: lambda s: time.sleep(float(s)) -> Returns None -> Query becomes False -> No results shown.
        db.create_function("sleep", 1, lambda s: (time.sleep(float(s)) is None) and 1)
        try:
            cur = db.cursor()
            cur.execute("SELECT count(*) FROM users")
        except:
            init_db(db)
    db.row_factory = sqlite3.Row
    return db

def init_db(db):
    c = db.cursor()
    # Users
    c.execute('''CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)''')
    c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 's3cr3t_P@ssw0rd', 'admin')")
    c.execute("INSERT INTO users (username, password, role) VALUES ('user', '123456', 'user')")
    
    # Products (Note: 3 main display columns to match Level 9)
    c.execute('''CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, description TEXT)''')
    c.execute("INSERT INTO products (name, price, description) VALUES ('Quantum Core', 500, 'Powerful CPU')")
    c.execute("INSERT INTO products (name, price, description) VALUES ('Plasma Ray', 1200, 'Weapon of mass destruction')")
    c.execute("INSERT INTO products (name, price, description) VALUES ('Stealth Chip', 300, 'Invisibility module')")
    
    # Secrets
    c.execute('''CREATE TABLE secrets (id INTEGER PRIMARY KEY, flag TEXT)''')
    c.execute("INSERT INTO secrets (flag) VALUES ('FLAG{SQLI_MASTER_CLASS}')")
    
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- THEME & TEMPLATES ---
base_layout = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQLi DOJO | Cyber Lab</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Source+Code+Pro:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Rajdhani', sans-serif; background-color: #020617; color: #fbbf24; background-image: linear-gradient(rgba(245, 158, 11, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(245, 158, 11, 0.1) 1px, transparent 1px); background-size: 40px 40px; }
        .mono-font { font-family: 'Source Code Pro', monospace; }
        .holo-text { text-shadow: 0 0 5px #f59e0b, 0 0 10px #f59e0b; }
        .holo-box { background: rgba(69, 26, 3, 0.6); border: 1px solid #f59e0b; box-shadow: 0 0 15px rgba(245, 158, 11, 0.2), inset 0 0 20px rgba(245, 158, 11, 0.1); backdrop-filter: blur(4px); }
        input, textarea, select { background-color: #0f172a; color: #fcd34d; border: 1px solid #92400e; font-family: 'Source Code Pro', monospace; }
        input:focus { outline: none; border-color: #f59e0b; box-shadow: 0 0 10px #f59e0b; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-thumb { background: #b45309; border-radius: 4px; }
    </style>
</head>
<body class="min-h-screen flex flex-col overflow-x-hidden">
    <nav class="bg-slate-950/90 border-b border-amber-800 p-4 sticky top-0 z-50 backdrop-blur-md">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-3xl font-bold holo-text tracking-widest">[SQLi_DOJO]</a>
            <a href="/reset" class="text-red-400 border border-red-900/50 bg-red-900/20 px-4 py-1 rounded hover:shadow-[0_0_10px_rgba(248,113,113,0.5)]">// RESET_DB</a>
        </div>
    </nav>
    <div class="container mx-auto flex-grow flex flex-col md:flex-row mt-8 gap-6 px-4 mb-10">
        <aside class="md:w-72 flex-shrink-0">
            <div class="holo-box p-5 rounded-lg h-full">
                <h3 class="text-amber-300 uppercase text-sm font-bold mb-4 border-b border-amber-800 pb-2">Modules</h3>
                <div class="space-y-1">
                {% for i in range(1, 11) %}
                <a href="/level{{i}}" class="block px-3 py-2 text-sm rounded transition-all duration-200 mono-font {{ 'bg-amber-900/50 text-white border-l-4 border-amber-500' if active_level == i else 'text-slate-400 hover:text-amber-200 hover:bg-amber-900/20' }}">
                    Level {{ '%02d' % i }} :: {{ titles[i-1] }}
                </a>
                {% endfor %}
                </div>
            </div>
        </aside>
        <main class="flex-1 relative">
            <div class="mb-6">
                <h1 class="text-5xl font-bold text-white drop-shadow-[0_0_5px_rgba(255,255,255,0.5)]">{{ current_title }}</h1>
                <p class="text-slate-300 mono-font border-l-2 border-amber-600 pl-4 py-1 mt-4 bg-gradient-to-r from-amber-900/20 to-transparent">
                    <span class="text-amber-500 font-bold">Briefing:</span> {{ description }}
                </p>
            </div>
            <div class="holo-box p-8 min-h-[400px] relative rounded-lg overflow-hidden flex flex-col">
                {{ content | safe }}
                {% if query_log %}
                <div class="mt-auto pt-6 border-t border-amber-900/50">
                    <div class="text-xs text-slate-500 font-mono mb-1">EXECUTED QUERY LOG:</div>
                    <code class="block bg-black p-3 rounded border border-amber-900 text-amber-500 font-mono text-sm break-all">{{ query_log }}</code>
                </div>
                {% endif %}
            </div>
        </main>
    </div>
</body>
</html>
"""

titles = [
    "Login Bypass (String)", "Login Bypass (Integer)", "UNION Attack", "Error Based",
    "Boolean Blind", "Time Based Blind", "Filter Bypass (Space)", "Second Order",
    "WAF Bypass", "Stacked Queries"
]

def render_page(level_id, description, content, query_log=None, **kwargs):
    return render_template_string(base_layout, active_level=level_id, titles=titles, current_title=titles[level_id-1], description=description, content=render_template_string(content, **kwargs), query_log=query_log)

@app.route('/')
def index(): return redirect('/level1')

@app.route('/reset')
def reset():
    db = get_db()
    c = db.cursor()
    c.executescript("DROP TABLE IF EXISTS users; DROP TABLE IF EXISTS products; DROP TABLE IF EXISTS secrets;")
    init_db(db)
    return redirect('/')

# --- LEVELS ---

@app.route('/level1', methods=['GET', 'POST'])
def level1():
    query_log = None
    msg = ""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        # VULN: String concat
        sql = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        query_log = sql
        try:
            cur = get_db().cursor()
            cur.execute(sql)
            if cur.fetchone(): msg = "<div class='text-green-400 text-2xl font-bold'>ACCESS GRANTED</div>"
            else: msg = "<div class='text-red-500 font-bold'>ACCESS DENIED</div>"
        except Exception as e: msg = f"<div class='text-red-500'>SQL ERROR: {e}</div>"

    content = """
    <form method="POST" class="max-w-md mx-auto mt-10">
        <label class="block text-amber-500 mb-1 font-bold">USERNAME</label>
        <input type="text" name="username" class="w-full p-2 mb-4 rounded" placeholder="admin">
        <label class="block text-amber-500 mb-1 font-bold">PASSWORD</label>
        <input type="password" name="password" class="w-full p-2 mb-6 rounded" placeholder="******">
        <button class="bg-amber-600 text-black px-6 py-2 font-bold w-full hover:bg-amber-500">LOGIN</button>
    </form>
    <div class="mt-8 text-center">{{ msg|safe }}</div>
    """
    return render_page(1, "Objective: Login as Admin without password. (String Injection)", content, query_log, msg=msg)

@app.route('/level2')
def level2():
    id_param = request.args.get('id', '1')
    sql = f"SELECT name, price FROM products WHERE id = {id_param}"
    try:
        cur = get_db().cursor()
        cur.execute(sql)
        items = cur.fetchall()
    except: items = []
    content = """
    <div class="text-center mb-6">
        <form method="GET" class="inline-flex shadow-lg"><span class="p-2 border border-amber-800 bg-amber-900/50">ID:</span><input name="id" value="{{ id_param }}" class="w-24 p-2 text-center bg-slate-900 border-amber-800"><button class="bg-amber-700 px-4 py-2 text-black font-bold">GO</button></form>
    </div>
    <div class="grid grid-cols-2 gap-4">{% for item in items %}<div class="border border-amber-800 p-4"><h3 class="font-bold text-white">{{ item['name'] }}</h3><div class="text-amber-500">{{ item['price'] }} $</div></div>{% endfor %}</div>
    """
    return render_page(2, "Objective: Display all products. (Integer Injection)", content, sql, items=items, id_param=id_param)

@app.route('/level3')
def level3():
    search = request.args.get('search', '')
    results = []
    # VULN: UNION Injection
    sql = f"SELECT name, description, price FROM products WHERE name LIKE '%{search}%'"
    if search:
        try:
            cur = get_db().cursor()
            cur.execute(sql)
            results = cur.fetchall()
        except Exception as e: results = [("SQL Error", str(e), 0)]
    content = """
    <form method="GET" class="flex gap-2 mb-8"><input type="text" name="search" value="{{ search }}" class="flex-1 p-3 bg-slate-900" placeholder="Search..."><button class="bg-amber-600 px-6 font-bold text-black">SCAN</button></form>
    <div class="space-y-2">{% for r in results %}<div class="p-2 border-l-2 border-amber-500 bg-slate-900/50">{{ r[0] }} :: {{ r[1] }}</div>{% endfor %}</div>
        """
    return render_page(3, "Objective: Extract Flag from 'secrets' table using UNION.", content, sql, results=results, search=search)

@app.route('/level4')
def level4():
    # FIX: Use string context to easily trigger syntax errors
    id_param = request.args.get('uuid', 'user-001')
    error_msg = None
    success_signal = False
    
    # Query search by string
    sql = f"SELECT * FROM users WHERE username = '{id_param}'" 
    
    try:
        cur = get_db().cursor()
        cur.execute(sql)
        cur.fetchall()
    except Exception as e:
        error_msg = str(e)
        # If there's a SQL syntax error, consider exploitation successful
        if "unrecognized token" in error_msg or "syntax" in error_msg.lower() or "unterminated" in error_msg.lower():
            success_signal = True

    content = """
    <div class="text-center max-w-lg mx-auto">
        <h2 class="text-xl mb-6 text-amber-300">USER UUID LOOKUP</h2>
        <form method="GET" class="mb-8">
            <input name="uuid" value="{{ id_param }}" class="w-full p-2 text-center bg-slate-900 border-amber-800" placeholder="Enter UUID">
            <button class="bg-amber-700 px-4 py-2 font-bold text-black mt-2 w-full">CHECK SYSTEM</button>
        </form>
        
        {% if success_signal %}
        <div class="mb-4 p-4 border-2 border-green-500 bg-green-900/30 text-green-400 font-bold text-xl animate-pulse">
            [+] VULNERABILITY CONFIRMED!<br>Database returned a syntax error.
        </div>
        {% endif %}

        {% if error_msg %}
        <div class="p-4 border border-red-500 bg-red-900/20 text-red-400 font-mono text-left">
            <div class="font-bold border-b border-red-500/50 mb-2">DB_DEBUG_LOG:</div>
            {{ error_msg }}
        </div>
        {% endif %}
    </div>
    """
    return render_page(4, "Objective: Trigger database syntax errors.", content, sql, id_param=id_param, error_msg=error_msg, success_signal=success_signal)

@app.route('/level5')
def level5():
    username = request.args.get('u', '')
    
    # FIX: Block direct 'admin' input at Python code level
    # Force user to use injection like: admin' AND 1=1-- 
    if username.strip() == 'admin':
        status = "<span class='text-red-500 font-bold'>[ DIRECT ACCESS BLOCKED BY IPS ]</span>"
        sql = "BLOCKED: Direct 'admin' string not allowed."
    else:
        sql = f"SELECT * FROM users WHERE username = '{username}'"
        exists = False
        try:
            cur = get_db().cursor()
            cur.execute(sql)
            if cur.fetchone(): exists = True
        except: pass
        
        status = "<span class='text-green-400 font-bold'>[ USER FOUND ]</span>" if exists else "<span class='text-slate-500'>[ NOT FOUND ]</span>"

    content = """
    <div class="text-center mt-10 max-w-lg mx-auto">
        <div class="border border-amber-500/30 p-8 bg-slate-900/50 rounded">
            <h2 class="text-2xl mb-6 text-amber-400">Blind Verifier</h2>
            <form method="GET" class="mb-8">
                <input name="u" value="{{ username }}" class="p-2 w-full mb-2 bg-black text-center border-amber-800" placeholder="Username">
                <button class="bg-amber-600 px-8 py-2 font-bold text-black w-full">VERIFY</button>
            </form>
            <div class="text-3xl font-mono tracking-wider">{{ status|safe }}</div>
        </div>
    </div>
    """
    return render_page(5, "Objective: Bypass simple filter and confirm 'admin' user exists (Blind).", content, sql, username=username, status=status)

@app.route('/level6')
def level6():
    search = request.args.get('q', '')
    start_time = time.time()
    results = []
    
    # Logic: Empty search doesn't query to save resources
    # Only query when there's search (or payload)
    if search:
        # VULN: Time Based Blind
        sql = f"SELECT * FROM products WHERE name = '{search}'"
        try:
            cur = get_db().cursor()
            cur.execute(sql)
            results = cur.fetchall()
        except: pass
    
    duration = time.time() - start_time
    # Only show time if query takes more than 0.1s (abnormal delay or user testing)
    msg = f"{duration:.2f}s" if duration > 0.1 else "0.00s"
    
    status_class = "text-green-500 font-bold border-green-500" if duration > 2 else "text-slate-600 border-slate-800"

    content = """
    <div class="text-center max-w-xl mx-auto">
        <h2 class="text-2xl mb-4 text-white font-light tracking-widest">LATENCY TEST</h2>
        <form method="GET" class="flex shadow-lg">
            <input name="q" value="{{ search }}" class="flex-1 p-3 bg-slate-900 border border-amber-900 focus:border-amber-500 transition-colors" placeholder="Enter payload...">
            <button class="bg-amber-700 hover:bg-amber-600 px-6 py-3 font-bold text-black transition-colors">EXECUTE</button>
        </form>
        
        <div class="mt-8 flex flex-col items-center justify-center">
            <div class="text-xs text-slate-500 uppercase tracking-widest mb-2">Response Time</div>
            <div class="p-4 border-2 {{ status_class }} bg-black font-mono text-3xl min-w-[150px] transition-all duration-300">
                {{ msg }}
            </div>
            {% if duration > 2 %}
            <div class="mt-4 text-green-400 font-mono text-sm animate-pulse">[!] TIMING ATTACK DETECTED [!]</div>
            {% endif %}
        </div>
    </div>
    """
    return render_page(6, "Objective: Make database sleep for 3 seconds.", content, "HIDDEN (Blind)", search=search, msg=msg, status_class=status_class, duration=duration)

@app.route('/level7')
def level7():
    id_param = request.args.get('id', '1')
    item = None
    error = None
    
    # FILTER: Block space characters
    if ' ' in id_param:
        error = "WAF ERROR: Malicious input detected (Space character)."
        sql = "BLOCKED"
    else:
        # Query to get products
        # Products table structure: id, name, price, description
        sql = f"SELECT name, price, description FROM products WHERE id = {id_param}"
        try:
            cur = get_db().cursor()
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                # Convert row to dict for easier display
                item = dict(row)
        except Exception as e: 
            error = f"SQL Error: {str(e)}"

    content = """
    <div class="max-w-2xl mx-auto">
        <div class="text-center mb-8">
            <h2 class="text-xl text-amber-500 font-bold mb-2">SECURE PRODUCT VIEWER</h2>
            <p class="text-slate-400 text-sm">Firewall Rule: <span class="text-red-400 font-mono">Input filtering active</span></p>
        </div>

        <form method="GET" class="flex justify-center mb-10">
            <div class="flex border border-amber-800 rounded overflow-hidden">
                <span class="bg-amber-900/30 text-amber-500 p-3 font-mono border-r border-amber-800">ID=</span>
                <input name="id" value="{{ id_param }}" class="bg-slate-900 text-white p-3 w-64 outline-none font-mono" placeholder="1">
                <button class="bg-amber-700 hover:bg-amber-600 px-6 font-bold text-black">LOAD</button>
            </div>
        </form>

        {% if error %}
        <div class="p-4 bg-red-900/20 border border-red-500 text-red-400 text-center font-mono">
            {{ error }}
        </div>
        {% elif item %}
        <div class="bg-slate-900/50 border border-amber-900/50 p-6 rounded-lg shadow-xl relative overflow-hidden group hover:border-amber-500/50 transition-colors">
            <div class="absolute top-0 right-0 bg-amber-600 text-black text-xs font-bold px-3 py-1">PRODUCT</div>
            <h3 class="text-2xl text-white font-bold mb-2">{{ item['name'] }}</h3>
            <div class="text-amber-400 text-xl font-mono mb-4">${{ item['price'] }}</div>
            <p class="text-slate-400 border-t border-slate-800 pt-4">{{ item['description'] }}</p>
            
            {% if 'FLAG' in item['name']|string or 'FLAG' in item['description']|string %}
            <div class="mt-6 p-4 bg-green-900/30 border border-green-500 text-green-400 font-mono font-bold text-center animate-pulse">
                [SUCCESS] FLAG CAPTURED!
            </div>
            {% endif %}
        </div>
        {% else %}
        <div class="text-center text-slate-500 italic">No product found.</div>
        {% endif %}
    </div>
    """
    return render_page(7, "Objective: Bypass WAF to extract 'flag' from 'secrets' table.", content, sql, id_param=id_param, item=item, error=error)

@app.route('/level8', methods=['GET', 'POST'])
def level8():
    if request.method == 'POST':
        username = request.form.get('username', '')
        # FIX: Block registration with existing 'admin' name
        # Force user to register: admin' -- 
        if username.strip() == 'admin':
             return render_page(8, "Second Order.", f"<div class='text-red-500 text-center font-bold'>ERROR: User 'admin' already exists.</div>", "REGISTER_FAILED")
        
        g.stored_user = username 
        return redirect(url_for('level8', step='view', user=username))

    step = request.args.get('step', 'register')
    stored_user = request.args.get('user', '')
    
    if step == 'register':
        content = """
        <div class="max-w-md mx-auto">
            <h3 class="text-xl mb-4 text-amber-400">Step 1: Register</h3>
            <form method="POST"><input name="username" class="w-full p-3 mb-2 bg-slate-900 border-amber-800" placeholder="Username"><button class="bg-amber-600 w-full py-3 font-bold text-black">REGISTER</button></form>
        </div>
        """
        return render_page(8, "Objective: Gain admin privileges via Second Order injection.", content, "")
    else:
        # VULN: Second order - Data from DB (g.stored_user) reused without filtering
        sql = f"SELECT role FROM users WHERE username = '{stored_user}'"
        role = "guest"
        try:
            cur = get_db().cursor()
            cur.execute(sql)
            res = cur.fetchone()
            if res: role = res[0]
        except Exception as e: role = f"ERROR: {e}"

        content = """
        <div class="max-w-md mx-auto text-center">
            <div class="text-2xl text-white mb-2">User: {{ user }}</div>
            <div class="border-t border-amber-900 pt-2 mt-2">ROLE: <span class="text-red-400 font-bold text-xl">{{ role }}</span></div>
            <div class="mt-6"><a href="/level8" class="text-amber-500 underline">Try again</a></div>
        </div>
        """
        return render_page(8, "Payload Execution.", content, sql, user=stored_user, role=role)

@app.route('/level9')
def level9():
    search = request.args.get('q', '')
    results = []
    
    # FILTER: Regex blocks "UNION SELECT" with whitespace (space, tab, newline)
    if re.search(r'union\s+select', search, re.IGNORECASE):
        msg = "<div class='text-red-500 text-center text-3xl font-bold p-8 border-2 border-red-500 bg-red-900/30'>WAF BLOCKED: 'UNION SELECT'</div>"
        return render_page(9, "WAF Bypass.", msg, "BLOCKED_BY_WAF")

    # FIX: Main query selects 3 columns (name, description, price) to match standard payload (id, flag, 1)
    sql = f"SELECT name, description, price FROM products WHERE name LIKE '%{search}%'"
    try:
        cur = get_db().cursor()
        cur.execute(sql)
        results = cur.fetchall()
    except Exception as e: results = [] # Hide SQL errors

    content = """
    <div class="max-w-lg mx-auto">
        <div class="mb-4 text-red-400 text-center border border-red-900/50 p-2">WAF Active: Keyword filtering enabled</div>
        <form method="GET" class="flex gap-2"><input type="text" name="q" value="{{ search }}" class="flex-1 p-2 bg-slate-900 border-amber-800" placeholder="Search"><button class="bg-amber-600 px-4 font-bold text-black">SEARCH</button></form>
        <ul class="mt-6 space-y-2 font-mono text-amber-200">{% for r in results %}<li class="p-2 bg-slate-900/50">{{ r[0] }} - {{ r[1] }}</li>{% endfor %}</ul>
    </div>
    """
    return render_page(9, "Objective: Bypass WAF keyword filtering.", content, sql, search=search, results=results)

@app.route('/level10', methods=['GET', 'POST'])
def level10():
    msg = ""
    query_log = ""
    if request.method == 'POST':
        user_input = request.form.get('id', '')
        sql = f"SELECT * FROM users WHERE id = {user_input}"
        query_log = sql
        try:
            cur = get_db().cursor()
            cur.executescript(sql) # VULN: Stacked Queries
            # Check if pwned
            cur.execute("SELECT password FROM users WHERE username='admin'")
            if cur.fetchone()[0] == 'pwned': msg = "<div class='text-green-400 text-2xl font-bold'>SYSTEM PWNED! Password changed.</div>"
            else: msg = "<div class='text-slate-400 italic'>Query executed. Admin password unchanged.</div>"
        except Exception as e: msg = f"<div class='text-red-500'>Error: {e}</div>"

    content = """
    <div class="text-center max-w-lg mx-auto">
        <h2 class="text-2xl mb-4 text-red-500 font-bold">STACKED QUERY ADMIN RESET</h2>
        <form method="POST"><input name="id" class="w-full p-3 mb-2 bg-slate-900 border-red-900" placeholder="User ID"><button class="bg-red-700 text-white w-full py-3 font-bold">EXECUTE</button></form>
        <div class="mt-8 border p-4 border-amber-900 bg-black/80 min-h-[60px] flex items-center justify-center">{{ msg|safe }}</div>
    </div>
    """
    return render_page(10, "Objective: Use semicolon ; to execute UPDATE command on admin password.", content, query_log, msg=msg)

if __name__ == '__main__':
    app.run(debug=True, port=1111)