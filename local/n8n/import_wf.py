import urllib.request, json, os
BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'

import http.cookiejar
cj = http.cookiejar.MozillaCookieJar(CJ)
try:
    cj.load(CJ, ignore_discard=True, ignore_expires=True)
except Exception as e:
    print('cookie load:', e)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def call(method, path, obj=None):
    data = json.dumps(obj).encode() if obj is not None else None
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                                 method=method)
    r = op.open(req, timeout=60)
    return json.loads(r.read())

base = r'C:\Users\pol\Desktop\OpenCode Project\ChatDesk\local\n8n'
for fn in ['rag-03-ingest.json', 'rag-04-answer.json']:
    wf = json.load(open(os.path.join(base, fn), encoding='utf-8'))
    try:
        out = call('POST', '/rest/workflows', wf)
        d = out.get('data', out)
        print(fn, '-> id:', d.get('id'), '| active:', d.get('active'), '| keys:', sorted(out.keys()))
    except Exception as e:
        import urllib.error
        body = ''
        try:
            body = e.read().decode()[:600]
        except Exception:
            pass
        print(fn, 'FAILED:', str(e)[:200], body)
