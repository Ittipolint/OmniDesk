import urllib.request, json
BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
import http.cookiejar
cj = http.cookiejar.MozillaCookieJar(CJ)
cj.load(CJ, ignore_discard=True, ignore_expires=True)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def activate(wid, ver):
    body = json.dumps({'versionId': ver}).encode()
    req = urllib.request.Request(BASE + '/rest/workflows/' + wid + '/activate', data=body,
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    d = json.loads(op.open(req, timeout=60).read())
    print(wid, 'active:', d.get('data', d).get('active'))

activate('AH6wmgP25j8erHEB', 'd4e2ef44-ff11-4d07-b6c1-bc0cab434b5a')
activate('4C8QHmcAJ02jW7Z9', '823308af-0f44-4730-b469-ce0163010c00')
activate('gesxAirJO3NY4gQR', '8439f663-5043-41a5-a8f6-7f1a9b74992a')
