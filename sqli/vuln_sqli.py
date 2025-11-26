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
        # Custom function for Time-based SQLi
        db.create_function("sleep", 1, lambda s: time.sleep(float(s)))
        
        # Init Data if empty
        try:
            cur = db.cursor()
            cur.execute("SELECT count(*) FROM users")
        except:
            init_db(db)
            
    db.row_factory = sqlite3.Row # Allow accessing columns by name
    return db

def init_db(db):
    c = db.cursor()
    # Users
    c.execute('''CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)''')
    c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 's3cr3t_P@ssw0rd', 'admin')")
    c.execute("INSERT INTO users (username, password, role) VALUES ('user', '123456', 'user')")
    
    # Products
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
    <title>SQLi DOJO | Data Breach Lab</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Source+Code+Pro:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { 
            font-family: 'Rajdhani', sans-serif; 
            background-color: #020617; /* Slate 950 */
            color: #fbbf24; /* Amber 400 */
            background-image: 
                linear-gradient(rgba(245, 158, 11, 0.1) 1px, transparent 1px), 
                linear-gradient(90deg, rgba(245, 158, 11, 0.1) 1px, transparent 1px);
            background-size: 40px 40px;
        }
        
        .mono-font { font-family: 'Source Code Pro', monospace; }
        
        /* Holographic Effects */
        .holo-text { text-shadow: 0 0 5px #f59e0b, 0 0 10px #f59e0b; }
        .holo-box { 
            background: rgba(69, 26, 3, 0.6); 
            border: 1px solid #f59e0b; 
            box-shadow: 0 0 15px rgba(245, 158, 11, 0.2), inset 0 0 20px rgba(245, 158, 11, 0.1); 
            backdrop-filter: blur(4px);
        }
        
        input, textarea, select { 
            background-color: #0f172a; 
            color: #fcd34d; 
            border: 1px solid #92400e; 
            font-family: 'Source Code Pro', monospace;
        }
        input:focus, textarea:focus, select:focus { 
            outline: none; 
            border-color: #f59e0b; 
            box-shadow: 0 0 10px #f59e0b; 
        }
        
        .scan-line {
            width: 100%;
            height: 2px;
            background: rgba(251, 191, 36, 0.5);
            animation: scan 3s linear infinite;
        }
        @keyframes scan {
            0% { transform: translateY(0); opacity: 0; }
            50% { opacity: 1; }
            100% { transform: translateY(400px); opacity: 0; }
        }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #020617; }
        ::-webkit-scrollbar-thumb { background: #b45309; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #f59e0b; }
        
        .secure-badge { border: 1px solid #10b981; color: #10b981; padding: 2px 8px; font-size: 0.7em; }
    </style>
</head>
<body class="min-h-screen flex flex-col overflow-x-hidden">
    <!-- Navbar -->
    <nav class="bg-slate-950/90 border-b border-amber-800 p-4 sticky top-0 z-50 backdrop-blur-md">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-3xl font-bold holo-text tracking-widest flex items-center gap-2">
                [SQLi_DOJO]
            </a>
            <div class="space-x-6 text-sm flex items-center font-bold">
                <span class="text-amber-600 uppercase tracking-widest">SYSTEM: <span class="text-amber-400">OPERATIONAL</span></span>
                <a href="/reset" class="text-red-400 hover:text-red-200 border border-red-900/50 bg-red-900/20 px-4 py-1 rounded transition-all hover:shadow-[0_0_10px_rgba(248,113,113,0.5)]">
                    // RESET_DB
                </a>
            </div>
        </div>
    </nav>

    <div class="container mx-auto flex-grow flex flex-col md:flex-row mt-8 gap-6 px-4 mb-10">
        <!-- Sidebar Navigation -->
        <aside class="md:w-72 flex-shrink-0">
            <div class="holo-box p-5 rounded-lg h-full">
                <h3 class="text-amber-300 uppercase text-sm font-bold mb-4 border-b border-amber-800 pb-2 flex justify-between">
                    <span>Injection Modules</span>
                    <span>v1.0</span>
                </h3>
                <div class="space-y-1">
                {% for i in range(1, 11) %}
                <a href="/level{{i}}" class="block px-3 py-2 text-sm rounded transition-all duration-200 mono-font
                    {{ 'bg-amber-900/50 text-white border-l-4 border-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.3)]' if active_level == i else 'text-slate-400 hover:text-amber-200 hover:bg-amber-900/20 hover:pl-4' }}">
                    Level {{ '%02d' % i }} :: {{ titles[i-1] }}
                </a>
                {% endfor %}
                </div>
            </div>
        </aside>

        <!-- Main Interface -->
        <main class="flex-1 relative">
            <div class="mb-6">
                <div class="flex items-end gap-4 mb-2">
                    <h1 class="text-5xl font-bold text-white drop-shadow-[0_0_5px_rgba(255,255,255,0.5)]">{{ current_title }}</h1>
                    <span class="text-amber-600 font-mono text-xl mb-1">ID: {{ 'L%02d' % active_level }}</span>
                </div>
                
                <div class="flex items-center gap-2 mb-4">
                    <span class="text-slate-500 font-bold text-sm uppercase">Threat Level:</span>
                    <div class="flex gap-1">
                        {% for i in range(1, 11) %}
                            <div class="h-2 w-4 rounded-sm {{ 'bg-amber-500 shadow-[0_0_5px_#f59e0b]' if i <= active_level else 'bg-slate-800' }}"></div>
                        {% endfor %}
                    </div>
                </div>
                
                <p class="text-slate-300 mono-font border-l-2 border-amber-600 pl-4 py-1 bg-gradient-to-r from-amber-900/20 to-transparent">
                    <span class="text-amber-500 font-bold">Briefing:</span> {{ description }}
                </p>
            </div>
            
            <div class="holo-box p-8 min-h-[400px] relative rounded-lg overflow-hidden flex flex-col">
                <div class="scan-line absolute top-0 left-0 pointer-events-none opacity-20"></div>
                <!-- Content Rendered Here -->
                {{ content | safe }}
                
                {% if query_log %}
                <div class="mt-auto pt-6 border-t border-amber-900/50">
                    <div class="text-xs text-slate-500 font-mono mb-1">EXECUTED QUERY LOG:</div>
                    <code class="block bg-black p-3 rounded border border-amber-900 text-amber-500 font-mono text-sm break-all">
                        {{ query_log }}
                    </code>
                </div>
                {% endif %}
            </div>
        </main>
    </div>
    
    <footer class="bg-slate-950 border-t border-amber-900 text-center p-6 text-slate-600 text-xs mt-auto mono-font">
        © sondt (Administrator) // All Rights Reserved
    </footer>
</body>
</html>
"""

titles = [
    "Login Bypass (String)", "Login Bypass (Integer)", "UNION Attack", "Error Based",
    "Boolean Blind", "Time Based Blind", "Filter Bypass (Space)", "Second Order",
    "WAF Bypass", "Stacked Queries"
]

def render_page(level_id, description, content, query_log=None, **kwargs):
    # Pass kwargs to template for variable substitution
    return render_template_string(base_layout, 
                                  active_level=level_id, 
                                  titles=titles, 
                                  current_title=titles[level_id-1], 
                                  description=description, 
                                  content=render_template_string(content, **kwargs), # Inner render for content logic
                                  query_log=query_log)

@app.route('/')
def index(): return redirect('/level1')

@app.route('/reset')
def reset():
    db = get_db()
    # Close old connection stored in g
    if hasattr(g, '_database'):
        g._database.close()
        delattr(g, '_database')
    
    # Init new connection will trigger init_db if tables don't exist, 
    # but here we want to force drop/create.
    # Simple way: just drop tables and re-init
    db = get_db() # Re-connect
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
            user = cur.fetchone()
            if user: msg = f"<div class='text-green-400 text-2xl font-bold border-l-4 border-green-500 pl-4'>ACCESS GRANTED: {user['username']}</div>"
            else: msg = "<div class='text-red-500 font-bold'>ACCESS DENIED</div>"
        except Exception as e: msg = f"<div class='text-red-500 font-bold'>SQL ERROR: {e}</div>"

    content = """
    <form method="POST" class="max-w-md mx-auto mt-10">
        <label class="block text-amber-500 mb-1 font-bold">USERNAME</label>
        <div class="flex mb-4">
            <span class="bg-amber-900/50 text-amber-500 p-2 border border-amber-800 border-r-0 font-mono">></span>
            <input type="text" name="username" class="w-full p-2 rounded-r" placeholder="admin">
        </div>
        
        <label class="block text-amber-500 mb-1 font-bold">PASSWORD</label>
        <div class="flex mb-6">
            <span class="bg-amber-900/50 text-amber-500 p-2 border border-amber-800 border-r-0 font-mono">*</span>
            <input type="password" name="password" class="w-full p-2 rounded-r" placeholder="******">
        </div>
        
        <button class="bg-amber-600 text-black px-6 py-2 font-bold w-full hover:bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)] transition">LOGIN</button>
    </form>
    <div class="mt-8 text-center">{{ msg|safe }}</div>
    """
    return render_page(1, "Bypass authentication. Log in as 'admin' without knowing the password.", content, query_log, msg=msg)

@app.route('/level2')
def level2():
    id_param = request.args.get('id', '1')
    query_log = ""
    items = []
    
    # VULN: Integer injection (No quotes)
    sql = f"SELECT name, price FROM products WHERE id = {id_param}"
    query_log = sql
    try:
        cur = get_db().cursor()
        cur.execute(sql)
        items = cur.fetchall()
    except Exception as e: items = []

    content = """
    <div class="text-center mb-6">
        <form method="GET" class="inline-flex shadow-lg">
            <span class="bg-amber-900/50 text-amber-500 p-2 border border-amber-800 border-r-0 font-mono">ID:</span>
            <input name="id" value="{{ id_param }}" class="w-24 p-2 text-center bg-slate-900 border-amber-800 text-amber-400">
            <button class="bg-amber-700 px-4 py-2 font-bold text-black hover:bg-amber-600">VIEW</button>
        </form>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        {% for item in items %}
        <div class="border border-amber-800 p-4 bg-black/50 hover:bg-amber-900/20 transition">
            <h3 class="text-xl font-bold text-white mb-1">{{ item['name'] }}</h3>
            <div class="text-amber-500 text-sm font-mono">PRICE: {{ item['price'] }} CREDITS</div>
        </div>
        {% else %}
        <div class="text-center text-slate-500 italic col-span-2 mt-4">No items found or SQL Error.</div>
        {% endfor %}
    </div>
    """
    return render_page(2, "Dump all products using Integer Injection (OR 1=1).", content, query_log, items=items, id_param=id_param)

@app.route('/level3')
def level3():
    search = request.args.get('search', '')
    results = []
    query_log = ""
    
    if search:
        # VULN: UNION Injection
        sql = f"SELECT name, description, price FROM products WHERE name LIKE '%{search}%'"
        query_log = sql
        try:
            cur = get_db().cursor()
            cur.execute(sql)
            results = cur.fetchall()
        except Exception as e: results = [("SQL Error", str(e), 0)]

    content = """
    <div class="max-w-xl mx-auto">
        <form method="GET" class="flex gap-0 shadow-lg mb-8">
            <span class="bg-amber-900/50 text-amber-500 p-3 font-mono border border-r-0 border-amber-700">SEARCH://</span>
            <input type="text" name="search" value="{{ search }}" class="flex-1 p-3 bg-slate-900/80 border-amber-700" placeholder="...">
            <button class="bg-amber-600 px-6 font-bold text-black hover:bg-amber-500">SCAN</button>
        </form>
        
        <div class="space-y-2">
            {% for r in results %}
            <div class="p-2 border-l-2 border-amber-500 bg-slate-900/50 text-amber-100 font-mono text-sm">
                <span class="text-amber-500">>></span> {{ r[0] }} <span class="text-slate-500">::</span> {{ r[1] }}
            </div>
            {% endfor %}
        </div>
        
        <div class="mt-8 border-t border-dashed border-amber-900 pt-4 text-xs text-slate-500 text-center">
            Target: Hidden table 'secrets' (columns: id, flag).
        </div>
    </div>
    """
    return render_page(3, "Use UNION SELECT to retrieve the 'flag' from 'secrets'.", content, query_log, results=results, search=search)

@app.route('/level4')
def level4():
    id_param = request.args.get('id', '1')
    error_msg = None
    
    sql = f"SELECT * FROM users WHERE id = {id_param}"
    try:
        cur = get_db().cursor()
        cur.execute(sql)
        cur.fetchall()
    except Exception as e:
        error_msg = str(e)

    content = """
    <div class="text-center max-w-lg mx-auto">
        <h2 class="text-xl mb-6 text-amber-300">USER LOOKUP SERVICE v0.9</h2>
        <form method="GET" class="mb-8">
            <input name="id" value="{{ id_param }}" class="w-32 p-2 text-center bg-slate-900 border-amber-800" placeholder="User ID">
            <button class="bg-amber-700 px-4 py-2 font-bold text-black ml-2">CHECK</button>
        </form>
        
        {% if error_msg %}
        <div class="p-4 border border-red-500 bg-red-900/20 text-red-400 font-mono text-left shadow-[0_0_15px_rgba(239,68,68,0.2)]">
            <div class="font-bold border-b border-red-500/50 mb-2 pb-1">FATAL_ERROR_DUMP:</div>
            {{ error_msg }}
        </div>
        {% endif %}
    </div>
    """
    return render_page(4, "Trigger a syntax error to confirm injection.", content, sql, id_param=id_param, error_msg=error_msg)

@app.route('/level5')
def level5():
    username = request.args.get('u', 'admin')
    # VULN: Boolean Blind
    sql = f"SELECT * FROM users WHERE username = '{username}'"
    exists = False
    try:
        cur = get_db().cursor()
        cur.execute(sql)
        if cur.fetchone(): exists = True
    except: pass
    
    status = "<span class='text-green-400 font-bold'>[ MATCH FOUND ]</span>" if exists else "<span class='text-red-500 font-bold'>[ NO MATCH ]</span>"

    content = """
    <div class="text-center mt-10 max-w-lg mx-auto">
        <div class="border border-amber-500/30 p-8 bg-slate-900/50 rounded">
            <h2 class="text-2xl mb-6 text-amber-400">Identity Verifier</h2>
            <form method="GET" class="mb-8">
                <input name="u" value="{{ username }}" class="p-2 w-full mb-2 bg-black text-center border-amber-800" placeholder="Username">
                <button class="bg-amber-600 px-8 py-2 font-bold text-black w-full hover:bg-amber-500">VERIFY IDENTITY</button>
            </form>
            <div class="text-3xl font-mono tracking-wider">{{ status|safe }}</div>
        </div>
        <p class="mt-4 text-xs text-slate-500">System returns only Boolean (True/False) responses.</p>
    </div>
    """
    return render_page(5, "Boolean Blind. Guess True/False questions.", content, "HIDDEN (Blind Query)", username=username, status=status)

@app.route('/level6')
def level6():
    search = request.args.get('q', '')
    start_time = time.time()
    if search:
        # VULN: Time Based (sleep function injected)
        sql = f"SELECT * FROM products WHERE name = '{search}'"
        try:
            cur = get_db().cursor()
            cur.execute(sql)
            cur.fetchall()
        except: pass
    
    duration = time.time() - start_time
    msg = f"Completed in {duration:.2f}s"

    content = """
    <div class="text-center max-w-xl mx-auto">
        <h2 class="text-2xl mb-2 text-white font-light">HEAVY SEARCH ENGINE</h2>
        <p class="text-slate-500 mb-6 text-sm">Complex algorithm. May take time.</p>
        
        <form method="GET" class="flex">
            <input name="q" value="{{ search }}" class="flex-1 p-3 bg-slate-900 border-amber-800" placeholder="Product name...">
            <button class="bg-amber-600 px-6 py-3 font-bold text-black">SEARCH</button>
        </form>
        
        <div class="mt-8 p-4 border border-amber-900 bg-black text-amber-500 font-mono text-xl">
            STATUS: <span class="text-white">{{ msg }}</span>
        </div>
        <p class="mt-4 text-xs text-slate-500">Hint: <code>' AND sleep(3)--</code></p>
    </div>
    """
    return render_page(6, "Time Based. Force a delay to extract data.", content, "HIDDEN (Blind Query)", search=search, msg=msg)

@app.route('/level7')
def level7():
    id_param = request.args.get('id', '1')
    res = ""
    
    # WAF: Block spaces
    if ' ' in id_param:
        res = "<div class='text-red-500 text-2xl font-bold p-4 border border-red-500 bg-red-900/20'>WAF ALERT: SPACE CHAR DETECTED</div>"
        sql = "BLOCKED_BY_WAF"
    else:
        sql = f"SELECT name, price FROM products WHERE id = {id_param}"
        try:
            cur = get_db().cursor()
            cur.execute(sql)
            item = cur.fetchone()
            res = f"<div class='text-xl text-white'>ITEM: <span class='text-amber-400'>{item['name']}</span> <br> PRICE: {item['price']}</div>" if item else "Not found"
        except Exception as e: res = str(e)

    content = """
    <div class="text-center">
        <h2 class="mb-6 text-amber-500 font-bold border-b border-amber-900 inline-block pb-2">STRICT FIREWALL: NO SPACES</h2>
        <form method="GET" class="mb-8">
            <input name="id" value="{{ id_param }}" class="p-2 w-64 bg-slate-900 border-amber-700" placeholder="ID (No spaces allowed)">
            <button class="bg-amber-600 px-4 py-2 font-bold text-black">GET</button>
        </form>
        <div class="mt-6">{{ res|safe }}</div>
        <p class="mt-8 text-xs text-slate-500">Hint: Use SQL comments <code>/**/</code> to replace spaces.</p>
    </div>
    """
    return render_page(7, "Bypass Space Filter.", content, sql, id_param=id_param, res=res)

@app.route('/level8', methods=['GET', 'POST'])
def level8():
    if request.method == 'POST':
        username = request.form.get('username', '')
        g.stored_user = username # Simulation of storage
        return redirect(url_for('level8', step='view', user=username))

    step = request.args.get('step', 'register')
    stored_user = request.args.get('user', '')
    query_log = ""
    
    if step == 'register':
        content = """
        <div class="max-w-md mx-auto">
            <h3 class="text-xl mb-4 text-amber-400">Step 1: User Registration</h3>
            <form method="POST">
                <input name="username" class="w-full p-3 mb-2 bg-slate-900 border-amber-800" placeholder="Choose username...">
                <button class="bg-amber-600 w-full py-3 font-bold text-black hover:bg-amber-500">REGISTER USER</button>
            </form>
            <p class="mt-4 text-sm text-slate-500">Your username will be stored in the database.</p>
        </div>
        """
        return render_page(8, "Second Order. Inject payload into database, trigger it later.", content, "")
    else:
        # VULN: Second order
        sql = f"SELECT role FROM users WHERE username = '{stored_user}'"
        query_log = sql
        role = "guest"
        try:
            cur = get_db().cursor()
            cur.execute(sql)
            res = cur.fetchone()
            if res: role = res[0]
        except Exception as e: role = f"ERROR: {e}"

        content = """
        <div class="max-w-md mx-auto">
            <h3 class="text-xl mb-4 text-amber-400">Step 2: Admin Profile View</h3>
            <div class="p-6 border border-amber-500 bg-slate-900/80">
                <div class="mb-4 text-sm text-slate-400">VIEWING USER PROFILE:</div>
                <div class="text-2xl text-white mb-2">{{ user }}</div>
                <div class="border-t border-amber-900 pt-2 mt-2">
                    ROLE: <span class="text-red-400 font-bold text-xl">{{ role }}</span>
                </div>
            </div>
            <div class="mt-6 text-center">
                <a href="/level8" class="text-amber-500 hover:text-white underline">Register another user</a>
            </div>
        </div>
        """
        return render_page(8, "Payload execution (Stored).", content, query_log, user=stored_user, role=role)

@app.route('/level9')
def level9():
    search = request.args.get('q', '')
    results = []
    
    # WAF: Block "UNION SELECT" with space, case insensitive
    if re.search(r'union\s+select', search, re.IGNORECASE):
        msg = "<div class='text-red-500 text-center text-3xl font-bold p-8 border-2 border-red-500 bg-red-900/30'>WAF BLOCKED: 'UNION SELECT'</div>"
        return render_page(9, "WAF Bypass.", msg, "BLOCKED_BY_WAF")

    sql = f"SELECT name, description FROM products WHERE name LIKE '%{search}%'"
    try:
        cur = get_db().cursor()
        cur.execute(sql)
        results = cur.fetchall()
    except Exception as e: results = []

    content = """
    <div class="max-w-lg mx-auto">
        <div class="mb-4 flex items-center gap-2 text-red-400 border border-red-900/50 p-2 bg-red-900/10 rounded">
            <span>Active Rule: Block "UNION SELECT"</span>
        </div>
        <form method="GET" class="flex gap-2">
            <input type="text" name="q" value="{{ search }}" class="flex-1 p-2 bg-slate-900 border-amber-800" placeholder="Product search...">
            <button class="bg-amber-600 px-4 font-bold text-black">SEARCH</button>
        </form>
        <ul class="mt-6 space-y-2 font-mono text-amber-200">
            {% for r in results %}
            <li class="p-2 bg-slate-900/50 border-l border-amber-700">{{ r[0] }} - <span class="text-slate-400">{{ r[1] }}</span></li>
            {% endfor %}
        </ul>
    </div>
    """
    return render_page(9, "Bypass 'UNION SELECT' filter.", content, sql, search=search, results=results)

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
            # VULN: Stacked queries
            cur.executescript(sql)
            
            # Verify result
            cur.execute("SELECT password FROM users WHERE username='admin'")
            if cur.fetchone()[0] == 'pwned':
                msg = "<div class='text-green-400 text-2xl font-bold border-2 border-green-500 p-4 bg-green-900/20'>SYSTEM PWNED! Password changed.</div>"
            else:
                msg = "<div class='text-slate-400 italic'>Query executed. Admin password unchanged.</div>"
        except Exception as e: msg = f"<div class='text-red-500'>Error: {e}</div>"

    content = """
    <div class="text-center max-w-lg mx-auto">
        <h2 class="text-2xl mb-4 text-red-500 font-bold animate-pulse">ADMIN RESET CONSOLE</h2>
        <p class="mb-6 text-slate-400">Dangerous Operation. Stacked Queries Enabled.</p>
        
        <form method="POST">
            <input name="id" class="w-full p-3 mb-2 bg-slate-900 border-red-900 text-red-100 placeholder-red-900/50" placeholder="Target User ID...">
            <button class="bg-red-700 text-white w-full py-3 font-bold hover:bg-red-600 shadow-[0_0_15px_rgba(185,28,28,0.4)]">EXECUTE BATCH</button>
        </form>
        
        <div class="mt-8 border p-4 border-amber-900 bg-black/80 min-h-[60px] flex items-center justify-center">
            {{ msg|safe }}
        </div>
        <p class="mt-4 text-xs text-slate-500">Goal: Change admin password to 'pwned'.<br>Hint: <code>1; UPDATE users SET ...</code></p>
    </div>
    """
    return render_page(10, "Stacked Queries (UPDATE).", content, query_log, msg=msg)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)