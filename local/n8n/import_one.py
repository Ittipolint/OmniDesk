import urllib.request, json, os, sys
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
        return json.loads(op.open(req, timeout=120).read())
    except Exception as e:
        body = ''
        try:
            body = e.read().decode()[:300]
        except Exception:
            pass
        return {'_err': str(e)[:150], '_body': body}

fn = sys.argv[1]
wf = json.load(open(os.path.join(r'C:\Users\pol\Desktop\OpenCode Project\ChatDesk\local\n8n', fn), encoding='utf-8'))
r = call('POST', '/rest/workflows', wf)
d = r.get('data', r)
print(fn, '-> id:', d.get('id'), '| nodes:', len((d.get('nodes') or [])))
