import urllib.request, http.cookiejar, json, re, urllib.parse
BASE = 'http://127.0.0.1:8081'
CJ = r'C:\Users\pol\AppData\Local\Temp\cdeng.txt'
cj = http.cookiejar.MozillaCookieJar(CJ)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def rq(url, data=None, headers=None):
    h = {'User-Agent': 'Mozilla/5.0'}
    if headers:
        h.update(headers)
    return op.open(urllib.request.Request(url, data=data, headers=h), timeout=120).read()

login = urllib.parse.urlencode({'login_user': 'admin', 'login_pass': '10203040'}).encode()
rq(BASE + '/chatdesk/index.php', data=login, headers={'Content-Type': 'application/x-www-form-urlencoded'})
cj.save(CJ, ignore_discard=True, ignore_expires=True)
html = rq(BASE + '/chatdesk/index.php').decode()
csrf = re.search(r'csrf: "([a-f0-9]+)"', html).group(1)
print('csrf ok')
# agent send through n8n engine
r = rq(BASE + '/chatdesk/api/send.php',
       data=json.dumps({'csrf': csrf, 'conversationId': 1, 'text': 'ทดสอบส่งผ่าน n8n engine กลางครับ'}).encode(),
       headers={'Content-Type': 'application/json'})
print('send:', r.decode()[:200])
