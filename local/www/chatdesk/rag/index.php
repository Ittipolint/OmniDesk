<?php
// ChatDesk LOCAL — RAG System: นำเข้าข้อมูล + ทดสอบถามตอบ (เฉพาะ ADMIN)
require_once __DIR__ . '/../inc/bootstrap.php';
$me = cd_current_user();
if (!$me) { header('Location: ../index.php'); exit; }
if (!cd_is_admin()) { http_response_code(403); echo 'เฉพาะกลุ่ม ADMIN'; exit; }
?>
<!doctype html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>RAG System • <?= e($CFG['app']['title']) ?></title>
<link rel="icon" href="../assets/omnidesk-icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../assets/css/app.css?v=<?= cd_asset_ver('assets/css/app.css') ?>">
<style>
.wrap{max-width:1024px;margin:24px auto;padding:0 16px}
.card{background:#fff;border-radius:14px;padding:18px;margin-bottom:16px;box-shadow:0 2px 10px rgba(0,0,0,.06)}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{border-bottom:1px solid #eef1f6;padding:8px 10px;text-align:left;vertical-align:top}
.btn{background:#287dfa;color:#fff;border:0;border-radius:8px;padding:8px 14px;cursor:pointer;font-weight:700}
.btn.green{background:#00a651}.btn.red{background:#ff5b5b}.btn.ghost{background:#eef2f9;color:#333}
input,select,textarea{border:1.5px solid #dfe4ee;border-radius:8px;padding:8px 10px;font-size:14px;font-family:inherit}
textarea{width:100%;min-height:120px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:end}
.topnav{margin-bottom:12px}.topnav a{color:#287dfa;font-weight:700;text-decoration:none;margin-right:12px}
.tabs{display:flex;gap:6px;margin:8px 0}
.tabs button{border:1px solid #d6e2ff;background:#f2f6ff;border-radius:10px;padding:6px 14px;cursor:pointer;font-weight:700}
.tabs button.on{background:#287dfa;color:#fff}
.answer{background:#f6f8ff;border-radius:10px;padding:12px;margin-top:10px;font-size:14px;line-height:1.7;white-space:pre-wrap}
.answer img{max-width:100%;border-radius:10px;margin-top:8px}
.src{font-size:12px;color:#667}
.spin{display:inline-block;animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
</style></head>
<body style="background:#f3f5f9;font-family:'IBM Plex Sans Thai',system-ui,sans-serif">
<div class="wrap">
  <div class="topnav"><a href="../index.php">← กลับกล่องข้อความ</a><a href="../users/">👥 จัดการผู้ใช้</a></div>
  <div class="card"><h2 style="margin:0 0 4px"><img src="../assets/omnidesk-icon.svg" alt="" style="height:1.1em;vertical-align:-0.15em"> RAG System</h2>
    <p style="margin:0;color:#667;font-size:13px">นำเข้าข้อมูลทุกแบบ (ข้อความ / PDF+OCR / รูป+คำบรรยาย / URL) → Embedding ด้วย Gemini (768 มิติ) → Vector DB (Postgres+pgvector) — จัดเป็นกลุ่ม ถามได้ทั้งข้อความและรูป</p>
    <div id="stats" style="margin-top:8px;font-size:13px">กำลังโหลดสถิติ…</div></div>

  <div class="card"><h3>📁 RAG Group</h3>
    <div class="row"><div><label>ชื่อกลุ่มใหม่<br><input id="g_name" placeholder="เช่น hotel"></label></div>
    <div><label>คำอธิบาย<br><input id="g_desc" placeholder="เช่น ข้อมูลโรงแรมในเครือ"></label></div>
    <div><br><button class="btn" onclick="addGroup()">เพิ่มกลุ่ม</button></div></div>
    <div id="groupList" style="margin-top:10px"></div></div>

  <div class="card"><h3>📄 เอกสารในกลุ่ม (ลบรายชิ้น)</h3>
    <div class="row"><div><label>กลุ่ม<br><select id="s_group" onchange="loadSources()"></select></label></div>
    <div><br><button class="btn" onclick="loadSources()">รีเฟรช</button></div></div>
    <div id="srcList" style="margin-top:8px">เลือกกลุ่มเพื่อดูเอกสาร…</div></div>

  <div class="card"><h3>🔀 ช่องทาง (1 ช่องทาง : 1 กลุ่ม RAG)</h3>
    <p class="muted" style="margin:0 0 8px;color:#667;font-size:13px">LINE แยกตาม OA (destination) • web แยกตามเว็บ • token เว้นว่าง = ไม่เปลี่ยน • ช่องที่ไม่ active จะไม่รับสายใหม่</p>
    <div id="chList" style="margin-top:6px">กำลังโหลด…</div></div>

  <div class="card"><h3>📥 นำเข้าข้อมูล (Embedding)</h3>
    <div class="row">
      <div><label>กลุ่ม<br><select id="i_group"></select></label></div>
      <div><label>หัวข้อ<br><input id="i_title" placeholder="เช่น โปรโมชั่นเดือนนี้" style="min-width:240px"></label></div>
    </div>
    <div class="tabs" id="typeTabs">
      <button data-t="text" class="on" onclick="setType('text')">📝 ข้อความ/FAQ</button>
      <button data-t="pdf" onclick="setType('pdf')">📄 PDF (OCR อัตโนมัติ)</button>
      <button data-t="image" onclick="setType('image')">🖼️ รูปภาพ</button>
      <button data-t="url" onclick="setType('url')">🔗 ลิงก์/URL</button>
    </div>
    <div id="pane-text"><textarea id="i_text" placeholder="วางข้อความหรือคำถาม-คำตอบที่นี่…"></textarea></div>
    <div id="pane-pdf" hidden><input type="file" id="i_pdf" accept=".pdf,application/pdf"><br><small>PDF จะถูก OCR (engine ตามที่เลือกใน ⚙️ AI Setting) แล้วแบ่ง chunk เข้า Vector DB</small></div>
    <div id="pane-image" hidden>
      <div>URL รูป (public HTTPS เท่านั้น — ใช้อ้างอิงแสดงผลในแชท/LINE):<br><input id="i_imgurl" placeholder="https://…/pic.jpg" style="min-width:320px"></div>
      <textarea id="i_caption" style="min-height:60px" placeholder="คำบรรยายรูป (ถ้าเว้นว่าง AI จะพากย์ภาพ+OCR ให้เอง)"></textarea>
    </div>
    <div id="pane-url" hidden><input id="i_url" placeholder="https://…" style="min-width:320px"><br><small>ดึงเนื้อหาหน้าเว็บมา embedding (text หลักของหน้า)</small></div>
    <div style="margin-top:10px"><button class="btn green" id="btnIngest" onclick="doIngest()">⬆️ นำเข้า + Embedding</button> <span id="ingestMsg"></span></div>
  </div>

  <div class="card"><h3>🔍 ทดสอบถามตอบ (RAG)</h3>
    <div class="row">
      <div><label>กลุ่ม (เว้นว่าง = ทุกกลุ่ม)<br><select id="q_group"><option value="">ทุกกลุ่ม</option></select></label></div>
      <div style="flex:1;min-width:240px"><label>คำถาม<br><input id="q_text" placeholder="เช่น ยกเลิกฟรีไหม" style="width:100%"></label></div>
      <div><br><button class="btn" id="btnAsk" onclick="doAsk()">ถาม</button></div>
    </div>
    <div id="answer" class="answer" hidden></div>
  </div>
</div>
<div class="toast" id="toast" hidden></div>
<script>
var CSRF = <?= json_encode(cd_csrf_token()) ?>;
var curType = 'text';
function toast(m){ var t=document.getElementById('toast'); t.textContent=m; t.hidden=false; clearTimeout(t._h); t._h=setTimeout(function(){t.hidden=true},3000); }
async function api(path, body, isForm){
  var opt = { method:'POST', body: body };
  if(!isForm){ opt.headers = {'Content-Type':'application/json'}; opt.body = JSON.stringify(Object.assign({csrf:CSRF}, body||{})); }
  else { if(body instanceof FormData) body.append('csrf', CSRF); }
  var r = await fetch(path, opt);
  return r.json();
}
function setType(t){
  curType = t;
  Array.prototype.forEach.call(document.querySelectorAll('#typeTabs button'), function(b){ b.classList.toggle('on', b.dataset.t===t); });
  ['text','pdf','image','url'].forEach(function(k){ document.getElementById('pane-'+k).hidden = (k!==t); });
}
async function load(){
  var g = await api('api/groups.php', {op:'list'});
  if(!g.ok){ toast(g.error||'โหลดกลุ่มไม่สำเร็จ'); return; }
  document.getElementById('groupList').innerHTML = g.groups.map(function(x){
    var prot = ' <button class="btn ghost" onclick="delGroup('+x.id+')">ลบ</button>';
    return '<div style="margin-bottom:10px">• <b>'+x.name+'</b> — '+x.description+' <small>('+x.chunks+' chunks)</small>'+prot+'</div>';
  }).join('');
  var opts = g.groups.map(function(x){ return '<option value="'+x.id+'">'+x.name+'</option>'; }).join('');
  document.getElementById('i_group').innerHTML = opts;
  document.getElementById('s_group').innerHTML = opts;
  loadSources();
  document.getElementById('q_group').innerHTML = '<option value="">ทุกกลุ่ม</option>' + opts;
  var s = await api('api/stats.php', {});
  if(s.ok){ document.getElementById('stats').innerHTML = '📚 '+s.sources+' แหล่งข้อมูล • 🧩 '+s.chunks+' chunks • 🖼️ '+s.images+' รูป • กลุ่ม: ' + s.groups.map(function(x){return x.name+'('+x.chunks+')'}).join(', '); }
  loadChannels(g.groups);
}

async function loadChannels(groups){
  var box = document.getElementById('chList');
  var r = await api('api/channels.php', {op:'list'});
  if(!r.ok){ box.textContent = 'โหลดไม่สำเร็จ: '+(r.error||''); return; }
  var gopts = (groups||[]).map(function(g){ return '<option value="'+g.id+'">'+g.name+'</option>'; }).join('');
  var gchecks = function(pid, sel){ return (groups||[]).map(function(g){
    return '<label style="white-space:nowrap;margin-right:8px"><input type="checkbox" data-chg="'+pid+'" value="'+g.id+'"'+(sel.indexOf(g.id)>=0?' checked':'')+'> '+g.name+'</label>'; }).join(''); };
  var gidsOf = function(c){
    var a = c.group_ids;
    try { if (typeof a === 'string') a = JSON.parse(a || '[]'); } catch(e){ a = []; }
    if (Array.isArray(a)) return a.map(function(x){ return parseInt(x); }).filter(function(x){ return x > 0; });
    return c.rag_group_id ? [parseInt(c.rag_group_id)] : [];
  };
  box.innerHTML = '<div style="overflow-x:auto"><table style="min-width:960px"><tr><th>Channel code</th><th>Channel Name</th><th>RAG groups (เลือกได้หลายกลุ่ม)</th><th>LINE bot</th><th>token</th><th>active</th><th>น้ำเสียงบอท (ของช่องทางนี้)</th><th></th></tr>' + r.channels.map(function(c){
    return '<tr><td><b>'+c.channel_code+'</b></td>'
      + '<td><input id="ch-label-'+c.channel_code+'" value="'+(c.label||'')+'" style="width:110px"></td>'
      + '<td style="min-width:210px"><span id="ch-groups-'+c.channel_code+'">'+gchecks(c.channel_code, gidsOf(c))+'</span></td>'
      + '<td><input id="ch-bot-'+c.channel_code+'" value="'+(c.line_bot_id||'')+'" placeholder="U…" style="width:100px"></td>'
      + '<td style="white-space:nowrap">'+(c.has_token?'•••มีแล้ว':'—ว่าง—')+' <input id="ch-tok-'+c.channel_code+'" type="password" placeholder="เว้นว่าง=ไม่เปลี่ยน" style="width:110px"></td>'
      + '<td><select id="ch-act-'+c.channel_code+'"><option value="1">เปิด</option><option value="0">ปิด</option></select></td>'
      + '<td><textarea id="ch-persona-'+c.channel_code+'" placeholder="น้ำเสียงบอทช่องนี้ (เว้นว่าง = ใช้ค่ากลาง)" style="min-height:40px;width:170px">'+((c.persona_system||'').replace(/</g,'&lt;'))+'</textarea></td>'
      + '<td style="white-space:nowrap"><button class="btn ghost" id="ch-save-'+c.channel_code+'" onclick="saveChannel(\''+c.channel_code+'\')">บันทึก</button><br><button class="btn ghost" onclick="delChannel(\''+c.channel_code+'\')" style="margin-top:4px">ลบ</button></td></tr>';
  }).join('') + '</table></div>'
  + '<div style="margin-top:10px">＋ เพิ่มช่องทาง: '
  + 'Channel code <input id="ch-new-code" placeholder="a-z 0-9 _" style="width:110px"> '
  + 'Channel Name <input id="ch-new-label" placeholder="Channel Name" style="width:120px"> '
  + 'RAG <span id="ch-new-groups">'+gchecks('__new__', [])+'</span> '
  + 'LINE bot <input id="ch-new-bot" placeholder="U…" style="width:110px"> '
  + 'token <input id="ch-new-tok" type="password" placeholder="เว้นว่างได้" style="width:110px"> '
  + 'active <select id="ch-new-act"><option value="1">เปิด</option><option value="0">ปิด</option></select><br>'
  + 'น้ำเสียงบอท <textarea id="ch-new-persona" placeholder="น้ำเสียงบอทช่องนี้ (เว้นว่าง = ใช้ค่ากลาง)" style="min-height:40px;width:320px"></textarea> '
  + '<button class="btn" onclick="addChannel()">เพิ่มช่องทาง</button></div>';
  r.channels.forEach(function(c){
    document.getElementById('ch-act-'+c.channel_code).value = c.is_active ? '1' : '0';
  });
}
function checkedGroups(pid){
  var out = [];
  Array.prototype.forEach.call(document.querySelectorAll('input[data-chg="'+pid+'"]'), function(b){ if(b.checked) out.push(parseInt(b.value)); });
  return out;
}
async function saveChannel(code){
  var btn = document.getElementById('ch-save-'+code);
  if(btn){ btn.disabled = true; btn.textContent = '…'; }
  try {
    var body = {op:'set', channel:code,
      label:document.getElementById('ch-label-'+code).value,
      group_ids:checkedGroups(code),
      persona_system:document.getElementById('ch-persona-'+code).value,
      line_bot_id:document.getElementById('ch-bot-'+code).value,
      is_active:document.getElementById('ch-act-'+code).value};
    var tok = document.getElementById('ch-tok-'+code).value;
    if(tok) body.line_channel_token = tok;
    var r = await api('api/channels.php', body);
    var msg = r.ok ? ('บันทึก '+code+' แล้ว') : ('❌ '+(r.error||''));
    if(r.ok && r.resolved_bot){ msg += ' (เจอ bot ' + r.resolved_bot + ' อัตโนมัติ)'; }
    toast(msg);
    if(r.ok) load(); else if(btn){ btn.disabled = false; btn.textContent = 'บันทึก'; }
  } catch(e) {
    toast('❌ บันทึกไม่สำเร็จ: ' + (e && e.message ? e.message : e));
    if(btn){ btn.disabled = false; btn.textContent = 'บันทึก'; }
  }
}
async function addChannel(){
  var code = document.getElementById('ch-new-code').value.trim().toLowerCase();
  if(!/^[a-z0-9_]{2,32}$/.test(code)){ toast('รหัสช่องทาง a-z 0-9 _ ยาว 2–32'); return; }
  var body = {op:'add', channel:code,
    label:document.getElementById('ch-new-label').value,
    group_ids:checkedGroups('__new__'),
    persona_system:document.getElementById('ch-new-persona').value,
    line_bot_id:document.getElementById('ch-new-bot').value,
    is_active:document.getElementById('ch-new-act').value};
  var tok = document.getElementById('ch-new-tok').value;
  if(tok) body.line_channel_token = tok;
  var r = await api('api/channels.php', body);
  toast(r.ok ? ('เพิ่ม '+code+' แล้ว') : ('❌ '+(r.error||'')));
  if(r.ok) load();
}
async function delChannel(code){
  if(!confirm('ลบช่องทาง "'+code+'"? ประวัติแชทเดิมยังดูได้ แต่บอทจะไม่รับสายใหม่ของช่องนี้')) return;
  var r = await api('api/channels.php', {op:'delete', channel:code});
  toast(r.ok ? ('ลบ '+code+' แล้ว') : ('❌ '+(r.error||'')));
  if(r.ok) load();
}
async function addGroup(){
  var r = await api('api/groups.php', {op:'add', name:document.getElementById('g_name').value, description:document.getElementById('g_desc').value});
  toast(r.ok?'เพิ่มกลุ่มแล้ว':('ผิดพลาด: '+(r.error||'')));
  if(r.ok){ document.getElementById('g_name').value=''; document.getElementById('g_desc').value=''; load(); }
}
async function delGroup(id){ if(!confirm('ลบกลุ่มนี้พร้อมข้อมูลทั้งหมด?')) return; var r = await api('api/groups.php', {op:'delete', id:id}); toast(r.ok?'ลบแล้ว':r.error); if(r.ok) load(); }
async function loadSources(){
  var gid = document.getElementById('s_group').value;
  var box = document.getElementById('srcList');
  if(!gid){ box.textContent = 'เลือกกลุ่มเพื่อดูเอกสาร…'; return; }
  box.textContent = 'กำลังโหลด…';
  var r = await api('api/sources.php', {op:'listsources', group_id:parseInt(gid)});
  if(!r.ok){ box.textContent = 'โหลดไม่สำเร็จ: '+(r.error||''); return; }
  if(!r.sources.length){ box.innerHTML = '<small class="muted">กลุ่มนี้ยังไม่มีเอกสาร</small>'; return; }
  box.innerHTML = '<table><tr><th>#</th><th>หัวข้อ</th><th>ชนิด</th><th>chunks</th><th>นำเข้าเมื่อ</th><th></th></tr>' + r.sources.map(function(s){
    var t = (s.title||'(ไม่มีหัวข้อ)').replace(/</g,'&lt;');
    return '<tr><td>'+s.id+'</td><td>'+t+'</td><td>'+s.source_type+'</td><td>'+s.chunks+'</td><td><small>'+(s.created_at||'').slice(0,16).replace('T',' ')+'</small></td>'
      + '<td><button class="btn ghost" onclick="delSource('+s.id+','+gid+',this)">ลบ</button></td></tr>';
  }).join('') + '</table>';
}
async function delSource(id, gid, btn){
  if(!confirm('ลบเอกสาร #'+id+' พร้อม chunks ทั้งหมด? (ลบไฟล์รูปที่แนบด้วยถ้ามี)')) return;
  btn.disabled = true;
  var r = await api('api/sources.php', {op:'deletesource', id:id, group_id:gid});
  toast(r.ok ? ('ลบแล้ว'+(r.file_cleaned?' + เก็บไฟล์รูป':'')) : ('❌ '+(r.error||'')));
  if(r.ok) load();
}
async function doIngest(){
  var msg = document.getElementById('ingestMsg');
  msg.innerHTML = '<span class="spin">⏳</span> กำลังนำเข้า…';
  document.getElementById('btnIngest').disabled = true;
  try{
    var r;
    if(curType==='text' || curType==='url' || curType==='image'){
      if(curType==='image' && !/^https:\/\//i.test(document.getElementById('i_imgurl').value.trim())){
        toast('URL รูปต้องเป็น public HTTPS'); return;
      }
      r = await api('api/ingest.php', { type:curType, group_id:document.getElementById('i_group').value,
        title:document.getElementById('i_title').value,
        text: curType==='text' ? document.getElementById('i_text').value : (curType==='url' ? document.getElementById('i_url').value : document.getElementById('i_caption').value),
        image_url: curType==='image' ? document.getElementById('i_imgurl').value : undefined });
    }else{
      var fd = new FormData();
      fd.append('type', curType);
      fd.append('group_id', document.getElementById('i_group').value);
      fd.append('title', document.getElementById('i_title').value);
      if(curType==='pdf'){ var f=document.getElementById('i_pdf').files[0]; if(!f){ toast('เลือกไฟล์ PDF ก่อน'); return; } fd.append('file', f); }
      r = await api('api/ingest.php', fd, true);
    }
    msg.textContent = r.ok ? ('✅ ' + (r.message||'นำเข้าแล้ว')) : ('❌ ' + (r.error||'ผิดพลาด'));
    if(r.ok){ document.getElementById('i_text').value=''; document.getElementById('i_caption').value=''; document.getElementById('i_imgurl').value=''; document.getElementById('i_url').value=''; load(); }
  }finally{ document.getElementById('btnIngest').disabled = false; }
}
async function doAsk(){
  var box = document.getElementById('answer');
  box.hidden = false; box.innerHTML = '<span class="spin">⏳</span> กำลังค้นหาคำตอบ…';
  document.getElementById('btnAsk').disabled = true;
  try{
    var r = await api('api/ask.php', { question:document.getElementById('q_text').value, group_id:document.getElementById('q_group').value });
    if(!r.ok){ box.textContent = '❌ ' + (r.error||'ผิดพลาด'); return; }
    var h = r.text || '(ไม่มีคำตอบ)';
    (r.images||[]).forEach(function(u){ h += '\n[IMG]'+u; });
    box.innerHTML = '';
    h.split('\n').forEach(function(line){
      if(line.indexOf('[IMG]')===0){ var img=document.createElement('img'); img.src=line.slice(5); img.loading='lazy'; box.appendChild(img); }
      else { box.appendChild(document.createTextNode(line)); box.appendChild(document.createElement('br')); }
    });
    if((r.sources||[]).length){ var s=document.createElement('div'); s.className='src'; s.textContent='ที่มา: '+r.sources.join(' • '); box.appendChild(s); }
  }finally{ document.getElementById('btnAsk').disabled = false; }
}
document.getElementById('q_text').addEventListener('keydown', function(e){ if(e.key==='Enter') doAsk(); });
load();
</script>
</body></html>
