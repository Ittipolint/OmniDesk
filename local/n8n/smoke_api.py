import urllib.request, json
BASE = 'http://127.0.0.1:5678'
def post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=90).read())

print('receive:', str(post('/webhook/api-receive', {'messageId': 9951, 'channel': 'web', 'sender': 'customer', 'content': 'webthread probe', 'externalUserId': 'WEB_N8NTEST', 'displayName': 'Engine Tester', 'skipAvatar': True}))[:160])
print('inbox:', str(post('/webhook/api-read', {'resource': 'inbox', 'filter': 'open'}))[:260])
print('webthread:', str(post('/webhook/api-read', {'resource': 'webthread', 'userId': 'WEB_N8NTEST', 'since': 0}))[:500])
print('users-list:', str(post('/webhook/api-users', {'op': 'list'}))[:200])
print('users-groups:', str(post('/webhook/api-users', {'op': 'list-groups'}))[:200])
print('ragmeta-stats:', str(post('/webhook/api-ragmeta', {'op': 'stats'}))[:200])
