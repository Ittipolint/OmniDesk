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
        r = op.open(req, timeout=60)
        return json.loads(r.read())
    except Exception as e:
        body = ''
        try:
            body = e.read().decode()[:400]
        except Exception:
            pass
        return {'_err': str(e)[:150], '_body': body}

for wid in ['zudtl8dVs8TfcUBj', 'RKrBD4TtzMNsRtEk']:
    print(wid, call('PATCH', '/rest/workflows/' + wid, {'active': True}))
