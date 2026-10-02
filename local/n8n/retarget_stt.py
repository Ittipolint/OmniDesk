import urllib.request, json, sys
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
    return json.loads(op.open(req, timeout=120).read())

WID = 'af6AkiMrcJupk8E5'
d = call('GET', '/rest/workflows/' + WID)['data']
for n in d['nodes']:
    if n['name'] == 'Whisper ASR':
        n['parameters']['url'] = sys.argv[1]
        print('url set to:', sys.argv[1][:80])
r = call('PATCH', '/rest/workflows/' + WID,
         {'name': d['name'], 'nodes': d['nodes'], 'connections': d['connections'],
          'settings': d.get('settings', {})})
ver = r['data']['versionId']
print('new version:', ver)
r2 = call('POST', '/rest/workflows/' + WID + '/activate', {'versionId': ver})
print('active:', r2.get('data', r2).get('active'))
