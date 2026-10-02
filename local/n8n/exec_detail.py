import urllib.request, json
BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
import http.cookiejar
cj = http.cookiejar.MozillaCookieJar(CJ)
cj.load(CJ, ignore_discard=True, ignore_expires=True)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get(path):
    req = urllib.request.Request(BASE + path, headers={'User-Agent': 'Mozilla/5.0'})
    return json.loads(op.open(req, timeout=60).read())

exe = get('/rest/executions?limit=1')['data']['results'][0]
eid = exe['id']
print('exec', eid, exe['status'])
d = get('/rest/executions/%s?includeData=true' % eid)
dd = d['data']
data = dd.get('data')
print('data type:', type(data))
if isinstance(data, str):
    print('len:', len(data))
    try:
        dj = json.loads(data)
        print('is list of', len(dj))
        def res(x, depth=0):
            try:
                if depth > 12:
                    return '...'
                if isinstance(x, str) and x.isdigit() and int(x) < len(dj):
                    return res(dj[int(x)], depth + 1)
                if isinstance(x, list):
                    return [res(i, depth + 1) for i in x]
                if isinstance(x, dict):
                    return {k: res(v, depth + 1) for k, v in x.items()}
                return x
            except Exception:
                return '?'
        full = res(dj)
        rd = full[2].get('runData', {}) if isinstance(full, list) else {}
        print('lastNode:', full[2].get('lastNodeExecuted') if isinstance(full, list) else '?')
        print('top error:', str(full[2].get('error'))[:300] if isinstance(full, list) else '?')
        if isinstance(rd, dict):
            for k, v in rd.items():
                st = (v or [{}])[0] if isinstance(v, list) else {}
                err = (st.get('error') or {}) if isinstance(st, dict) else {}
                msg = (err.get('message') or err.get('description') or '')
                if msg:
                    print('FAIL NODE:', k, '::', msg[:300])
    except Exception as e:
        print('not plain json:', str(e)[:100])
if isinstance(data, dict):
    rd = data.get('resultData', {})
    for k, v in (rd.get('runData') or {}).items():
        st = (v or [{}])[0]
        err = st.get('error') or {}
        msg = err.get('message') or err.get('description') or ''
        print('NODE:', k, '::', msg[:250].replace(chr(10), ' | '))
