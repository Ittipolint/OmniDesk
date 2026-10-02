import urllib.request, json, os
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
            body = e.read().decode()[:500]
        except Exception:
            pass
        return {'_err': str(e)[:200], '_body': body}

import sys
fn = sys.argv[1] if len(sys.argv) > 1 else 'rag-03-ingest.json'
wid = sys.argv[2] if len(sys.argv) > 2 else 'zudtl8dVs8TfcUBj'
wf = json.load(open(os.path.join(r'C:\Users\pol\Desktop\OpenCode Project\ChatDesk\local\n8n', fn), encoding='utf-8'))
# PUT full workflow (keep server id out; name+nodes+connections+settings)
r = call('PATCH', '/rest/workflows/' + wid,
         {'name': wf['name'], 'nodes': wf['nodes'], 'connections': wf['connections'],
          'settings': wf.get('settings', {})})
d = r.get('data', r)
print('update:', d.get('id'), '| version:', d.get('versionId'), '| err:', d.get('_err'), d.get('_body'))
