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

def save(name, obj):
    open(os.path.join(OUT, name + '.json'), 'w', encoding='utf-8').write(
        json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True))
    print('saved', name)

# 1) incoming new user
r = rq(BASE + '/chatdesk/api/incoming.php',
       data=json.dumps({'userId': 'WEB_DIFFTEST', 'channel': 'web', 'text': 'diff baseline msg',
                        'displayName': 'Diff Tester', 'messageId': 'WEB_DIFF_001'}).encode(),
       headers={'Content-Type': 'application/json'})
save('incoming', json.loads(r))

# 2) webthread
save('webthread', json.loads(rq(BASE + '/chatdesk/api/webthread.php?userId=WEB_DIFFTEST&since=0')))

# 3) login as admin
login = urllib.parse.urlencode({'login_user': 'admin', 'login_pass': '10203040'}).encode()
rq(BASE + '/chatdesk/index.php', data=login, headers={'Content-Type': 'application/x-www-form-urlencoded'})
html = rq(BASE + '/chatdesk/rag/')
csrf = re.search(r'var CSRF = "([a-f0-9]+)"', html).group(1)

def api(path, obj):
    return json.loads(rq(BASE + path, data=json.dumps(obj).encode(),
                         headers={'Content-Type': 'application/json'}))

save('inbox', json.loads(rq(BASE + '/chatdesk/api/inbox.php?filter=all')))
save('thread', json.loads(rq(BASE + '/chatdesk/api/thread.php?id=1&since=0')))
save('users_list', api('/chatdesk/users/api/list.php', {'csrf': csrf}))
save('rag_groups', api('/chatdesk/rag/api/groups.php', {'csrf': csrf, 'op': 'list'}))
save('rag_stats', api('/chatdesk/rag/api/stats.php', {'csrf': csrf}))
print('BASELINE DONE')
