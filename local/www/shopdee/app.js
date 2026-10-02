// ===== ShopDee storefront + chatbot (Shopee-style demo) =====
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const fmt = (n) => '฿' + Number(n || 0).toLocaleString('en-US');
const CHATDESK = new URL('../chatdesk/api/', location.href).toString();
function toast(m){ const t = $('toast'); t.textContent = m; t.hidden = false; clearTimeout(t._h); t._h = setTimeout(() => { t.hidden = true; }, 2800); }
async function getJSON(url){
  const r = await fetch(url);
  return r.json();
}
async function postJSON(url, body){
  const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  return r.json();
}
function sdGuestId(){
  let id = '';
  try { id = localStorage.getItem('shopdee_gid') || ''; } catch (e) {}
  if (!/^WEB_[A-Za-z0-9_-]{1,64}$/.test(id)) {
    id = 'WEB_' + Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
    try { localStorage.setItem('shopdee_gid', id); } catch (e) {}
  }
  return id;
}

/* ---------- catalog ---------- */
const S = { cat: '', q: '', sort: 'pop', page: 1, total: 0, cats: [] };
async function init(){
  try {
    const c = await getJSON('api/products.php?op=cats');
    if (c && c.ok) S.cats = c.cats;
  } catch (e) {}
  renderCats();
  await loadProducts(true);
  paintBadge();
  botSay('สวัสดีค่ะ 🙏 ยินดีต้อนรับสู่ <b>ShopDee</b> มีสินค้า 100+ รายการ ถามราคา โปร หรือให้ช่วยเลือกได้เลยค่ะ');
  renderChips();
}
function renderCats(){
  const all = [{ category: '', n: S.total || '' }].concat(S.cats);
  $('catBar').innerHTML = all.map((c, i) =>
    `<button class="${(c.category === S.cat) ? 'on' : ''}" onclick="pickCat(${i})">${c.category === '' ? '🏠 ทั้งหมด' : esc(c.category)}</button>`).join('');
  $('catBar')._list = all;
}
function pickCat(i){
  const c = $('catBar')._list[i];
  S.cat = c.category; S.page = 1;
  renderCats(); loadProducts(true);
}
function doSearch(){ S.q = $('q').value.trim(); S.page = 1; loadProducts(true); }
function changeSort(){ S.sort = $('sortBy').value; S.page = 1; loadProducts(true); }
function goHome(e){ if (e) e.preventDefault(); S.cat = ''; S.q = ''; S.sort = 'pop'; S.page = 1; $('q').value = ''; $('sortBy').value = 'pop'; renderCats(); loadProducts(true); }
async function loadProducts(reset){
  const u = `api/products.php?op=list&category=${encodeURIComponent(S.cat)}&q=${encodeURIComponent(S.q)}&sort=${S.sort}&page=${S.page}&per_page=24`;
  let r;
  try { r = await getJSON(u); } catch (e) { toast('โหลดสินค้าไม่สำเร็จ'); return; }
  if (!r || !r.ok) { toast((r && r.error) || 'โหลดสินค้าไม่สำเร็จ'); return; }
  S.total = r.total;
  $('resultInfo').textContent = (S.q ? `“${S.q}” ` : '') + `พบ ${r.total} รายการ` + (S.cat ? ` • ${S.cat}` : '');
  const html = r.items.map(cardHTML).join('');
  $('grid').innerHTML = reset ? html : ($('grid').innerHTML + html);
  $('moreBtn').style.display = (S.page * r.per_page < r.total) ? '' : 'none';
  renderCats();
}
function loadMore(){ S.page += 1; loadProducts(false); }
function cardHTML(h){
  const off = h.old_price > h.price ? Math.round((h.old_price - h.price) * 100 / h.old_price) : 0;
  return `<div class="card" onclick="openProduct(${h.id})">
    <img src="${esc(h.image_url)}" alt="${esc(h.name)}" loading="lazy">
    <div class="nm">${esc(h.name)}</div>
    <div class="pr"><span class="new">${fmt(h.price)}</span>${h.old_price > h.price ? `<span class="old">${fmt(h.old_price)}</span>` : ''}</div>
    <div class="meta"><span class="rate">★ ${h.rating}</span><span>ขายแล้ว ${Number(h.sold).toLocaleString()}</span></div>
    ${h.free_shipping ? '<span class="tag free">ส่งฟรี</span>' : ''}${h.cod ? '<span class="tag cod">COD</span>' : ''}${off ? `<span class="tag cod">-${off}%</span>` : ''}
  </div>`;
}
async function openProduct(id){
  let r;
  try { r = await getJSON(`api/products.php?op=get&id=${id}`); } catch (e) {}
  if (!r || !r.ok) { toast('เปิดสินค้าไม่สำเร็จ'); return; }
  const h = r.item;
  $('pDetail').innerHTML = `
    <img class="pd-img" src="${esc(h.image_url)}" alt="${esc(h.name)}">
    <h3 style="margin:10px 0 4px">${esc(h.name)}</h3>
    <div class="pd-meta"><span class="rate">★ ${h.rating}</span> (${Number(h.reviews).toLocaleString()} รีวิว) • ขายแล้ว ${Number(h.sold).toLocaleString()} • สต็อก ${h.stock}</div>
    <div><span class="pd-price">${fmt(h.price)}</span>${h.old_price > h.price ? `<span class="pd-old">${fmt(h.old_price)}</span>` : ''}</div>
    <div class="pd-shop">🏪 ${esc(h.shop_name)} • ${h.free_shipping ? '🚚 ส่งฟรี' : 'ค่าส่งตามจริง'} • ${h.cod ? '💵 เก็บปลายทางได้' : ''}</div>
    <p style="font-size:14px">${esc(h.description)}</p>
    <p style="font-size:13px;color:#555">📋 ${esc(h.specs)}</p>
    <div class="pd-row" style="align-items:center">
      <div class="qty"><button onclick="pdQty(-1)">−</button><span id="pdQ">1</span><button onclick="pdQty(1)">＋</button></div>
    </div>
    <div class="pd-row">
      <button class="btn cartb" onclick="addCart(${h.id},pdN(),false)">＋ ตะกร้า</button>
      <button class="btn buy" style="margin:0" onclick="addCart(${h.id},pdN(),true)">ซื้อเลย</button>
    </div>`;
  $('pDetail')._price = h.price;
  openModal('pModal');
}
function pdN(){ return Math.max(1, parseInt(($('pdQ') || {}).textContent) || 1); }
function pdQty(d){ const e = $('pdQ'); e.textContent = Math.min(99, Math.max(1, (parseInt(e.textContent) || 1) + d)); }
function openModal(id){ $(id).hidden = false; }
function closeModal(id){ $(id).hidden = true; }

/* ---------- cart ---------- */
function getCart(){
  try { return JSON.parse(localStorage.getItem('shopdee_cart') || '{}'); } catch (e) { return {}; }
}
function setCart(c){ try { localStorage.setItem('shopdee_cart', JSON.stringify(c)); } catch (e) {} paintBadge(); }
function paintBadge(){
  const c = getCart();
  const n = Object.values(c).reduce((a, b) => a + b, 0);
  $('cartBadge').hidden = n <= 0;
  $('cartBadge').textContent = n > 99 ? '99+' : n;
}
async function addCart(id, qty, buyNow){
  const c = getCart();
  c[id] = Math.min(99, (c[id] || 0) + qty);
  setCart(c);
  toast('ใส่ตะกร้าแล้ว');
  if (buyNow) { openCart(); }
}
async function openCart(){
  const c = getCart();
  const ids = Object.keys(c);
  if (!ids.length) {
    $('cartLines').innerHTML = '<p style="color:#888;text-align:center">ตะกร้าว่าง — ไปช้อปกันเลย 🛍️</p>';
    $('cartFoot').innerHTML = '';
    $('cartDrawer').hidden = false;
    return;
  }
  let lines = [], sub = 0;
  for (const id of ids) {
    let r;
    try { r = await getJSON(`api/products.php?op=get&id=${id}`); } catch (e) {}
    if (!r || !r.ok) continue;
    const h = r.item, q = Math.min(c[id], 99);
    lines.push({ id: h.id, name: h.name, img: h.image_url, price: h.price, qty: q });
    sub += h.price * q;
  }
  if (!lines.length) { $('cartLines').innerHTML = 'สินค้าไม่พร้อมขายแล้ว'; $('cartFoot').innerHTML = ''; }
  else {
    $('cartLines').innerHTML = lines.map(l => `
      <div class="cline"><img src="${esc(l.img)}" alt="">
        <div class="t"><b>${esc(l.name)}</b><span>${fmt(l.price)} × ${l.qty} = <b>${fmt(l.price * l.qty)}</b></span></div>
        <div class="qty"><button onclick="chQty(${l.id},-1)">−</button><span>${l.qty}</span><button onclick="chQty(${l.id},1)">＋</button></div>
        <button class="mini" onclick="rmLine(${l.id})">🗑</button>
      </div>`).join('');
    const ship = sub >= 299 ? 0 : 35;
    $('cartFoot').innerHTML = `ค่าส่ง: ${ship === 0 ? 'ฟรี 🎉' : fmt(ship)} (ฟรีเมื่อครบ ฿299)<br>
      <b>รวม: ${fmt(sub + ship)}</b><br><button class="btn buy" onclick="openCheckout()">สั่งซื้อเลย</button>`;
    $('cartFoot')._sub = sub;
    $('cartFoot')._ship = ship;
    $('cartFoot')._lines = lines;
  }
  $('cartDrawer').hidden = false;
}
function closeCart(){ $('cartDrawer').hidden = true; }
function chQty(id, d){
  const c = getCart();
  c[id] = (c[id] || 1) + d;
  if (c[id] <= 0) delete c[id];
  setCart(c); openCart();
}
function rmLine(id){ const c = getCart(); delete c[id]; setCart(c); openCart(); }
function openCheckout(){
  const lines = $('cartFoot')._lines || [];
  if (!lines.length) return;
  $('coSummary').innerHTML = lines.map(l => `${esc(l.name)} × ${l.qty} = ${fmt(l.price * l.qty)}`).join('<br>') +
    `<br>ค่าส่ง ${fmt($('cartFoot')._ship)} • <b>รวม ${fmt($('cartFoot')._sub + $('cartFoot')._ship)}</b>`;
  $('coMsg').textContent = '';
  closeCart(); openModal('coModal');
}
async function placeOrder(){
  const lines = ($('cartFoot')._lines || []).map(l => ({ id: l.id, qty: l.qty }));
  $('coMsg').textContent = 'กำลังสั่งซื้อ…';
  let r;
  try {
    r = await postJSON('api/order.php', { op: 'create', items: lines,
      name: $('coName').value, phone: $('coPhone').value, address: $('coAddr').value,
      note: $('coNote').value, payment: $('coPay').value, coupon: $('coCoupon').value,
      userId: sdGuestId() });
  } catch (e) { r = null; }
  if (!r || !r.ok) { $('coMsg').textContent = '❌ ' + ((r && r.error) || 'สั่งซื้อไม่สำเร็จ'); return; }
  setCart({});
  closeModal('coModal');
  $('coSummary').innerHTML = '';
  toast(`✅ สั่งซื้อสำเร็จ! รหัส ${r.code} ยอด ${fmt(r.total)}`);
  botSay(`🎉 สั่งซื้อสำเร็จค่ะ รหัส <b>${esc(r.code)}</b> ยอด ${fmt(r.total)}${r.shipping ? '' : ' (ส่งฟรี)'}<br>เช็คสถานะได้ที่ “📦 เช็คพัสดุของฉัน” นะคะ`);
  toggleChat(true);
}
async function openOrders(e){ if (e) e.preventDefault(); openModal('odModal'); $('odList').innerHTML = ''; }
async function findOrders(){
  const ph = $('odPhone').value.trim();
  $('odList').innerHTML = 'กำลังค้นหา…';
  let r;
  try { r = await postJSON('api/order.php', { op: 'byphone', phone: ph }); } catch (e) { r = null; }
  if (!r || !r.ok) { $('odList').innerHTML = '❌ ' + ((r && r.error) || 'ค้นหาไม่สำเร็จ'); return; }
  if (!r.orders.length) { $('odList').innerHTML = 'ไม่พบคำสั่งซื้อของเบอร์นี้'; return; }
  const st = { pending: 'รอชำระ/รอยืนยัน', await_payment: 'รอโอนเงิน', paid: 'ชำระแล้ว', shipped: 'จัดส่งแล้ว', done: 'สำเร็จ', cancelled: 'ยกเลิก' };
  $('odList').innerHTML = r.orders.map(o =>
    `<div class="cline"><div class="t"><b>${esc(o.code)}</b><span>${fmt(o.total)} • ${esc(st[o.status] || o.status)} • ${esc((o.created_at || '').slice(0, 16).replace('T', ' '))}</span></div>
    <button class="mini" onclick="viewOrder('${esc(o.code)}')">ดู</button></div>`).join('');
}
async function viewOrder(code){
  let r;
  try { r = await postJSON('api/order.php', { op: 'get', code }); } catch (e) { r = null; }
  if (!r || !r.ok) { toast('เปิดไม่สำเร็จ'); return; }
  const o = r.order;
  $('odList').innerHTML = `<b>${esc(o.code)}</b> • ${fmt(o.total)}<br>${esc(o.cust_name)} ${esc(o.cust_phone)}<br><small>${esc(o.address)}</small><br>` +
    o.items.map(i => `${esc(i.name)} × ${i.qty} = ${fmt(i.price * i.qty)}`).join('<br>');
}

/* ---------- chatbot ---------- */
let chatHist = [];
let spkOn = false, audioEl = null, botOn = true, lastSeen = 0, pollT = null;
function toggleChat(force){
  try {
    const p = $('chatPanel');
    if (!p) { toast('เปิดแชทไม่ได้ (ไม่พบแผงแชท)'); return; }
    p.hidden = (force === undefined) ? !p.hidden : !force;
    if (!p.hidden && !pollT) { pollT = setInterval(pollStaff, 5000); }
    if (!p.hidden) { toast('เปิดแชทแล้ว 👋'); try { p.scrollIntoView({ block: 'nearest' }); } catch (e) {} }
  } catch (e) { toast('เปิดแชทไม่ได้: ' + (e && e.message ? e.message : e)); }
}
function botSay(html){
  const d = document.createElement('div');
  d.className = 'msg b';
  d.innerHTML = html;
  $('chatBody').appendChild(d);
  $('chatBody').scrollTop = 99999;
  return d;
}
function userSay(html){
  const d = document.createElement('div');
  d.className = 'msg u';
  d.innerHTML = html;
  $('chatBody').appendChild(d);
  $('chatBody').scrollTop = 99999;
}
function renderChips(){
  const qs = ['ส่งฟรีไหม', 'คืนสินค้าได้ไหม', 'มีโค้ดส่วนลดไหม', 'แนะนำมือถือไม่เกิน 5000'];
  $('quickChips').innerHTML = qs.map(q => `<button onclick="quickAsk(this)">${esc(q)}</button>`).join('');
}
function quickAsk(b){ $('chatText').value = b.textContent; sendChat(); }
async function refreshBot(){
  try {
    const r = await getJSON('../chatdesk/api/webthread.php?userId=' + encodeURIComponent(sdGuestId()) + '&since=' + lastSeen + '&channel=shopweb');
    if (r && r.ok) {
      if (typeof r.botEnabled === 'boolean' && r.botEnabled !== botOn) {
        botOn = r.botEnabled;
        $('chatStatus').textContent = botOn ? '● ออนไลน์ • ตอบทันที' : '● 👩‍💼 เจ้าหน้าที่กำลังดูแล';
        if (!botOn) botSay('👩‍💼 เจ้าหน้าที่รับเรื่องไปดูแลเองแล้วค่ะ พิมพ์ฝากข้อความได้เลย');
      }
      (r.messages || []).forEach(m => {
        if (m.id > lastSeen) lastSeen = m.id;
        if (m.sender === 'agent' || m.sender === 'staff') botSay(esc(m.text));
      });
    }
  } catch (e) {}
}
function pollStaff(){ if (!$('chatPanel').hidden) refreshBot(); }
async function sendChat(){
  const inp = $('chatText'), t = inp.value.trim();
  if (!t) return;
  inp.value = '';
  if (!botOn) { userSay(esc(t)); fwd('visitor', t); toast('ฝากถึงเจ้าหน้าที่แล้ว'); return; }
  userSay(esc(t));
  fwd('visitor', t);
  const b = botSay('…');
  b.innerHTML = '⏳ กำลังคิด…';
  let r;
  try {
    r = await postJSON('api/chat.php', { text: t, userId: sdGuestId(), history: chatHist.slice(-10) });
  } catch (e) { r = null; }
  if (!r || !r.ok || !r.text) {
    b.innerHTML = '❌ ' + esc((r && r.error) || 'บอทไม่ตอบ ลองใหม่นะคะ');
    return;
  }
  chatHist.push({ role: 'user', text: t.slice(0, 500) }, { role: 'model', text: r.text.slice(0, 500) });
  if (chatHist.length > 10) chatHist.splice(0, chatHist.length - 10);
  b.innerHTML = esc(r.text).replace(/\n/g, '<br>');
  (r.images || []).slice(0, 3).forEach(u => {
    if (!/^https?:\/\//i.test(u)) return;
    b.insertAdjacentHTML('beforeend', `<br><img src="${esc(u)}" alt="รูปประกอบ" loading="lazy">`);
  });
  if (r.sources && r.sources.length) {
    b.insertAdjacentHTML('beforeend', `<br><small class="src">ที่มา: ${esc(r.sources.slice(0, 3).join(' • '))}</small>`);
  }
  $('chatBody').scrollTop = 99999;
  fwd('bot', r.text);
  (r.images || []).slice(0, 3).forEach(u => {
    if (!/^https?:\/\//i.test(u)) return;
    fwd('bot', u, { messageType: 'image', mediaUrl: u, mediaPreviewUrl: u });
  });
  if (spkOn) speak(r.text);
}
async function fwd(sender, text, extra){
  try {
    const body = { userId: sdGuestId(), channel: 'shopweb', text: String(text).slice(0, 2000), sender };
    if (extra && typeof extra === 'object') {
      if (extra.messageType) body.messageType = extra.messageType;
      if (extra.mediaUrl) body.mediaUrl = extra.mediaUrl;
      if (extra.mediaPreviewUrl) body.mediaPreviewUrl = extra.mediaPreviewUrl;
    }
    await postJSON('../chatdesk/api/incoming.php', body);
  } catch (e) {}
}
/* ---------- voice ---------- */
let actx = null;
function unlockAudio(){
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (AC) { if (!actx) actx = new AC(); if (actx.state === 'suspended') actx.resume(); }
  } catch (e) {}
}
function toggleSpk(){
  spkOn = !spkOn;
  $('spkBtn').textContent = spkOn ? '🔊' : '🔇';
  if (!spkOn && audioEl) { try { audioEl.pause(); } catch (e) {} audioEl = null; }
  toast(spkOn ? '🔊 เปิดเสียงอ่านแล้ว' : '🔇 ปิดเสียงอ่าน');
  if (spkOn) { unlockAudio(); speak('เปิดเสียงอ่านแล้วค่ะ ถามสินค้าได้เลย'); }
}
function stripTags(s){
  return String(s || '').replace(/<br\s*\/?>/gi, ' ').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}
async function speak(text){
  const plain = stripTags(text).slice(0, 600);
  if (!plain) return;
  unlockAudio();
  let r;
  try {
    r = await fetch('../tripthai/api/tts.php', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: plain, userId: sdGuestId() }) });
  } catch (e) { toast('เรียก TTS ไม่สำเร็จ'); return; }
  if (!r.ok) { toast('TTS ตอบกลับผิดพลาด'); return; }
  const b = await r.blob();
  if (!b || b.size < 1000) { toast('ไฟล์เสียงสั้นผิดปกติ'); return; }
  try {
    const url = URL.createObjectURL(b);
    if (audioEl) { try { audioEl.pause(); } catch (e) {} }
    audioEl = new Audio(url);
    audioEl.onended = () => { try { URL.revokeObjectURL(url); } catch (e) {} };
    await audioEl.play();
  } catch (e) { toast('เบราว์เซอร์บล็อกเสียง — แตะหน้าจออีกครั้ง'); }
}
let micRec = null, micChunks = [];
async function toggleMic(){
  const btn = $('micBtn');
  if (micRec && micRec.state === 'recording') { micRec.stop(); return; }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
    toast('เบราว์เซอร์นี้ใช้ไมค์ไม่ได้');
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
    const mime = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'].find(m => { try { return MediaRecorder.isTypeSupported(m); } catch (e) { return false; } });
    micChunks = [];
    micRec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    micRec.ondataavailable = (e) => { if (e.data && e.data.size) micChunks.push(e.data); };
    micRec.onstop = onMicStop;
    micRec.start();
    btn.textContent = '⏹';
    btn.classList.add('mic-live');
    $('chatStatus').textContent = '● 🎤 กำลังฟัง… แตะอีกครั้งเพื่อหยุด';
    setTimeout(() => { if (micRec && micRec.state === 'recording') micRec.stop(); }, 30000);
  } catch (e) {
    toast('เปิดไมค์ไม่ได้ — ตรวจสิทธิ์ Microphone');
  }
}
async function onMicStop(){
  const btn = $('micBtn');
  btn.textContent = '🎤';
  btn.classList.remove('mic-live');
  $('chatStatus').textContent = '● ออนไลน์ • ตอบทันที';
  try { micRec.stream.getTracks().forEach(t => t.stop()); } catch (e) {}
  if (!micChunks.length) return;
  const blob = new Blob(micChunks, { type: micRec.mimeType || 'audio/webm' });
  micChunks = [];
  if (blob.size > 5 * 1024 * 1024) { toast('คลิปยาวไป (เกิน 5MB)'); return; }
  botSay('🎤 กำลังแปลงเสียง…');
  const fd = new FormData();
  fd.append('audio', blob, 'voice.webm');
  fd.append('userId', sdGuestId());
  let r;
  try {
    const res = await fetch('../tripthai/api/stt.php', { method: 'POST', body: fd });
    r = await res.json();
  } catch (e) { r = null; }
  const box = $('chatBody');
  if (box.lastChild) box.removeChild(box.lastChild);
  if (!r || !r.ok || !r.text) { toast('แปลงเสียงไม่สำเร็จ ลองพิมพ์แทน'); return; }
  $('chatText').value = r.text;
  sendChat();
}

init();
