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
print('exec', exe['id'], exe['status'])
d = get('/rest/executions/%s?includeData=true' % exe['id'])['data']
dj = json.loads(d['data']) if isinstance(d.get('data'), str) else None

def res(x, depth=0):
    try:
        if depth > 10:
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
for k in ['Whisper ASR', 'Shape Transcript', 'Validate']:
    v = rd.get(k, '???')
    s = json.dumps(res(v), ensure_ascii=False)
    print('=' * 10, k, 'bytes:', len(s))
    print(s[:1200])
