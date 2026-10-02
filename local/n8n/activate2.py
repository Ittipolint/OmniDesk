import urllib.request, http.cookiejar, json
BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
cj = http.cookiejar.MozillaCookieJar(CJ)
cj.load(CJ, ignore_discard=True, ignore_expires=True)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def activate(wid, ver):
    body = json.dumps({'versionId': ver}).encode()
    req = urllib.request.Request(BASE + '/rest/workflows/' + wid + '/activate', data=body,
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    d = json.loads(op.open(req, timeout=60).read())
    print(wid, 'active:', d.get('data', d).get('active'))
activate('AH6wmgP25j8erHEB', 'f9030d59-7e3f-48c4-a409-8b55a27acc0e')
activate('ynBDglW8hWrzEp81', '9a7baa85-f75e-4714-9969-74914d2381a5')
