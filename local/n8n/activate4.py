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

activate('4C8QHmcAJ02jW7Z9', '8f436971-12db-4ee6-93ae-e9e2a8e7d9c8')
activate('gesxAirJO3NY4gQR', '838568af-6824-48e7-9504-83aa15a11c6c')
activate('AH6wmgP25j8erHEB', 'bd93f8bd-5b98-4e18-ba86-4257199bc4b2')
activate('ynBDglW8hWrzEp81', '1faed6d5-c955-4bfb-9cac-fd4c3e0a44c2')
