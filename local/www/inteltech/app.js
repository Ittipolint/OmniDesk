// ===== Intelligent Technology — corporate site + chatbot (RAG only) =====
var CH = 'intelweb'; // channel code (1 เว็บ : 1 channel) — เว็บใหม่ก๊อปไฟล์นี้ไปเปลี่ยนบรรทัดเดียว
var $ = function (id) { return document.getElementById(id); };
var esc = function (s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); };
function toast(m){ var t = $('toast'); if(!t) return; t.textContent = m; t.hidden = false; clearTimeout(t._h); t._h = setTimeout(function(){ t.hidden = true; }, 2800); }
async function postJSON(url, body){
  var r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  return r.json();
}
async function getJSON(url){ var r = await fetch(url); return r.json(); }
function guestId(){
  var key = CH + '_gid', id = '';
  try { id = localStorage.getItem(key) || ''; } catch (e) {}
  if (!/^WEB_[A-Za-z0-9_-]{1,64}$/.test(id)) {
    id = 'WEB_' + Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
    try { localStorage.setItem(key, id); } catch (e) {}
  }
  return id;
}

var chatHist = [], botOn = true, lastSeen = 0, pollT = null;
var spkOn = false, audioEl = null;
function toggleChat(force){
  var p = $('chatPanel');
  p.hidden = (force === undefined) ? !p.hidden : !force;
  if (!p.hidden && !pollT) { pollT = setInterval(pollStaff, 5000); }
}
function botSay(html){
  var d = document.createElement('div');
  d.className = 'msg b'; d.innerHTML = html;
  $('chatBody').appendChild(d); $('chatBody').scrollTop = 99999;
  return d;
}
function userSay(html){
  var d = document.createElement('div');
  d.className = 'msg u'; d.innerHTML = html;
  $('chatBody').appendChild(d); $('chatBody').scrollTop = 99999;
}
async function pollStaff(){
  if ($('chatPanel').hidden) return;
  try {
    var r = await getJSON('../chatdesk/api/webthread.php?userId=' + encodeURIComponent(guestId()) + '&since=' + lastSeen + '&channel=' + CH);
    if (r && r.ok) {
      if (typeof r.botEnabled === 'boolean' && r.botEnabled !== botOn) {
        botOn = r.botEnabled;
        $('chatStatus').textContent = botOn ? '● ออนไลน์' : '● เจ้าหน้าที่กำลังดูแล';
      }
      (r.messages || []).forEach(function (m) {
        if (m.id > lastSeen) lastSeen = m.id;
        if (m.sender === 'agent' || m.sender === 'staff') botSay(esc(m.text));
      });
    }
  } catch (e) {}
}
async function sendChat(){
  var inp = $('chatText'), t = inp.value.trim();
  if (!t) return;
  inp.value = '';
  if (!botOn) { userSay(esc(t)); fwd('visitor', t); toast('ฝากถึงเจ้าหน้าที่แล้ว'); return; }
  userSay(esc(t));
  fwd('visitor', t);
  var b = botSay('⏳ กำลังคิด…');
  var r;
  try {
    r = await postJSON('api/chat.php', { text: t, userId: guestId(), history: chatHist.slice(-10) });
  } catch (e) { r = null; }
  if (!r || !r.ok || !r.text) {
    b.innerHTML = '❌ ' + esc((r && r.error) || 'บอทไม่ตอบ ลองใหม่นะคะ');
    return;
  }
  chatHist.push({ role: 'user', text: t.slice(0, 500) }, { role: 'model', text: r.text.slice(0, 500) });
  if (chatHist.length > 10) chatHist.splice(0, chatHist.length - 10);
  b.innerHTML = esc(r.text).replace(/\n/g, '<br>');
  (r.images || []).slice(0, 3).forEach(function (u) {
    if (!/^https?:\/\//i.test(u)) return;
    b.insertAdjacentHTML('beforeend', '<br><img src="' + esc(u) + '" alt="รูปประกอบ" loading="lazy">');
    fwd('bot', u, { messageType: 'image', mediaUrl: u, mediaPreviewUrl: u });
  });
  if (r.sources && r.sources.length) {
    b.insertAdjacentHTML('beforeend', '<br><small class="src">ที่มา: ' + esc(r.sources.slice(0, 3).join(' • ')) + '</small>');
  }
  $('chatBody').scrollTop = 99999;
  fwd('bot', r.text);
  if (spkOn) speak(r.text);
}
async function fwd(sender, text, extra){
  try {
    var body = { userId: guestId(), channel: CH, text: String(text).slice(0, 2000), sender: sender };
    if (extra && typeof extra === 'object') {
      if (extra.messageType) body.messageType = extra.messageType;
      if (extra.mediaUrl) body.mediaUrl = extra.mediaUrl;
      if (extra.mediaPreviewUrl) body.mediaPreviewUrl = extra.mediaPreviewUrl;
    }
    await postJSON('../chatdesk/api/incoming.php', body);
  } catch (e) {}
}
botSay('สวัสดีค่ะ 🙏 ยินดีต้อนรับสู่ <b>Intelligent Technology</b> สอบถามงานพัฒนาระบบ Network Infrastructure หรืองานที่ปรึกษาได้เลยค่ะ');
/* ---------- voice (ชุดเดียวกับ ShopDee: TTS ผ่าน tripthai/api) ---------- */
var actx = null;
function unlockAudio(){
  try {
    var AC = window.AudioContext || window.webkitAudioContext;
    if (AC) { if (!actx) actx = new AC(); if (actx.state === 'suspended') actx.resume(); }
  } catch (e) {}
}
function toggleSpk(){
  spkOn = !spkOn;
  $('spkBtn').textContent = spkOn ? '🔊' : '🔇';
  if (!spkOn && audioEl) { try { audioEl.pause(); } catch (e) {} audioEl = null; }
  toast(spkOn ? '🔊 เปิดเสียงอ่านแล้ว' : '🔇 ปิดเสียงอ่าน');
  if (spkOn) { unlockAudio(); speak('เปิดเสียงอ่านแล้วค่ะ ถามได้เลย'); }
}
function stripTags(s){
  return String(s || '').replace(/<br\s*\/?>/gi, ' ').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}
async function speak(text){
  var plain = stripTags(text).slice(0, 600);
  if (!plain) return;
  unlockAudio();
  var r;
  try {
    r = await fetch('../tripthai/api/tts.php', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: plain, userId: guestId() }) });
  } catch (e) { toast('เรียก TTS ไม่สำเร็จ'); return; }
  if (!r.ok) { toast('TTS ตอบกลับผิดพลาด'); return; }
  var b = await r.blob();
  if (!b || b.size < 1000) { toast('ไฟล์เสียงสั้นผิดปกติ'); return; }
  try {
    var url = URL.createObjectURL(b);
    if (audioEl) { try { audioEl.pause(); } catch (e) {} }
    audioEl = new Audio(url);
    audioEl.onended = function(){ try { URL.revokeObjectURL(url); } catch (e) {} };
    await audioEl.play();
  } catch (e) { toast('เบราว์เซอร์บล็อกเสียง — แตะหน้าจออีกครั้ง'); }
}
var micRec = null, micChunks = [];
async function toggleMic(){
  var btn = $('micBtn');
  if (micRec && micRec.state === 'recording') { micRec.stop(); return; }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
    toast('เบราว์เซอร์นี้ใช้ไมค์ไม่ได้');
    return;
  }
  try {
    var stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
    var mime = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'].find(function(m){ try { return MediaRecorder.isTypeSupported(m); } catch (e) { return false; } });
    micChunks = [];
    micRec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    micRec.ondataavailable = function(e){ if (e.data && e.data.size) micChunks.push(e.data); };
    micRec.onstop = onMicStop;
    micRec.start();
    btn.textContent = '⏹';
    btn.classList.add('mic-live');
    $('chatStatus').textContent = '● 🎤 กำลังฟัง… แตะอีกครั้งเพื่อหยุด';
    setTimeout(function(){ if (micRec && micRec.state === 'recording') micRec.stop(); }, 30000);
  } catch (e) {
    toast('เปิดไมค์ไม่ได้ — ตรวจสิทธิ์ Microphone');
  }
}
async function onMicStop(){
  var btn = $('micBtn');
  btn.textContent = '🎤';
  btn.classList.remove('mic-live');
  $('chatStatus').textContent = '● ออนไลน์';
  try { micRec.stream.getTracks().forEach(function(t){ t.stop(); }); } catch (e) {}
  if (!micChunks.length) return;
  var blob = new Blob(micChunks, { type: micRec.mimeType || 'audio/webm' });
  micChunks = [];
  if (blob.size > 5 * 1024 * 1024) { toast('คลิปยาวไป (เกิน 5MB)'); return; }
  botSay('🎤 กำลังแปลงเสียง…');
  var fd = new FormData();
  fd.append('audio', blob, 'voice.webm');
  fd.append('userId', guestId());
  var r;
  try {
    var res = await fetch('../tripthai/api/stt.php', { method: 'POST', body: fd });
    r = await res.json();
  } catch (e) { r = null; }
  var box = $('chatBody');
  if (box.lastChild) box.removeChild(box.lastChild);
  if (!r || !r.ok || !r.text) { toast('แปลงเสียงไม่สำเร็จ ลองพิมพ์แทน'); return; }
  $('chatText').value = r.text;
  sendChat();
}
