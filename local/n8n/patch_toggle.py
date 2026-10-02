import urllib.request, json, os, sys
BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
import http.cookiejar
cj = http.cookiejar.MozillaCookieJar(CJ)
cj.load(CJ, ignore_discard=True, ignore_expires=True)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def call(method, path, obj=None):
    data = json.dumps(obj).encode() if obj is not None else None
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                                 method=method)
    try:
        return json.loads(op.open(req, timeout=120).read())
    except Exception as e:
        body = ''
        try:
            body = e.read().decode()[:400]
        except Exception:
            pass
        return {'_err': str(e)[:150], '_body': body}

TARGETS = [
    ('rag-03-ingest.json', 'zudtl8dVs8TfcUBj'),
    ('rag-04-answer.json', 'RKrBD4TtzMNsRtEk'),
    ('api-10-voice.json', 'ZJQRxPRCyMi6Nszd'),
]
if len(sys.argv) > 1:
    TARGETS = [(sys.argv[1], sys.argv[2])]

for fn, wid in TARGETS:
    wf = json.load(open(os.path.join(r'C:\Users\pol\Desktop\OpenCode Project\ChatDesk\local\n8n', fn), encoding='utf-8'))
    call('POST', '/rest/workflows/%s/deactivate' % wid)
    r = call('PATCH', '/rest/workflows/' + wid,
             {'name': wf['name'], 'nodes': wf['nodes'], 'connections': wf['connections'],
              'settings': wf.get('settings', {})})
    d = r.get('data', r)
    g = call('GET', '/rest/workflows/' + wid).get('data', {})
    a = call('POST', '/rest/workflows/%s/activate' % wid, {'versionId': g.get('versionId')})
    ad = a.get('data', a)
    print(fn, '| patch id:', d.get('id'), '| err:', d.get('_err'), d.get('_body'), '| active:', ad.get('active'), a.get('_err'), a.get('_body'))
