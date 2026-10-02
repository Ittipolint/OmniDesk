import urllib.request, json, sys
BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
import http.cookiejar
cj = http.cookiejar.MozillaCookieJar(CJ)
cj.load(CJ, ignore_discard=True, ignore_expires=True)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
wid = sys.argv[1]
d = json.load(op.open(urllib.request.Request(
    BASE + '/rest/workflows/' + wid, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60))['data']
ver = d.get('versionId')
print('version:', ver, '| active:', d.get('active'))
if len(sys.argv) > 2 and sys.argv[2] == 'on':
    body = json.dumps({'versionId': ver}).encode()
    r = op.open(urllib.request.Request(
        BASE + '/rest/workflows/' + wid + '/activate', data=body,
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}), timeout=60)
    print('activated:', json.load(r).get('data', {}).get('active'))
