import urllib.request, http.cookiejar, json, re, urllib.parse, os
BASE = 'http://127.0.0.1:8081'
BL = r'C:\Users\pol\AppData\Local\Temp\opencode\baseline'
cj = http.cookiejar.MozillaCookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def rq(url, data=None, headers=None):
    h = {'User-Agent': 'Mozilla/5.0'}
    if headers:
        h.update(headers)
    return op.open(urllib.request.Request(url, data=data, headers=h), timeout=90).read().decode()
def load(n):
    return json.load(open(os.path.join(BL, n + '.json'), encoding='utf-8'))
rep = []
def check(name, cond, detail=''):
    rep.append(('PASS' if cond else 'DIFF') + ' ' + name + (' :: ' + str(detail)[:220] if detail and not cond else ''))

# 1) incoming (duplicate expected — same messageId as baseline)
r = json.loads(rq(BASE + '/chatdesk/api/incoming.php',
    data=json.dumps({'userId': 'WEB_DIFFTEST', 'channel': 'web', 'text': 'diff baseline msg',
                     'displayName': 'Diff Tester', 'messageId': 'WEB_DIFF_001'}).encode(),
    headers={'Content-Type': 'application/json'}))
b = load('incoming')
check('incoming.ok', r.get('ok') is True, r)
check('incoming.convId', r.get('conversationId') == b.get('conversationId'), r)

# 2) webthread — must contain baseline message ids
w = json.loads(rq(BASE + '/chatdesk/api/webthread.php?userId=WEB_DIFFTEST&since=0'))
bw = load('webthread')
bids = set(m['id'] for m in bw.get('messages', []))
nids = set(m['id'] for m in w.get('messages', []))
check('webthread.ok', w.get('ok') is True, w)
check('webthread.convId', w.get('conversationId') == bw.get('conversationId'), w)
check('webthread.msgs-superset', bids <= nids, 'base=%s now=%s' % (sorted(bids), sorted(nids)))
check('webthread.keys', set(w.get('messages', [{}])[0].keys() if w.get('messages') else {}) == set(bw.get('messages', [{}])[0].keys() if bw.get('messages') else {}), '')

# login
login = urllib.parse.urlencode({'login_user': 'admin', 'login_pass': '10203040'}).encode()
rq(BASE + '/chatdesk/index.php', data=login, headers={'Content-Type': 'application/x-www-form-urlencoded'})
html = rq(BASE + '/chatdesk/rag/')
csrf = re.search(r'var CSRF = "([a-f0-9]+)"', html).group(1)
def api(path, obj):
    return json.loads(rq(BASE + path, data=json.dumps(obj).encode(), headers={'Content-Type': 'application/json'}))

# 3) inbox — baseline conv ids must still be present with same keys
ib = load('inbox')
ic = json.loads(rq(BASE + '/chatdesk/api/inbox.php?filter=all'))
bids = set(x['id'] for x in ib.get('items', []))
nids = set(x['id'] for x in ic.get('items', []))
check('inbox.ok', ic.get('ok') is True, ic)
check('inbox.convs-superset', bids <= nids, 'base=%s now=%s' % (sorted(bids), sorted(nids)))
bk = set(ib['items'][0].keys()) if ib.get('items') else set()
nk = set(ic['items'][0].keys()) if ic.get('items') else set()
check('inbox.item-keys', bk == nk, 'base=%s now=%s' % (bk, nk))
check('inbox.counts-keys', set(ib.get('counts', {}).keys()) == set(ic.get('counts', {}).keys()), '')

# 4) thread id=1 — conv shape + remaining msgs (msg 13 was deleted by engine test)
t = json.loads(rq(BASE + '/chatdesk/api/thread.php?id=1&since=0'))
bt = load('thread')
check('thread.ok', t.get('ok') is True, t)
check('thread.conv-same', t.get('conversation') == bt.get('conversation'), 'now=%s' % json.dumps(t.get('conversation'), ensure_ascii=False)[:200])
bm = set(m['id'] for m in bt.get('messages', [])) - {13}
nm = set(m['id'] for m in t.get('messages', []))
check('thread.msgs', bm <= nm, 'expect-minus13=%s now=%s' % (sorted(bm), sorted(nm)))

# 5) users_list — baseline usernames present, same keys
u = api('/chatdesk/users/api/list.php', {'csrf': csrf})
bu = load('users_list')
bun = set(x['username'] for x in bu.get('users', []))
nun = set(x['username'] for x in u.get('users', []))
check('users.ok', u.get('ok') is True, u)
check('users.superset', bun <= nun, '')
check('users.keys', set(bu['users'][0].keys()) == set(u['users'][0].keys()), '')

# 6) rag groups + stats
g = api('/chatdesk/rag/api/groups.php', {'csrf': csrf, 'op': 'list'})
bg = load('rag_groups')
bgn = set(x['name'] for x in bg.get('groups', []))
ngn = set(x['name'] for x in g.get('groups', []))
check('rag-groups.ok', g.get('ok') is True, g)
check('rag-groups.names', bgn <= ngn, 'base=%s now=%s' % (bgn, ngn))
s = api('/chatdesk/rag/api/stats.php', {'csrf': csrf})
check('rag-stats.ok', s.get('ok') is True, s)
check('rag-stats.keys', set(s.keys()) == {'ok', 'sources', 'chunks', 'images', 'groups'}, set(s.keys()))
check('rag-stats.groups', isinstance(s.get('groups'), list) and all(set(g.keys()) == {'name', 'chunks'} for g in s['groups']), s)

print('\n'.join(rep))
print('RESULT:', 'ALL PASS' if all(x.startswith('PASS') for x in rep) else 'HAS DIFFS')
