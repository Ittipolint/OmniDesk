import urllib.request, http.cookiejar, json, re, urllib.parse
BASE = 'http://127.0.0.1:8081'
cj = http.cookiejar.MozillaCookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def rq(url, data=None, headers=None):
    h = {'User-Agent': 'Mozilla/5.0'}
    if headers:
        h.update(headers)
    r = op.open(urllib.request.Request(url, data=data, headers=h), timeout=60)
    return r.status, r.read()

login = urllib.parse.urlencode({'login_user': 'admin', 'login_pass': '10203040'}).encode()
print(rq(BASE + '/chatdesk/index.php', data=login,
         headers={'Content-Type': 'application/x-www-form-urlencoded'})[0])
st, body = rq(BASE + '/chatdesk/rag/')
print('rag page:', st, len(body))
csrf = re.search(r'var CSRF = "([a-f0-9]+)"', body.decode()).group(1)
st, body = rq(BASE + '/chatdesk/rag/api/stats.php',
              data=json.dumps({'csrf': csrf}).encode(),
              headers={'Content-Type': 'application/json'})
print('stats:', st, body[:200])
