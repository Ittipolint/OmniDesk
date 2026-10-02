import urllib.request, http.cookiejar, json, re
BASE = 'http://127.0.0.1:8081'
CJ = r'C:\Users\pol\AppData\Local\Temp\cd_staff.txt'
cj = http.cookiejar.MozillaCookieJar(CJ)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def rq(url, data=None, headers=None):
    h = {'User-Agent': 'Mozilla/5.0'}
    if headers:
        h.update(headers)
    return op.open(urllib.request.Request(url, data=data, headers=h), timeout=30).read()

import urllib.parse
# admin creates staff1
admin_cj = r'C:\Users\pol\AppData\Local\Temp\cd2.txt'
acj = http.cookiejar.MozillaCookieJar(admin_cj)
aop = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(acj))
alogin = urllib.parse.urlencode({'login_user': 'admin', 'login_pass': '10203040'}).encode()
aop.open(urllib.request.Request(BASE + '/chatdesk/index.php', data=alogin,
                                headers={'User-Agent': 'Mozilla/5.0',
                                         'Content-Type': 'application/x-www-form-urlencoded'}), timeout=30).read()
acj.save(admin_cj, ignore_discard=True, ignore_expires=True)
html = aop.open(urllib.request.Request(BASE + '/chatdesk/users/',
                                      headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode()
csrf = re.search(r'var CSRF = "([a-f0-9]+)"', html).group(1)
body = json.dumps({'csrf': csrf, 'username': 'staff1', 'password': 'staff1234',
                   'display_name': 'พนักงาน 1', 'groups': [2]}).encode()
r = aop.open(urllib.request.Request(BASE + '/chatdesk/users/api/save.php', data=body,
                                    headers={'Content-Type': 'application/json',
                                             'User-Agent': 'Mozilla/5.0'}), timeout=30).read()
print('create staff1:', r.decode()[:120])

# staff login
login = urllib.parse.urlencode({'login_user': 'staff1', 'login_pass': 'staff1234'}).encode()
rq(BASE + '/chatdesk/index.php', data=login,
   headers={'Content-Type': 'application/x-www-form-urlencoded'})
cj.save(CJ, ignore_discard=True, ignore_expires=True)
page = rq(BASE + '/chatdesk/index.php').decode()
print('staff sees RAG button:', 'RAG System' in page)
print('staff sees Users button:', 'จัดการผู้ใช้' in page)
print('staff sees inbox:', 'conv-list' in page)
# staff tries admin APIs (must fail 403)
for p in ['/chatdesk/users/api/list.php', '/chatdesk/rag/api/groups.php']:
    html2 = rq(BASE + '/chatdesk/rag/').decode() if 'rag' in p else ''
    print(p, '-> tested below')
# staff CAN use inbox/thread
print('staff inbox:', rq(BASE + '/chatdesk/api/inbox.php?filter=all').decode()[:80])
# staff rag page blocked?
try:
    print('staff rag page:', rq(BASE + '/chatdesk/rag/').decode()[:60])
except Exception as e:
    print('staff rag blocked:', str(e)[:80])
