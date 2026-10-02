import urllib.request, json
BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
import http.cookiejar
cj = http.cookiejar.MozillaCookieJar(CJ)
cj.load(CJ, ignore_discard=True, ignore_expires=True)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def call(method, path, obj=None):
    data = json.dumps(obj).encode() if obj is not None else None
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                                 method=method)
    try:
        return json.loads(op.open(req, timeout=60).read())
    except Exception as e:
        body = ''
        try:
            body = e.read().decode()[:200]
        except Exception:
            pass
        return {'_err': str(e)[:120], '_body': body}

for wid in ['YrTEKLIr9iugXw2r', '1SntVHQ7YwqTdrT4', 'uZvS8bNbwWQD7kd8', 'L35TopowvjoXZUwD']:
    print(wid, 'archive:', call('POST', '/rest/workflows/%s/archive' % wid))
    print(wid, 'delete:', call('DELETE', '/rest/workflows/%s' % wid))
