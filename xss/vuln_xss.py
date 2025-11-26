import sqlite3
from flask import Flask, request, render_template_string, redirect, url_for, make_response
import re
import html
import urllib.parse
import json

app = Flask(__name__)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE comments (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT)''')
    conn.commit()
    return conn

db = init_db()

# --- TEMPLATES (Frontend - Blue Holographic Theme) ---
# FIX: Changed {% block extra_head %} to {{ extra_head|default('')|safe }} so variables pass through correctly
base_layout = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XSS DOJO | Advanced Cyber Range</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Source+Code+Pro:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { 
            font-family: 'Rajdhani', sans-serif; 
            background-color: #020617; /* Slate 950 */
            color: #38bdf8; /* Sky 400 */
            background-image: 
                linear-gradient(rgba(6, 182, 212, 0.1) 1px, transparent 1px), 
                linear-gradient(90deg, rgba(6, 182, 212, 0.1) 1px, transparent 1px);
            background-size: 40px 40px;
        }
        
        .mono-font { font-family: 'Source Code Pro', monospace; }
        
        /* Holographic Effects */
        .holo-text { text-shadow: 0 0 5px #0ea5e9, 0 0 10px #0ea5e9; }
        .holo-box { 
            background: rgba(8, 47, 73, 0.6); 
            border: 1px solid #0ea5e9; 
            box-shadow: 0 0 15px rgba(14, 165, 233, 0.2), inset 0 0 20px rgba(14, 165, 233, 0.1); 
            backdrop-filter: blur(4px);
        }
        
        input, textarea, select { 
            background-color: #0f172a; 
            color: #bae6fd; 
            border: 1px solid #1e40af; 
            font-family: 'Source Code Pro', monospace;
        }
        input:focus, textarea:focus, select:focus { 
            outline: none; 
            border-color: #38bdf8; 
            box-shadow: 0 0 10px #38bdf8; 
        }
        
        .scan-line {
            width: 100%;
            height: 2px;
            background: rgba(56, 189, 248, 0.5);
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
        ::-webkit-scrollbar-thumb { background: #0369a1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #0ea5e9; }
    </style>
    {{ extra_head|default('')|safe }}
</head>
<body class="min-h-screen flex flex-col overflow-x-hidden">
    <!-- Navbar -->
    <nav class="bg-slate-950/90 border-b border-cyan-800 p-4 sticky top-0 z-50 backdrop-blur-md">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-3xl font-bold holo-text tracking-widest flex items-center gap-2">
                [XSS_DOJO]
            </a>
            <div class="space-x-6 text-sm flex items-center font-bold">
                <span class="text-cyan-600 uppercase tracking-widest">SYSTEM: <span class="text-cyan-400">OPERATIONAL</span></span>
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
                <h3 class="text-cyan-300 uppercase text-sm font-bold mb-4 border-b border-cyan-800 pb-2 flex justify-between">
                    <span>Training Modules</span>
                    <span>v2.2</span>
                </h3>
                <div class="space-y-1">
                {% for i in range(1, 11) %}
                <a href="/level{{i}}" class="block px-3 py-2 text-sm rounded transition-all duration-200 mono-font
                    {{ 'bg-cyan-900/50 text-white border-l-4 border-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.3)]' if active_level == i else 'text-slate-400 hover:text-cyan-200 hover:bg-cyan-900/20 hover:pl-4' }}">
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
                    <span class="text-cyan-600 font-mono text-xl mb-1">ID: {{ 'L%02d' % active_level }}</span>
                </div>
                
                <div class="flex items-center gap-2 mb-4">
                    <span class="text-slate-500 font-bold text-sm uppercase">Threat Level:</span>
                    <div class="flex gap-1">
                        {% for i in range(1, 11) %}
                            <div class="h-2 w-4 rounded-sm {{ 'bg-cyan-400 shadow-[0_0_5px_#22d3ee]' if i <= active_level else 'bg-slate-800' }}"></div>
                        {% endfor %}
                    </div>
                </div>
                
                <p class="text-slate-300 mono-font border-l-2 border-cyan-600 pl-4 py-1 bg-gradient-to-r from-cyan-900/20 to-transparent">
                    <span class="text-cyan-500 font-bold">Briefing:</span> {{ description }}
                </p>
            </div>
            
            <div class="holo-box p-8 min-h-[400px] relative rounded-lg overflow-hidden">
                <div class="scan-line absolute top-0 left-0 pointer-events-none opacity-20"></div>
                <!-- Injection Point Rendered Here -->
                {{ content | safe }}
            </div>
        </main>
    </div>
    
    <footer class="bg-slate-950 border-t border-cyan-900 text-center p-6 text-slate-600 text-xs mt-auto mono-font">
        © sondt (Administrator) // All Rights Reserved
    </footer>
</body>
</html>
"""

titles = [
    "Reflected (No Filter)",
    "Stored (Persistence)",
    "DOM (Fragment)",
    "Tag Filter (No Script)",
    "Attribute (Quotes)",
    "Protocol (Href)",
    "JS Context (String)",
    "Double Encoding (WAF)",
    "Client-Side Template (CSTI)",
    "CSP Bypass (JSONP Gadget)"
]

# --- ROUTES ---

@app.route('/')
def index():
    return redirect('/level1')

@app.route('/reset')
def reset():
    global db
    db.close()
    db = init_db()
    return redirect('/')

# LEVEL 1: Reflected (Basic)
@app.route('/level1')
def level1():
    query = request.args.get('q', '')
    html_content = f"""
        <form method="GET" class="mb-8">
            <label class="block mb-2 text-xl text-cyan-300">USER SEARCH PROTOCOL:</label>
            <div class="flex gap-0 shadow-lg">
                <span class="bg-cyan-900/50 text-cyan-300 p-3 font-mono border border-r-0 border-cyan-700">query://</span>
                <input type="text" name="q" value="Guest" class="flex-1 p-3 text-lg bg-slate-900/80 border-cyan-700" placeholder="Enter payload...">
                <button class="bg-cyan-600 text-white px-8 py-2 font-bold hover:bg-cyan-500 transition shadow-[0_0_15px_rgba(8,145,178,0.5)]">SCAN</button>
            </div>
        </form>
        <div class="mt-8 border-t border-dashed border-cyan-800 pt-6">
            <div class="text-xs text-cyan-600 mb-2 font-mono uppercase">System Output:</div>
            <div class="text-3xl text-white break-words font-light">Welcome back, <span class="text-cyan-300">{query}</span></div>
        </div>
    """
    return render_template_string(base_layout, active_level=1, titles=titles, 
                                  current_title=titles[0], 
                                  description="The basics. No filters applied. Input is reflected directly into the HTML body.",
                                  content=html_content)

# LEVEL 2: Stored
@app.route('/level2', methods=['GET', 'POST'])
def level2():
    if request.method == 'POST':
        comment = request.form.get('comment', '')
        # VULN: Stored XSS without sanitization
        c = db.cursor()
        c.execute("INSERT INTO comments (content) VALUES (?)", (comment,))
        db.commit()
        return redirect('/level2')

    c = db.cursor()
    c.execute("SELECT content FROM comments")
    comments = c.fetchall()
    
    comments_html = "".join([f'<div class="border-l-2 border-cyan-500 bg-slate-900/50 p-4 mb-3 text-cyan-100 break-words shadow-sm">{row[0]}</div>' for row in comments])
    
    html_content = f"""
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
                <h3 class="font-bold mb-4 text-xl text-cyan-400 border-b border-cyan-800/50 pb-2">ADD LOG ENTRY</h3>
                <form method="POST">
                    <textarea name="comment" class="w-full p-4 h-40 mb-4 bg-slate-900/80 rounded" placeholder="Inject malicious code here..."></textarea>
                    <button class="bg-green-600 text-white px-6 py-2 w-full font-bold hover:bg-green-500 rounded shadow-lg transition">COMMIT TO DB</button>
                </form>
            </div>
            <div class="bg-slate-950/30 p-4 rounded border border-slate-800">
                <h3 class="font-bold mb-4 text-xl text-cyan-400 border-b border-cyan-800/50 pb-2">SERVER LOGS</h3>
                <div class="h-80 overflow-y-auto pr-2 custom-scrollbar">
                    {comments_html if comments else '<div class="text-slate-600 italic text-center mt-10">No entries found.</div>'}
                </div>
            </div>
        </div>
    """
    return render_template_string(base_layout, active_level=2, titles=titles,
                                  current_title=titles[1],
                                  description="Persistence. The payload is saved to the database and executed every time the page loads.",
                                  content=html_content)

# LEVEL 3: DOM Based
@app.route('/level3')
def level3():
    html_content = """
        <div class="text-center py-12">
            <div class="inline-block p-6 border border-cyan-500/30 rounded-full mb-6">
            </div>
            <h2 class="text-3xl mb-2 text-white font-light">SIGNAL INTERCEPTOR</h2>
            <p class="text-slate-400 mb-8">Waiting for URL Fragment...</p>
            
            <div id="signal-display" class="hidden p-6 bg-cyan-900/20 border border-cyan-500/50 rounded text-xl text-cyan-300"></div>
        </div>
        
        <script>
            // Simulate processing delay
            setTimeout(() => {
                var hash = decodeURIComponent(window.location.hash.substring(1));
                var display = document.getElementById('signal-display');
                
                if (hash) {
                    display.classList.remove('hidden');
                    // VULN: DOM XSS source is location.hash, sink is innerHTML
                    display.innerHTML = "Signal Received: " + hash;
                }
            }, 500);
        </script>
    """
    return render_template_string(base_layout, active_level=3, titles=titles,
                                  current_title=titles[2],
                                  description="Client-side vulnerability. The server does not see the payload. Check the URL Fragment (#).",
                                  content=html_content)

# LEVEL 4: Tag Filter (No Script)
@app.route('/level4')
def level4():
    query = request.args.get('q', '')
    # FILTER: Remove <script> tags (case insensitive)
    safe_query = re.sub(r'(?i)<script.*?>.*?</script>', '[BLOCKED]', query)
    safe_query = re.sub(r'(?i)<script', '[BLOCKED]', safe_query)
    
    html_content = f"""
        <form method="GET" class="max-w-2xl mx-auto">
            <div class="mb-2 flex justify-between">
                <label class="text-cyan-300 font-bold">SECURITY FILTER: <span class="text-green-400">ACTIVE</span></label>
                <span class="text-xs text-slate-500">Blocklist: &lt;script&gt;</span>
            </div>
            <div class="flex gap-2">
                <input type="text" name="q" value="{query}" class="w-full p-3 rounded bg-slate-900 border-slate-700" placeholder="Try <script>alert(1)</script>">
                <button class="bg-blue-700 px-6 py-2 text-white font-bold rounded hover:bg-blue-600">TEST</button>
            </div>
        </form>
        <div class="mt-10 p-6 border border-slate-700 bg-slate-900/50 rounded text-center">
            <div class="text-slate-500 text-xs uppercase mb-2">Rendered Output</div>
            <div class="text-xl">{safe_query}</div>
        </div>
    """
    return render_template_string(base_layout, active_level=4, titles=titles,
                                  current_title=titles[3],
                                  description="Bypass. The administrator has blocked the <script> tag. Can you execute JS using other tags?",
                                  content=html_content)

# LEVEL 5: Attribute Injection
@app.route('/level5')
def level5():
    username = request.args.get('u', 'User')
    # FILTER: Escapes < and > but NOT quotes (").
    # Prevents creating new tags, forces attribute injection.
    safe_username = username.replace('<', '&lt;').replace('>', '&gt;')
    
    html_content = f"""
        <div class="max-w-md mx-auto bg-slate-900 p-8 rounded border border-slate-800 shadow-2xl">
            <h2 class="text-2xl text-white mb-6 border-b border-slate-700 pb-2">Profile Settings</h2>
            <form method="GET">
                <label class="text-cyan-600 text-sm font-bold">DISPLAY NAME</label>
                <!-- VULN: Input reflects inside value attribute, double quotes are not escaped -->
                <input type="text" name="u" value="{safe_username}" class="w-full p-3 mt-1 mb-4 rounded bg-black border-cyan-900 text-white focus:border-cyan-500">
                
                <button class="w-full bg-cyan-700 text-white py-3 font-bold rounded hover:bg-cyan-600 transition">UPDATE PROFILE</button>
            </form>
            <div class="mt-4 text-xs text-slate-500 text-center">
                Note: Tag injection (&lt; &gt;) is blocked by WAF.
            </div>
        </div>
    """
    return render_template_string(base_layout, active_level=5, titles=titles,
                                  current_title=titles[4],
                                  description="Context Breakout. Angle brackets are escaped. You cannot create new tags. Check the input attribute.",
                                  content=html_content)

# LEVEL 6: Protocol Injection
@app.route('/level6')
def level6():
    link = request.args.get('link', 'https://example.com')
    # FILTER: Full HTML escape (Quotes and Tags).
    # Cannot break out of the attribute.
    safe_link = html.escape(link) 
    
    html_content = f"""
        <div class="text-center">
            <h2 class="text-3xl mb-6 text-white font-light">HYPERLINK MANAGER</h2>
            
            <div class="mb-10">
                <a href="{safe_link}" class="group relative inline-flex items-center justify-center px-8 py-4 font-bold text-white transition-all duration-200 bg-cyan-600 font-lg rounded hover:bg-cyan-500 hover:shadow-[0_0_20px_rgba(8,145,178,0.6)] hover:-translate-y-1">
                    <span>VISIT DESTINATION</span>
                    <svg class="w-5 h-5 ml-2 -mr-1 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"></path></svg>
                </a>
            </div>
            
            <form method="GET" class="max-w-lg mx-auto border-t border-slate-800 pt-8">
                <label class="block text-left text-cyan-500 text-sm mb-1">SET CUSTOM URL:</label>
                <div class="flex">
                    <input name="link" value="{safe_link}" class="flex-1 p-2 bg-slate-900 border-slate-700">
                    <button class="bg-slate-700 px-4 text-white hover:bg-slate-600">SAVE</button>
                </div>
                <p class="text-xs text-left text-slate-500 mt-2">All special characters are HTML escaped.</p>
            </form>
        </div>
    """
    return render_template_string(base_layout, active_level=6, titles=titles,
                                  current_title=titles[5],
                                  description="Protocol. All HTML characters are escaped. You are trapped inside the href attribute.",
                                  content=html_content)

# LEVEL 7: JS Context
@app.route('/level7')
def level7():
    payload = request.args.get('p', 'System Normal')
    # FILTER: Prevent HTML Injection, prevent double quote breakout
    safe_payload = payload.replace('<', '').replace('>', '').replace('"', '').replace('/', '')
    
    html_content = f"""
        <div class="text-center py-10">
            <div id="status-box" class="text-4xl font-bold font-mono text-green-400 mb-4">Initializing...</div>
            <div class="text-slate-500">Live System Monitor</div>
        </div>
        <script>
            // CONFIGURATION
            // Developer Note: Removed < > " / to prevent XSS.
            var systemStatus = '{safe_payload}';
            
            document.getElementById('status-box').innerText = "STATUS: " + systemStatus;
        </script>
        
        <form method="GET" class="mt-8 text-center border-t border-slate-800 pt-8">
            <input name="p" value="{safe_payload}" class="w-64 p-2 bg-slate-900 border-slate-700 rounded text-center">
            <button class="ml-2 bg-cyan-700 text-white px-4 py-2 rounded">UPDATE</button>
        </form>
    """
    return render_template_string(base_layout, active_level=7, titles=titles,
                                  current_title=titles[6],
                                  description="Script Injection. Input is inside a JS string. Tags and double quotes are blocked.",
                                  content=html_content)

# LEVEL 8: Double Encoding
@app.route('/level8')
def level8():
    raw_query = request.query_string.decode('utf-8').split('=')[1] if '=' in request.query_string.decode('utf-8') else ''
    
    # 1. WAF CHECK (Checks on raw input)
    decoded_once = urllib.parse.unquote(raw_query)
    
    if '<script' in decoded_once.lower() or 'javascript:' in decoded_once.lower():
        return render_template_string(base_layout, active_level=8, titles=titles, current_title=titles[7], description="BLOCKED", content="<div class='text-red-500 text-center text-4xl font-bold border-2 border-red-500 p-10 bg-red-900/20'>🚫 WAF BLOCKED REQUEST</div>")

    # 2. VULNERABILITY: Application decodes AGAIN
    final_content = urllib.parse.unquote(decoded_once)
    
    html_content = f"""
        <form method="GET" class="text-center">
            <label class="block mb-4 text-xl font-bold text-red-400">🔥 ADVANCED FIREWALL ENABLED</label>
            <div class="inline-flex shadow-lg">
                <input type="text" name="q" class="w-96 p-3 bg-slate-900 border-red-900 text-red-200 placeholder-red-900" placeholder="Try <script>alert(1)</script>">
                <button class="bg-red-700 px-6 py-2 text-white font-bold hover:bg-red-600">INJECT</button>
            </div>
        </form>
        <div class="mt-12 text-center text-2xl font-light">
            Search result: <span class="text-white">{final_content}</span>
        </div>
    """
    return render_template_string(base_layout, active_level=8, titles=titles,
                                  current_title=titles[7],
                                  description="Obfuscation. The WAF checks for '<script' and 'javascript:'. Can you hide your payload via encoding?",
                                  content=html_content)

# LEVEL 9: Client-Side Template Injection (CSTI)
@app.route('/level9')
def level9():
    # Fix: Use raw string (r) for regex to avoid syntax warning about invalid escape sequence \s
    html_content = r"""
        <div class="max-w-2xl mx-auto">
            <h2 class="text-2xl text-cyan-400 mb-4">User Dashboard (Beta)</h2>
            <div class="bg-slate-900 p-6 rounded border border-slate-700">
                <div class="mb-4 text-sm text-slate-500">Welcome back! We interpret your name dynamically.</div>
                <div id="greeting" class="text-3xl text-white font-bold">Hello, Guest!</div>
            </div>
            
            <div class="mt-6 text-sm text-slate-400">
                <p>Tip: Add <code>#name=YourName</code> to the URL to customize.</p>
                <p>Try math: <code>#name={{ 7 * 7 }}</code></p>
            </div>
        </div>

        <script>
            function parseTemplate() {
                var hash = decodeURIComponent(window.location.hash.substring(1));
                if (hash.startsWith("name=")) {
                    var name = hash.split("=")[1];
                    var template = "Hello, " + name + "!";
                    var rendered = template.replace(/{{\s*(.*?)\s*}}/g, function(match, code) {
                        try { return eval(code); } catch(e) { return "ERROR"; }
                    });
                    document.getElementById('greeting').innerHTML = rendered;
                }
            }
            window.addEventListener('hashchange', parseTemplate);
            if(window.location.hash) parseTemplate();
        </script>
    """
    return render_template_string(base_layout, active_level=9, titles=titles,
                                  current_title=titles[8],
                                  description="Template Injection. The application manually parses '{{ code }}' and executes it. Check the URL Fragment.",
                                  content=html_content)

# LEVEL 10: CSP Bypass (JSONP/Gadget)
@app.route('/api/widgets')
def api_widgets():
    callback = request.args.get('callback', 'init')
    data = json.dumps({"status": "ok", "items": ["Widget A", "Widget B"]})
    return f"{callback}({data})"

@app.route('/level10')
def level10():
    query = request.args.get('q', 'Active')
    
    # CSP: Allow self (including our API) but block inline scripts
    # NO 'unsafe-inline'.
    csp_meta = '<meta http-equiv="Content-Security-Policy" content="script-src \'self\';">'
    
    custom_head = f"""
    {csp_meta}
    <style>.secure-badge {{ border: 1px solid #10b981; color: #10b981; padding: 2px 8px; font-size: 0.7em; }}</style>
    """
    
    # FIX: Escaped braces {{ }} for JS function to prevent f-string syntax error
    html_content = f"""
        <div class="text-center">
            <div class="inline-block mb-6">
                <span class="secure-badge">CSP: STRICT</span>
                <span class="secure-badge">SOURCE: SELF ONLY</span>
            </div>
            
            <h2 class="text-3xl mb-4">Secure Dashboard</h2>
            <p class="mb-4 text-slate-400">
                Inline scripts are blocked. Only scripts from <code>'self'</code> are allowed.
            </p>
            
            <div class="bg-slate-900 p-4 rounded mb-6 w-1/2 mx-auto">
                <div id="widget-container">Loading widgets...</div>
            </div>

            <form method="GET" class="mb-8">
                <input type="text" name="q" value="{query}" class="w-1/2 p-3 bg-black border-green-900 text-green-400 font-mono">
                <button class="bg-green-800 text-white px-6 py-3 font-bold">SEARCH</button>
            </form>
            
            <div class="p-4 border border-slate-800 bg-slate-900">
                Result: {query}
            </div>
            
            <!-- Safe Widget Loader using internal API -->
            <script src="/api/widgets?callback=loadWidgets"></script>
            <script>
                // This inline script will be BLOCKED by CSP
                console.log("If you see this, CSP is broken.");
                
                function loadWidgets(data) {{
                    document.getElementById('widget-container').innerText = "Loaded: " + data.items.join(", ");
                }}
            </script>
        </div>
    """
    
    # FIX: Pass extra_head directly to render_template_string
    return render_template_string(base_layout, active_level=10, titles=titles,
                                  current_title=titles[9],
                                  description="CSP Bypass. 'script-src self' is active. Inline scripts are blocked. Can you use the local API to execute code?",
                                  content=html_content,
                                  extra_head=custom_head)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)