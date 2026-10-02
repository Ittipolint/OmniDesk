import urllib.request, http.cookiejar, json, re, urllib.parse, os
BASE = 'http://127.0.0.1:8081'
OUT = r'C:\Users\pol\AppData\Local\Temp\opencode\baseline'
os.makedirs(OUT, exist_ok=True)
cj = http.cookiejar.MozillaCookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def rq(url, data=None, headers=None):
    h = {'User-Agent': 'Mozilla/5.0'}
    if headers:
        h.update(headers)
    return op.open(urllib.request.Request(url, data=data, headers=h), timeout=60).read().decode()

login = urllib.parse.urlencode({'login_user': 'admin', 'login_pass': '10203040'}).encode()
rq(BASE + '/chatdesk/index.php', data=login, headers={'Content-Type': 'application/x-www-form-urlencoded'})
html = rq(BASE + '/chatdesk/rag/')
csrf = re.search(r'var CSRF = "([a-f0-9]+)"', html).group(1)
print('csrf:', csrf[:8])

def api(path, obj):
    return json.loads(rq(BASE + path, data=json.dumps(obj).encode(),
                         headers={'Content-Type': 'application/json'}))

open(os.path.join(OUT, 'rag_stats.json'), 'w', encoding='utf-8').write(
    json.dumps(api('/chatdesk/rag/api/stats.php', {'csrf': csrf}),
               ensure_ascii=False, indent=1, sort_keys=True))
print('saved rag_stats')
