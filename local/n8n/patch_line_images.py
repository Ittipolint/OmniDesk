"""Patch [LOCAL] ChatDesk Manager - LINE: send RAG images as LINE image messages (public https only)."""
import urllib.request, json, http.cookiejar

BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
cj = http.cookiejar.MozillaCookieJar(CJ)
cj.load(CJ, ignore_discard=True, ignore_expires=True)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
WID = 'DPXcIEfqSaxmbLV3'


def call(method, path, obj=None):
    data = json.dumps(obj).encode() if obj is not None else None
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                                 method=method)
    try:
        return json.loads(op.open(req, timeout=120).read())
    except Exception as e:
        try:
            body = e.read().decode('utf-8', 'replace')[:400]
        except Exception:
            body = str(e)[:200]
        return {'_err': getattr(e, 'code', '?'), '_body': body}


ATTACH_JS = """const items = $input.all().map(r => r.json);
const orig = items.find(r => r.text !== undefined && r.ok === undefined) || {};
const rag = items.find(r => r.ok !== undefined) || {};
const rc = (rag.text || '').toString();
const rimgs = Array.isArray(rag.images) ? rag.images.map(u => (u || '').toString().trim()).filter(u => u !== '') : [];
return [{ json: { ...orig, rag_context: rc, rag_sources: rag.sources || [], rag_images: rimgs } }];"""

REPLY_JS = """/* Take AI/LLM output, attach userId, carry RAG image URLs (public https only, max 4) */
const items = $input.all();
const out = [];
let imgs = [];
try { imgs = ($('Attach RAG').first().json.rag_images || []); } catch (err) { imgs = []; }
if (!Array.isArray(imgs)) imgs = [];
const seen = {};
imgs = imgs.map(u => (u || '').toString().trim()).filter(u => /^https:\\/\\//i.test(u) && !seen[u] && (seen[u] = 1)).slice(0, 4);
for (let i = 0; i < items.length; i++) {
  let userId = '';
  try { userId = $('Send to ChatDesk').itemMatching(i).json.userId || ''; } catch (err) { userId = ''; }
  const raw = items[i].json.output || items[i].json.text || '';
  const replyText = String(raw).replace(/<think>[\\s\\S]*?<\\/think>/g, '').trim();
  if (userId && replyText) { out.push({ json: { userId: userId, replyText: replyText, images: imgs } }); }
}
return out;"""

PUSH_BODY = ("={{ {to: $json.userId, messages: [{type: 'text', text: $json.replyText}]"
               ".concat((($json.images || []).slice(0, 4)).map(u => ({type: 'image', originalContentUrl: u, previewImageUrl: u}))) } }}")

SEND_TEXT = "={{ $json.replyText + (($json.images || []).length ? '\\n' + $json.images.join('\\n') : '') }}"

w = call('GET', '/rest/workflows/' + WID).get('data', {})
nodes = {n['name']: n for n in w.get('nodes', [])}
assert 'Attach RAG' in nodes and 'Build Reply' in nodes and 'Push LINE' in nodes and 'Send LINE' in nodes, 'node missing'

nodes['Attach RAG']['parameters']['jsCode'] = ATTACH_JS
nodes['Build Reply']['parameters']['jsCode'] = REPLY_JS
nodes['Push LINE']['parameters']['jsonBody'] = PUSH_BODY
msgs = nodes['Send LINE']['parameters'].get('messages', {}).get('values', [])
assert msgs and 'text' in msgs[0], 'Send LINE shape unexpected: %s' % json.dumps(msgs)[:200]
msgs[0]['text'] = SEND_TEXT

call('POST', '/rest/workflows/%s/deactivate' % WID)
r = call('PATCH', '/rest/workflows/' + WID,
         {'name': w['name'], 'nodes': w.get('nodes', []),
          'connections': w.get('connections', {}), 'settings': w.get('settings', {})})
d = r.get('data', r)
g = call('GET', '/rest/workflows/' + WID).get('data', {})
a = call('POST', '/rest/workflows/%s/activate' % WID, {'versionId': g.get('versionId')})
print('patch id:', d.get('id'), '| err:', d.get('_err'), d.get('_body'),
      '| active:', a.get('data', a).get('active'))
