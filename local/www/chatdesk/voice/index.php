<?php
// ChatDesk LOCAL — AI Setting: เลือก engine รายกิจกรรม (เฉพาะ ADMIN)
// อ่าน/เขียนผ่าน n8n api-voice (engine) เท่านั้น — PHP ไม่แตะตาราง app_settings ตรง
require_once __DIR__ . '/../inc/bootstrap.php';
$me = cd_current_user();
if (!$me) { header('Location: ../index.php'); exit; }
if (!cd_is_admin()) { http_response_code(403); echo 'เฉพาะกลุ่ม ADMIN'; exit; }
?>
<!doctype html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>AI Setting • <?= e($CFG['app']['title']) ?></title>
<link rel="icon" href="../assets/omnidesk-icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../assets/css/app.css?v=<?= cd_asset_ver('assets/css/app.css') ?>">
<style>
.wrap{max-width:720px;margin:24px auto;padding:0 16px}
.card{background:#fff;border-radius:14px;padding:18px;margin-bottom:16px;box-shadow:0 2px 10px rgba(0,0,0,.06)}
.btn{background:#287dfa;color:#fff;border:0;border-radius:8px;padding:8px 14px;cursor:pointer;font-weight:700}
.btn.green{background:#00a651}
select{border:1.5px solid #dfe4ee;border-radius:8px;padding:8px 10px;font-size:14px;min-width:280px}
select:disabled{background:#eef2f9;color:#667}
.topnav{margin-bottom:12px}.topnav a{color:#287dfa;font-weight:700;text-decoration:none;margin-right:12px}
.muted{color:#667;font-size:13px}
.msg{margin-left:10px;font-weight:700}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{border-bottom:1px solid #eef1f6;padding:8px 6px;text-align:left;vertical-align:middle}
</style></head>
<body style="background:#f3f5f9;font-family:'IBM Plex Sans Thai',system-ui,sans-serif">
<div class="wrap">
  <div class="topnav"><a href="../index.php">← กลับกล่องข้อความ</a><a href="../rag/">🧠 RAG System</a><a href="../users/">👥 จัดการผู้ใช้</a></div>
  <div class="card"><h2 style="margin:0 0 4px"><img src="../assets/omnidesk-icon.svg" alt="" style="height:1.1em;vertical-align:-0.15em"> AI Setting</h2>
    <p class="muted" style="margin:0">เฉพาะกลุ่ม ADMIN • เลือก engine ได้รายกิจกรรม มีผลทั้งเสียง TripThai และบอท LINE (ผ่าน n8n engine)</p></div>

  <div class="card"><h3>เลือก engine รายกิจกรรม</h3>
    <table>
      <tr><th>กิจกรรม</th><th>engine</th><th></th></tr>
      <tr><td>💬 ตอบคำถาม<br><small class="muted">RAG + แชท + LINE</small></td>
        <td><select id="f-llm-qa">
          <option value="gemini">Gemini 2.5 Flash (Public) — แนะนำ</option>
          <option value="qwen3:4b">Qwen3 4B (Local)</option>
        </select></td>
        <td><button class="btn green" onclick="saveKey('llm.qa','f-llm-qa','m-llm-qa')">บันทึก</button><span class="msg" id="m-llm-qa"></span></td></tr>
      <tr><td>🔊 อ่านออกเสียง (TTS)<br><small class="muted">auto = neural ก่อน ตก Piper</small></td>
        <td><select id="f-tts">
          <option value="auto">Auto (neural → Piper)</option>
          <option value="neural">Neural เท่านั้น</option>
          <option value="piper">Piper เท่านั้น</option>
        </select></td>
        <td><button class="btn green" onclick="saveKey('tts.engine','f-tts','m-tts')">บันทึก</button><span class="msg" id="m-tts"></span></td></tr>
      <tr><td>📄 OCR เอกสาร<br><small class="muted">PDF/รูป → ข้อความ</small></td>
        <td><select id="f-ocr">
          <option value="gemini">Gemini (Public) — แม่นสุด</option>
          <option value="easyocr">EasyOCR Thai (Local)</option>
        </select></td>
        <td><button class="btn green" onclick="saveKey('ocr.engine','f-ocr','m-ocr')">บันทึก</button><span class="msg" id="m-ocr"></span></td></tr>
      <tr><td>🧩 Embedding</td>
        <td><select disabled><option>Gemini 768 มิติ</option></select></td>
        <td><small class="muted">ล็อก (vector คนละ space ผสมไม่ได้)</small></td></tr>
      <tr><td>🎤 แปลงเสียง (STT)</td>
        <td><select disabled><option>whisper-large-v3-turbo (local)</option></select></td>
        <td><small class="muted">ล็อก</small></td></tr>
      <tr><td>🔑 Gemini API Key<br><small class="muted">ใช้ทุกเส้น Gemini (OCR/embed/ตอบคำถาม/AI chat)</small></td>
        <td><input type="password" id="f-gkey" placeholder="วาง key ใหม่ที่นี่" autocomplete="off" style="width:100%;max-width:280px"><br>
          <small class="muted">ปัจจุบัน: <span id="f-gkey-mask">…</span></small></td>
        <td><button class="btn green" onclick="saveGkey()">บันทึก</button><span class="msg" id="m-gkey"></span></td></tr>
    </table></div>
</div>
<script>
var CSRF = <?= json_encode($csrf = cd_csrf_token()) ?>;
async function api(path, body){
  var r = await fetch(path, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(Object.assign({csrf:CSRF}, body||{})) });
  return r.json();
}
async function loadAll(){
  try{
    var r = await api('api/setting.php', {op:'get'});
    if(r && r.ok && r.settings){
      document.getElementById('f-llm-qa').value = r.settings['llm.qa'] || 'gemini';
      document.getElementById('f-tts').value = r.settings['tts.engine'] || 'auto';
      document.getElementById('f-ocr').value = r.settings['ocr.engine'] || 'gemini';
      document.getElementById('f-gkey-mask').textContent = r.settings['gemini.api_key_masked'] || '(ยังไม่ตั้ง)';
    }
  }catch(e){}
}
async function saveGkey(){
  var m = document.getElementById('m-gkey'); m.textContent = 'กำลังบันทึก…';
  try{
    var inp = document.getElementById('f-gkey');
    var r = await api('api/setting.php', {op:'set', key:'gemini.api_key', value:inp.value});
    if(r && r.ok){
      m.textContent = '✓ บันทึกแล้ว' + (r.credential_updated === false ? ' (แต่หมุน credential ไม่สำเร็จ: '+(r.error||'')+')' : '');
      inp.value = '';
      if(r.value) document.getElementById('f-gkey-mask').textContent = r.value;
    } else {
      m.textContent = '❌ '+((r && r.error)||'');
    }
  }catch(e){ m.textContent = 'เชื่อมต่อไม่ได้'; }
}
async function saveKey(key, fid, mid){
  var m = document.getElementById(mid); m.textContent = 'กำลังบันทึก…';
  try{
    var r = await api('api/setting.php', {op:'set', key:key, value:document.getElementById(fid).value});
    m.textContent = (r && r.ok) ? '✓ บันทึกแล้ว' : ('❌ '+((r && r.error)||''));
  }catch(e){ m.textContent = 'เชื่อมต่อไม่ได้'; }
}
loadAll();
</script>
</body></html>
