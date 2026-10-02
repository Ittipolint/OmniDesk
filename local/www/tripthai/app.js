// ===== TripThai booking demo (Trip.com style) + AI Bot + ChatDesk =====
// API ของ ChatDesk อยู่ origin เดียวกัน (week7/chatdesk/api/) — รับ/ส่งข้อความเบื้องหลัง
const CHATDESK_API = new URL("../chatdesk/api/", location.href).toString();

const HOTELS = [
  {id:1, name:"สยาม เคมปินสกี้ กรุงเทพฯ (Siam Kempinski)", loc:"กรุงเทพฯ • สยาม (ถ.พระราม 1)", price:7400, old:10500, rating:9.5, reviews:2822, stars:5, img:"https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f9/Siam_Kempinski_Bangkok.jpg/1280px-Siam_Kempinski_Bangkok.jpg", tag:"แลนด์มาร์กสยาม", freeCancel:true, fac:["WiFi ฟรี","สระว่ายน้ำ","สปา","ฟิตเนส","ห้องอาหาร Sra Bua","เลานจ์"], desc:"รีสอร์ทหรูกลางสยาม ติดสยามพารากอน มีสวนและสระขนาดใหญ่ 395 ห้อง สไตล์ยูโรเปียนผสมไทย"},
  {id:2, name:"ยู นิมมาน เชียงใหม่ (U Nimman)", loc:"เชียงใหม่ • นิมมาน", price:2400, old:3200, rating:9.1, reviews:3053, stars:5, img:"https://thumb.wikimedia.org/wikipedia/commons/thumb/f/fa/One_Nimman.jpg/1280px-One_Nimman.jpg", tag:"ทำเลดี", freeCancel:true, fac:["WiFi ฟรี","สระดาดฟ้า","ฟิตเนส","ที่จอดรถ","ห้องอาหาร"], desc:"147 ห้อง หรูย่านนิมมาน ติด Maya และ One Nimman ทำเลช้อป-คาเฟ่"},
  {id:3, name:"อมารี ภูเก็ต (Amari Phuket)", loc:"ภูเก็ต • ป่าตอง (ท้ายหาด)", price:6400, old:10500, rating:8.3, reviews:3721, stars:5, img:"https://thumb.wikimedia.org/wikipedia/commons/thumb/9/90/Long-tail_boats_on_Patong_Beach_Phuket.jpg/1280px-Long-tail_boats_on_Patong_Beach_Phuket.jpg", tag:"ลด 39%", freeCancel:true, fac:["หาดส่วนตัว","สระ 3 สระ","Breeze Spa","Kids Club","La Gritta/TreePod","WiFi ฟรี"], desc:"380 ห้อง มุมสงบท้ายหาดป่าตอง วิวทะเลอันดามัน ใกล้จังซีลอน"},
  {id:4, name:"เซ็นทารา แกรนด์ มิราจ พัทยา", loc:"พัทยา • นาเกลือ (หาดวงศ์อมาตย์)", price:3500, old:4900, rating:8.6, reviews:3889, stars:5, img:"https://thumb.wikimedia.org/wikipedia/commons/thumb/9/93/Centara_Grand_Mirage_Beach_Resort%2C_Pattaya_-_panoramio.jpg/1280px-Centara_Grand_Mirage_Beach_Resort%2C_Pattaya_-_panoramio.jpg", tag:"เหมาะกับครอบครัว", freeCancel:true, fac:["สวนน้ำ Lost World","หาดส่วนตัว","Kids Club","สปา","4 ห้องอาหาร","สระว่ายน้ำ"], desc:"555 ห้อง ธีมผจญภัย ทุกห้องวิวทะเล มีหาดส่วนตัว 230 เมตร"},
  {id:5, name:"เดอะ เชลล์ซี กระบี่ (The ShellSea)", loc:"กระบี่ • อ่าวน้ำเมา (ใกล้หาดอ่าวนาง)", price:2900, old:4200, rating:8.8, reviews:1063, stars:5, img:"https://thumb.wikimedia.org/wikipedia/commons/thumb/5/57/Ao_Nang_beach.jpg/1280px-Ao_Nang_beach.jpg", tag:"วิวดี", freeCancel:true, fac:["พูลวิลล่าส่วนตัว","หาด","สระผู้ใหญ่/ครอบครัว","สปา","Fin Bar","อาหารเช้า"], desc:"85 ห้อง pool villa หน้าหาด ใกล้หาดเปลือกหอยและอ่าวนาง"},
  {id:6, name:"เซ็นทารา แกรนด์ หัวหิน", loc:"หัวหิน • ใจกลางเมืองติดหาด", price:4200, old:6000, rating:8.9, reviews:2737, stars:5, img:"https://upload.wikimedia.org/wikipedia/commons/5/51/Centara_Grand_-_former_Sofitel_-_panoramio.jpg", tag:"เหมาะกับครอบครัว", freeCancel:true, fac:["สระ 4 สระ","สปา","Kids Club","4 ห้องอาหาร","ฟิตเนส","สวน"], desc:"รีสอร์ทริมชายหาดตั้งแต่ยุค 1920 สไตล์โคโลเนียล (เดิมโซฟิเทล) ใจกลางหัวหิน"},
  {id:7, name:"บันยันทรี สมุย (Banyan Tree Samui)", loc:"เกาะสมุย • ละไม (อ่าวส่วนตัว)", price:16900, old:22500, rating:9.5, reviews:914, stars:5, img:"https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d2/Lamai_Beach.jpg/1280px-Lamai_Beach.jpg", tag:"หรูหรา", freeCancel:true, fac:["พูลวิลล่าทุกหลัง","หาดส่วนตัว","สปา","The Edge/Saffron","WiFi ฟรี"], desc:"86 หลัง all-pool-villa บนอ่าวส่วนตัวลำไยเบย์ วิวอ่าวสะไฟร์"},
  {id:8, name:"เลอ พัทธา เชียงราย (Le Patta)", loc:"เชียงราย • ตัวเมือง (ถ.พหลโยธิน)", price:1500, old:1900, rating:9.3, reviews:3941, stars:4, img:"https://thumb.wikimedia.org/wikipedia/commons/thumb/d/df/Chiang_Rai_Clock_Tower_2018-05-23.jpg/1280px-Chiang_Rai_Clock_Tower_2018-05-23.jpg", tag:"ประหยัด", freeCancel:true, fac:["WiFi ฟรี","สระว่ายน้ำ","ฟิตเนส","ห้องอาหาร","ที่จอดรถ"], desc:"39 ห้อง ใจกลางเมือง ใกล้หอนาฬิกาและไนท์บาซาร์ เดินถึงได้"},
  {id:9, name:"แมนดาริน โอเรียนเต็ล กรุงเทพฯ", loc:"กรุงเทพฯ • ริมแม่น้ำเจ้าพระยา (บางรัก)", price:16000, old:20000, rating:9.6, reviews:657, stars:5, img:"https://thumb.wikimedia.org/wikipedia/commons/thumb/7/7c/Panorama_of_Chao_Phraya_River_from_Iconsiam_at_night%2C_Bangkok.jpg/1280px-Panorama_of_Chao_Phraya_River_from_Iconsiam_at_night%2C_Bangkok.jpg", tag:"ตำนานริมน้ำ", freeCancel:true, fac:["เรือรับส่ง","สระว่ายน้ำ","Oriental Spa","Le Normandie","ฟิตเนส","WiFi ฟรี"], desc:"เปิดปี 1876 เก่าแก่ที่สุดของไทย ปีก Authors' Wing 393 ห้อง ริมน้ำบางรัก"},
  {id:10, name:"เดอะ เมมโมรี่ แอท ออน ออน (ภูเก็ต)", loc:"ภูเก็ต • เมืองเก่า (ถนนพังงา)", price:1400, old:1800, rating:9.5, reviews:321, stars:3, img:"https://thumb.wikimedia.org/wikipedia/commons/thumb/3/31/Thalang_Road%2C_Old_Phuket_Town.jpg/1280px-Thalang_Road%2C_Old_Phuket_Town.jpg", tag:"ฉากหนัง The Beach", freeCancel:true, fac:["WiFi ฟรี","อาหารเช้า","เลานจ์บาร์","ลานกลาง"], desc:"เปิดปี 1929 เก่าแก่สุดของภูเก็ต ตึก Sino-Portuguese 34 ห้อง เดิน 2 นาทีถึงถนนถลาง"},
  {id:11, name:"ฮิลตัน พัทยา (Hilton Pattaya)", loc:"พัทยา • กลางเมือง (บน Central Festival)", price:5500, old:7500, rating:9.2, reviews:3885, stars:5, img:"https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8c/Hilton_Pattaya_Hotel.jpg/1280px-Hilton_Pattaya_Hotel.jpg", tag:"วิวอ่าวพัทยา", freeCancel:true, fac:["อินฟินิตี้พูล","สปา","Edge/Drift/Horizon rooftop","ฟิตเนส","WiFi","ทางลงหาด"], desc:"34 ชั้น 304 ห้อง วิวอ่าว 180 องศา ใกล้ Walking Street 1.3 กม."},
  {id:12, name:"โฟร์ซีซั่นส์ เชียงใหม่", loc:"เชียงใหม่ • แม่ริม (ทุ่งนา)", price:21500, old:27000, rating:9.5, reviews:307, stars:5, img:"https://upload.wikimedia.org/wikipedia/commons/8/87/Rice_fields_Chiang_Mai.jpg", tag:"กลางทุ่งนา", freeCancel:true, fac:["พูลวิลล่าส่วนตัว","สปา","โยคะ","โรงเรียนสอนทำอาหาร","สระ 3 สระ","เทนนิส"], desc:"Pavilions กลางทุ่งนาแม่ริม สถาปัตยกรรมล้านนา 98 หลัง เงียบสงบ"},
];

let state = { dest:"", coupon:0, currentHotel:null, nights:2 };
const $ = id => document.getElementById(id);
const fmt = n => "฿" + n.toLocaleString("th-TH");

// สถานะลำโพง: ปิดเสมอเมื่อโหลดหน้า (default OFF) + จะพูดอัตโนมัติก็ต่อเมื่อผู้ใช้เปิดหน้าต่างแชทแล้ว
let spkOn = false;
let chatSeen = false;
let saySeq = 0; const sayMap = {};

/* ---- state ทั้งหมดของวิดเจ็ตรวมไว้ตรงนี้ (ห้ามประกาศ let/const กลางไฟล์แล้วให้ init ใช้) ---- */
// TTS
let speakQueue = [], speaking = false, speakErrs = 0, speakTotal = 0, speakTimer = null;
// ไมค์
let micRec = null, micChunks = [], micStart = 0, micTimer = null, micStream = null;
// Bridge ChatDesk
let cdConvId = 0, cdLastSeen = 0, cdPollTimer = null, cdAwaitName = false;
let cdBotEnabled = true; // true = AI ตอบได้; false = โหมดคนดูแล (เจ้าหน้าที่ปิดบอท) -> AI ห้ามตอบ
// นับคลิปเงียบ/พังติดกันในโหมดต่อเนื่อง (ครบ 3 ครั้ง = หยุดลูป ไม่สแปม)
let idleSilent = 0;
const IDLE_MAX = 3;
const cdSeenIds = new Set();
try{
  cdConvId = parseInt(localStorage.getItem("tt_conv_id") || "0");
  cdLastSeen = parseInt(localStorage.getItem("tt_last_seen") || "0");
}catch(e){}
// ดัก error
let errShownAt = 0;
// เปิดแชทแล้วหรือยัง (toggleChat)
let chatOpened = false;
// จูนเสียง TTS
const SPK_RATE = 0.9, SPK_PITCH = 1, SPK_GAP_MS = 600, SPK_CHUNK = 180, SPK_START_DELAY = 150;
const VOICE_GAP_MS = 600; // หยุดระหว่างประโยคของเสียง Piper (ฟังทัน ไม่รัว)
// STT
const STT_URL = new URL("api/stt.php", location.href).toString();
const MIC_MAX_SEC = 45;

/* อุ่นรายชื่อเสียงตั้งแต่โหลดหน้า (บาง browser โหลดเสียงช้า รอบแรกจะได้ไม่เงียบ) */
try{
  if("speechSynthesis" in window){
    speechSynthesis.getVoices();
    speechSynthesis.onvoiceschanged = () => { try{ speechSynthesis.getVoices(); }catch(e){} };
  }
}catch(e){}

// ---- init dates (หุ้ม try/catch: กัน error ตอนบูตฆ่าไฟล์ทั้งไฟล์) ----
(function init(){
  try{
    const t = new Date(), f = d => d.toISOString().slice(0,10);
    const ci = new Date(t); ci.setDate(ci.getDate()+7);
    const co = new Date(t); co.setDate(co.getDate()+9);
    $("qCheckin").value = f(ci); $("qCheckout").value = f(co);
    renderHotels();
    updateCount();
    greet();
  }catch(err){ setTimeout(() => { throw err; }, 0); } // โยนต่อให้ error reporter จับ แต่ให้ไฟล์รันต่อจนจบ
})();

function nights(){
  const a = new Date($("qCheckin").value), b = new Date($("qCheckout").value);
  const n = Math.round((b-a)/86400000);
  return (isNaN(n)||n<1)?1:n;
}

function goHome(e){ e.preventDefault(); state.dest=""; $("qDest").value=""; renderHotels(); window.scrollTo({top:0,behavior:"smooth"}); }
function soon(e){ e.preventDefault(); toast("🚧 เมนูนี้เป็นเดโม — ใช้ได้เฉพาะจองโรงแรมในเวอร์ชันนี้"); }
function quickSearch(d){ $("qDest").value=d; doSearch(); }
function doSearch(){
  state.dest = $("qDest").value.trim();
  state.nights = nights();
  renderHotels();
  $("searchMeta").textContent = state.dest
    ? `“${state.dest}” • ${$("qCheckin").value} → ${$("qCheckout").value} (${state.nights} คืน) • ${$("qGuests").value}`
    : `${$("qCheckin").value} → ${$("qCheckout").value} (${state.nights} คืน)`;
  document.getElementById("hotels").scrollIntoView({behavior:"smooth"});
  toast(state.dest ? `🔍 พบที่พักใน “${state.dest}”` : "🔍 แสดงที่พักทั้งหมด");
}
function resetFilters(){
  document.querySelectorAll(".filters input[type=checkbox]").forEach(c=>c.checked=true);
  $("sortBy").value="pop"; state.dest=""; $("qDest").value=""; renderHotels();
}
document.querySelectorAll(".filters input").forEach(c=>c.addEventListener("change",renderHotels));

function passFilters(h){
  const prices=[...document.querySelectorAll(".f-price:checked")].map(x=>x.value);
  const okP = prices.some(r=>{const[a,b]=r.split("-").map(Number);return h.price>=a&&h.price<=b;});
  if(!okP) return false;
  const rates=[...document.querySelectorAll(".f-rate:checked")].map(x=>parseFloat(x.value));
  // star filter reuse: value 3 with data-star means allow <=3? simplify: if star 3 unchecked hide 3-star
  const starBoxes=[...document.querySelectorAll(".f-star:checked")].map(x=>x.value);
  if(h.stars>=4 && !starBoxes.includes(String(h.stars))) return false;
  if(h.stars<=3){
    const allow3 = document.querySelector('.f-rate[data-star="3"]');
    if(allow3 && !allow3.checked) return false;
  }
  if(!rates.includes(0) && !rates.some(r=>r>0 && h.rating>=r)) return false;
  if(state.dest){
    const d = state.dest.replace("ฯ","");
    const hl = (h.loc+h.name).replace("ฯ","");
    if(!hl.includes(state.dest) && !hl.includes(d) && !state.dest.includes(h.loc.split("•")[0].trim().replace("ฯ",""))) return false;
  }
  return true;
}

function renderHotels(){
  const sort = $("sortBy").value;
  let list = HOTELS.filter(passFilters);
  if(sort==="low") list=[...list].sort((a,b)=>a.price-b.price);
  if(sort==="high") list=[...list].sort((a,b)=>b.price-a.price);
  if(sort==="rate") list=[...list].sort((a,b)=>b.rating-a.rating);
  $("listCount").textContent = `(${list.length} แห่ง)`;
  $("listTitle").firstChild.textContent = state.dest ? `🏨 ที่พักใน ${state.dest} ` : "🏨 ที่พักแนะนำ ";
  const g = $("hotelGrid");
  if(!list.length){ g.innerHTML = `<div style="grid-column:1/-1;background:#fff;border-radius:12px;padding:30px;text-align:center">😢 ไม่พบที่พักตามเงื่อนไข<br><button class="btn-chat-open" style="max-width:220px;margin:12px auto 0" onclick="resetFilters()">ล้างตัวกรอง</button></div>`; return; }
  g.innerHTML = list.map(h=>`
    <div class="hotel-card" onclick="openHotel(${h.id})">
      <div style="position:relative"><img src="${h.img}" alt="${h.name}" loading="lazy">
      ${h.tag?`<span class="tag hot" style="position:absolute;top:10px;left:10px">${h.tag}</span>`:""}</div>
      <div class="hc-body">
        <h3>${h.name} ${"⭐".repeat(Math.min(h.stars,3))}${h.stars>3?"⭐".repeat(h.stars-3):""}</h3>
        <div class="hc-loc">📍 ${h.loc}</div>
        <div class="hc-rate"><span class="score">${h.rating}</span><span>${h.rating>=9?"ยอดเยี่ยม":h.rating>=8?"ดีมาก":"ดี"} • ${h.reviews.toLocaleString()} รีวิว</span></div>
        <div>${h.freeCancel?'<span class="tag free">ยกเลิกฟรี</span>':'<span class="tag">ยกเลิกมีค่าธรรมเนียม</span>'} <span class="tag">ยืนยันทันที</span></div>
        <div class="hc-price"><span class="old">${fmt(h.old)}</span><span><span class="new">${fmt(h.price)}</span><small>/คืน</small></span></div>
      </div>
    </div>`).join("");
}

// ---- hotel detail + booking ----
function openHotel(id){
  const h = HOTELS.find(x=>x.id===id); if(!h) return;
  state.currentHotel = h; state.coupon = 0; $("bCoupon").value=""; $("couponMsg").textContent="";
  const n = nights();
  $("hotelDetail").innerHTML = `
    <img class="detail-img" src="${h.img}" alt="${h.name}">
    <h2 style="margin:12px 0 4px">${h.name}</h2>
    <div class="hc-loc">📍 ${h.loc} • ⭐ ${h.stars} ดาว • <span class="score">${h.rating}</span> ${h.reviews.toLocaleString()} รีวิว</div>
    <p>${h.desc}</p>
    <div class="fac">${h.fac.map(f=>`<span>✓ ${f}</span>`).join("")}</div>
    <div class="book-summary">📅 ${$("qCheckin").value} → ${$("qCheckout").value} (${n} คืน) • ${$("qGuests").value}<br>
    💰 <span class="old">${fmt(h.old*n)}</span> <b style="color:#ff6a00;font-size:20px">${fmt(h.price*n)}</b> รวม ${n} คืน (ยังไม่รวมส่วนลด)</div>
    <button class="btn-book" onclick="openBooking()">🛎️ จองห้องนี้เลย</button>
    <button class="btn-chat-open" onclick="openChat();askHotel(${h.id})">💬 สอบถาม AI เกี่ยวกับที่พักนี้</button>`;
  openModal("hotelModal");
}
function openBooking(){
  const h = state.currentHotel; if(!h) return;
  closeModal("hotelModal");
  const n = nights(); state.nights = n;
  const rooms = parseInt($("bRooms").value||"1");
  const total = h.price*n*rooms;
  const final = Math.max(0,total-state.coupon);
  $("bookSummary").innerHTML = `<b>${h.name}</b><br>📍 ${h.loc}<br>📅 ${$("qCheckin").value} → ${$("qCheckout").value} (${n} คืน) x ${rooms} ห้อง`;
  $("bookTotal").textContent = fmt(final);
  $("bookBreak").textContent = state.coupon?`(ลดคูปอง ฿${state.coupon})`:`(฿${h.price.toLocaleString()} × ${n} คืน × ${rooms} ห้อง)`;
  $("bRooms").onchange = openBookingRefresh;
  openModal("bookModal");
}
function openBookingRefresh(){ openBooking(); }
function applyCoupon(){
  const c = $("bCoupon").value.trim().toUpperCase();
  if(c==="TRIPTHAI100"){ state.coupon=100; $("couponMsg").textContent="✅ ใช้โค้ดสำเร็จ ลด 100 บาท"; $("couponMsg").style.color="green"; }
  else if(c===""){ state.coupon=0; $("couponMsg").textContent=""; }
  else { state.coupon=0; $("couponMsg").textContent="❌ โค้ดไม่ถูกต้อง (ลอง TRIPTHAI100)"; $("couponMsg").style.color="red"; }
  openBooking();
}
function confirmBooking(){
  const name=$("bName").value.trim(), phone=$("bPhone").value.trim(), email=$("bEmail").value.trim();
  if(!state.currentHotel) return;
  if(!name||!phone||!email){ toast("⚠️ กรุณากรอกชื่อ เบอร์โทร และอีเมลให้ครบ"); return; }
  if(!/^[0-9+\-\s]{8,15}$/.test(phone)){ toast("⚠️ เบอร์โทรไม่ถูกต้อง"); return; }
  if(!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)){ toast("⚠️ อีเมลไม่ถูกต้อง"); return; }
  const h=state.currentHotel, n=state.nights||nights(), rooms=parseInt($("bRooms").value||"1");
  const total=Math.max(0,h.price*n*rooms-state.coupon);
  const code="TT"+Date.now().toString().slice(-8);
  const bookings=JSON.parse(localStorage.getItem("tt_bookings")||"[]");
  bookings.unshift({code,hotel:h.name,loc:h.loc,img:h.img,name,phone,email,rooms,nights:n,total,note:$("bNote").value,ci:$("qCheckin").value,co:$("qCheckout").value,at:new Date().toLocaleString("th-TH")});
  localStorage.setItem("tt_bookings",JSON.stringify(bookings));
  updateCount(); closeModal("bookModal");
  toast(`✅ จองสำเร็จ! รหัส ${code} ยอด ${fmt(total)}`);
  aiSay(`🎉 ยินดีด้วย ${name}! จอง <b>${h.name}</b> สำเร็จ<br>รหัส: <b>${code}</b> • ยอด ${fmt(total)}<br>ดูได้ที่ “การจองของฉัน” นะคะ`);
  openChat();
}
function openBookings(){
  const b=JSON.parse(localStorage.getItem("tt_bookings")||"[]");
  $("myList").innerHTML = b.length? b.map((x,i)=>`
    <div class="my-card"><b class="code">${x.code}</b> • ${x.at}<br><b>${x.hotel}</b><br>
    📅 ${x.ci} → ${x.co} (${x.nights} คืน) x ${x.rooms} ห้อง • 👤 ${x.name}<br>
    💰 <b>${fmt(x.total)}</b> ${x.note?`<br>📝 ${x.note}`:""}
    <br><button class="cancel" onclick="cancelBooking(${i})">ยกเลิกการจอง</button></div>`).join("")
    : `<p style="text-align:center;color:#667">ยังไม่มีการจอง<br><button class="btn-chat-open" style="max-width:200px;margin:10px auto" onclick="closeModal('myModal')">เลือกที่พักเลย</button></p>`;
  openModal("myModal");
}
function cancelBooking(i){
  const b=JSON.parse(localStorage.getItem("tt_bookings")||"[]");
  const [rm]=b.splice(i,1);
  localStorage.setItem("tt_bookings",JSON.stringify(b));
  updateCount(); openBookings(); toast(`🗑️ ยกเลิก ${rm.code} แล้ว (คืนเงิน 3-5 วัน)`);
}
function updateCount(){
  const b=JSON.parse(localStorage.getItem("tt_bookings")||"[]");
  $("bookingCount").textContent=b.length;
}
function openModal(id){ $(id).classList.remove("hidden"); }
function closeModal(id){ $(id).classList.add("hidden"); }
function toast(msg){
  const t=$("toast"); t.textContent=msg; t.classList.remove("hidden");
  clearTimeout(t._h); t._h=setTimeout(()=>t.classList.add("hidden"),2600);
}

// ================= AI CHAT + ChatDesk =================
function toggleChat(forceClose){
  const w=$("chatWin");
  if(forceClose===true){
    w.classList.add("hidden");
    voiceCont = false; voiceStop(); paintMic(); // ปิดแชท = หยุดโหมดต่อเนื่องด้วย
    return;
  }
  w.classList.toggle("hidden");
  if(!w.classList.contains("hidden")){
    $("fabBadge").style.display="none"; chatOpened=true; chatSeen=true;
    cdStartPoll(); // เริ่มดึงคำตอบเจ้าหน้าที่จาก ChatDesk
    setTimeout(()=>$("chatText").focus(),100);
  }
}
function openChat(){
  $("chatWin").classList.remove("hidden");
  $("fabBadge").style.display="none";
  chatSeen = true; // ผู้ใช้เปิดแชทแล้ว อนุญาตให้บอทพูดอัตโนมัติได้ (ถ้าเปิดลำโพงไว้)
  cdStartPoll(); // เริ่มดึงคำตอบเจ้าหน้าที่จาก ChatDesk
}

function greet(){
  $("spkBtn").textContent = spkOn ? "🔊" : "🔇";
  botSay(`สวัสดีค่ะ 🙏 <b>TripThai AI</b> ยินดีให้บริการ<br>ถามได้เลย เช่น <i>“หาที่พักภูเก็ตไม่เกิน 2000”</i> หรือแตะปุ่มไมค์ครั้งเดียว<b>คุยต่อเนื่อง</b>ได้เลยค่ะ (แตะอีกครั้งเพื่อหยุด)<br>📡 ทุกข้อความ (พิมพ์/เสียง) จะ<b>ส่งถึงเจ้าหน้าที่ใน ChatDesk</b>ด้วย — ถ้าเจ้าหน้าที่ตอบกลับจะเด้งขึ้นที่นี่ทันทีค่ะ`);
}
function escapeHtml(s){ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\n/g,"<br>"); }

/* ============ Bridge: วิดเจ็ต ↔ ChatDesk (สองทาง) ============ */
function cdGuestId(){
  let id = localStorage.getItem("tt_web_id");
  if(!id){ id = "WEB_" + Date.now().toString(36) + Math.random().toString(36).slice(2,8); localStorage.setItem("tt_web_id", id); }
  return id;
}
function cdGuestName(){ return localStorage.getItem("tt_guest_name") || ""; }

/* โหมดบอทตาม ChatDesk: true = AI ตอบได้ / false = คนดูแลอยู่ AI ห้ามตอบ (รอคนพิมพ์เท่านั้น) */
function setBotMode(on){
  on = !!on;
  if(on === cdBotEnabled) return;
  cdBotEnabled = on;
  if(on){
    $("chatStatus").textContent = "● ออนไลน์ • ตอบทันที";
    toast("🤖 AI กลับมาตอบแล้ว");
  }else{
    botSay("👩‍💼 เจ้าหน้าที่รับเรื่องไปดูแลเองแล้ว — <b>AI หยุดตอบชั่วคราว</b><br>พิมพ์ฝากข้อความได้เลย เจ้าหน้าที่จะมาตอบในแชทนี้โดยตรงค่ะ");
    $("chatStatus").textContent = "● 👩‍💼 เจ้าหน้าที่กำลังดูแล — AI หยุดตอบ";
  }
}
/* เช็คสดจาก ChatDesk ก่อน AI จะตอบทุกครั้ง (กันตอบสวนเจ้าหน้าที่) */
async function refreshBotMode(){
  try{
    const r = await fetch(CHATDESK_API + "webthread.php?userId=" + encodeURIComponent(cdGuestId()) + "&since=" + cdLastSeen);
    const j = await r.json();
    if(j && j.ok && typeof j.botEnabled === "boolean") setBotMode(j.botEnabled);
  }catch(e){}
  return cdBotEnabled;
}
/* ประตู AI: ให้ตอบเฉพาะเมื่อ ChatDesk อนุญาต (bot on) — ข้อความผู้ใช้ยังส่งถึงเจ้าหน้าที่เสมอ */
async function aiGate(okFn){
  if(await refreshBotMode()){ okFn(); }
}

/* ขาไป: ส่งข้อความของแขกเข้า ChatDesk (ขึ้นกล่องข้อความเจ้าหน้าที่ทันที) */
async function cdForward(text, msgId){
  try{
    const name = cdGuestName();
    const r = await fetch(CHATDESK_API + "incoming.php", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        userId: cdGuestId(), channel: "web", text: text,
        displayName: name ? ("🌐 " + name + " (TripThai)") : "🌐 แขกเว็บ (TripThai)",
        messageId: msgId || ("WEB_" + Date.now() + "_" + Math.floor(Math.random() * 1e6))
      })
    });
    const j = await r.json();
    if(j && j.ok){
      if(j.conversationId){ cdConvId = j.conversationId; localStorage.setItem("tt_conv_id", String(cdConvId)); }
      if(j.messageId){ cdLastSeen = Math.max(cdLastSeen, j.messageId); localStorage.setItem("tt_last_seen", String(cdLastSeen)); }
      $("chatStatus").textContent = "● เชื่อม ChatDesk แล้ว ✓ ส่งถึงเจ้าหน้าที่แล้ว";
    }else{
      $("chatStatus").textContent = "● ส่งถึง ChatDesk ไม่สำเร็จ (" + ((j && j.error) || ("HTTP " + r.status)) + ")";
      botSay(`⚠️ ส่งข้อความถึงเจ้าหน้าที่ไม่สำเร็จ (${escapeHtml((j && j.error) || ("HTTP " + r.status))})<br>ลองใหม่อีกครั้งนะคะ`);
    }
  }catch(e){ /* เน็ตขัดข้อง */
    $("chatStatus").textContent = "● เชื่อม ChatDesk ไม่ได้ — ตรวจเน็ตแล้วลองใหม่";
    botSay(`⚠️ เชื่อม ChatDesk ไม่ได้ (เน็ตขัดข้อง) — ข้อความนี้ยังไม่ถึงเจ้าหน้าที่ ลองส่งใหม่อีกครั้งค่ะ`);
  }
}

/* ขาไป (บอท): ส่งคำตอบของ AI Bot เข้า ChatDesk ด้วย เจ้าหน้าที่จะได้เห็นบริบทครบ */
async function cdForwardBot(html){
  try{
    const text = String(html).replace(/<br\s*\/?>/gi, "\n").replace(/<[^>]+>/g, "")
      .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&")
      .replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim().slice(0, 2000);
    if(!text) return;
    const name = cdGuestName();
    const r = await fetch(CHATDESK_API + "incoming.php", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        userId: cdGuestId(), channel: "web", sender: "bot", text: text,
        displayName: name ? ("🌐 " + name + " (TripThai)") : "🌐 แขกเว็บ (TripThai)",
        messageId: "WEBBOT_" + Date.now() + "_" + Math.floor(Math.random() * 1e6)
      })
    });
    // กัน echo: จำ id ล่าสุดไว้ poll รอบหน้าจะได้ไม่ดึงข้อความบอทของตัวเองกลับมาแสดงซ้ำ
    try{
      const j = await r.json();
      if(j && j.ok && j.messageId){ cdLastSeen = Math.max(cdLastSeen, j.messageId); localStorage.setItem("tt_last_seen", String(cdLastSeen)); }
    }catch(e){}
  }catch(e){}
}
/* aiSay = ตอบในวิดเจ็ต + ส่งสำเนาเข้า ChatDesk (ใช้เฉพาะคำตอบ AI: aiReply/askHotel/ยืนยันจอง) */
function aiSay(html){ botSay(html); cdForwardBot(html); }

/* ขากลับ: ดึงคำตอบของเจ้าหน้าที่จาก ChatDesk ทุก 4 วินาที */
async function cdPoll(){
  if($("chatWin").classList.contains("hidden")) return;
  try{
    const r = await fetch(CHATDESK_API + "webthread.php?userId=" + encodeURIComponent(cdGuestId()) + "&since=" + cdLastSeen);
    const j = await r.json();
    if(j && typeof j.botEnabled === "boolean") setBotMode(j.botEnabled);
    if(!j || !j.ok || !j.messages || !j.messages.length){
      return;
    }
    let agentNew = 0;
    j.messages.forEach(m => {
      if(cdSeenIds.has(m.id)) return;
      cdSeenIds.add(m.id);
      if(m.id > cdLastSeen){ cdLastSeen = m.id; localStorage.setItem("tt_last_seen", String(cdLastSeen)); }
      if(m.sender === "agent"){ botSay(`👩‍💼 <b>เจ้าหน้าที่ (ChatDesk):</b><br>${escapeHtml(m.text)}`); agentNew++; }
      // ข้าม sender bot: เป็น echo คำตอบ AI ของวิดเจ็ตเองที่ส่งเข้า ChatDesk ไปแล้ว (แสดงไปแล้วตอน aiSay)
      // ข้าม sender customer/system: เป็นข้อความของเราเอง / ข้อความระบบ
    });
    if(agentNew > 0){
      toast("👩‍💼 เจ้าหน้าที่ตอบกลับแล้ว");
      const b = $("fabBadge"); b.textContent = agentNew; b.style.display = "flex";
    }
  }catch(e){}
}
function cdStartPoll(){ if(!cdPollTimer){ cdPoll(); cdPollTimer = setInterval(cdPoll, 4000); } }

/* แขกแจ้งชื่อ — จะได้แสดงชื่อจริงในกล่อง ChatDesk */
function askName(){
  openChat(); cdAwaitName = true;
  botSay("ได้เลยค่ะ 😊 <b>พิมพ์ชื่อของคุณ</b>ในช่องด้านล่างได้เลย");
  setTimeout(() => $("chatText").focus(), 100);
}
function setGuestName(name){
  name = name.trim().slice(0, 50);
  localStorage.setItem("tt_guest_name", name);
  cdForward("👤 แขกแจ้งชื่อ: " + name);
  botSay(`รับทราบค่ะ คุณ<b>${escapeHtml(name)}</b> ✅ ข้อความต่อจากนี้จะส่งถึงเจ้าหน้าที่ในนามคุณ`);
}
function scrollChat(){ const b=$("chatBody"); b.scrollTop=b.scrollHeight; }
function userSay(t){ $("chatBody").insertAdjacentHTML("beforeend",`<div class="msg user">${t}</div>`); scrollChat(); }

/* botSay ทุกข้อความเป็น log ถาวร + มีปุ่ม 🔊 ฟังเสียงรายข้อ */
function botSay(html, quiet){
  const id = ++saySeq;
  const plain = html.replace(/<[^>]+>/g, " ").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&").replace(/\s+/g, " ").trim().slice(0, 500);
  sayMap[id] = plain;
  if(saySeq > 60){ delete sayMap[saySeq - 60]; }
  $("chatBody").insertAdjacentHTML("beforeend", `<div class="msg bot" id="say-${id}">${html}<br><button class="play-btn" onclick="speakById(${id})">🔊 ฟังเสียง</button></div>`);
  scrollChat();
  if(spkOn && chatSeen && plain && !quiet) speak(plain);
  return id;
}
function speakById(id){
  if(!sayMap[id]) return;
  if(!("speechSynthesis" in window)){ toast("⚠️ เบราว์เซอร์นี้อ่านออกเสียงไม่ได้"); return; }
  speak(sayMap[id]);
}
/* ---------- TTS จูนแล้ว: เสียงช้าลง + เลือกเสียงไทยดีสุด + อ่านทีละประโยค ---------- */

/* ลำดับเสียงไทยที่เพราะสุด → ดีน้อยสุด (Google / Microsoft Natural อยู่บน) */
function pickThaiVoice(){
  try{
    const vs = (speechSynthesis.getVoices && speechSynthesis.getVoices()) || [];
    const th = vs.filter(v => v.lang && v.lang.toLowerCase().indexOf("th") === 0);
    if(!th.length) return null;
    const score = n => {
      n = (n || "").toLowerCase();
      if(n.indexOf("google") >= 0 && n.indexOf("thailand") >= 0) return 0; // Chrome: Google ไทย
      if(n.indexOf("natural") >= 0) return 1;                              // Edge: Premwadee/Narisa Natural
      if(n.indexOf("premwadee") >= 0 || n.indexOf("narisa") >= 0) return 2;
      if(n.indexOf("online") >= 0) return 3;
      return 4;
    };
    return th.slice().sort((a, b) => score(a.name) - score(b.name))[0];
  }catch(e){ return null; }
}
/* ทำความสะอาดข้อความก่อนอ่าน: ตัดอีโมจิ/สัญลักษณ์กวนเสียงอ่าน, ขยายคำที่อ่านเพี้ยน */
function cleanForSpeech(t){
  return String(t)
    .replace(/https?:\/\/[^\s]+/g, " ลิงก์ ")
    .replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{2190}-\u{21FF}\u{FE0F}]/gu, "")
    .replace(/฿/g, "บาท ").replace(/→/g, " ถึง ").replace(/[•·]/g, ", ")
    .replace(/[*#_`>|⧉]/g, "").replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ").trim();
}
/* ตัดเป็นท่อนสั้น ๆ ทีละประโยค (กันอ่านรัว + กันบั๊ก Chrome ตัดเสียงข้อความยาว) */
function chunkThai(t){
  const parts = String(t).split(/([\n.!?…]+)/);
  const out = [];
  let cur = "";
  parts.forEach(p => {
    if(!p) return;
    if(/^[\n.!?…]+$/.test(p)){ cur += " "; if(cur.trim()){ out.push(cur.trim()); cur = ""; } }
    else if((cur + " " + p).trim().length > SPK_CHUNK){ if(cur.trim()) out.push(cur.trim()); cur = p; }
    else cur += " " + p;
  });
  if(cur.trim()) out.push(cur.trim());
  return out.length ? out : [t];
}
function speak(text){
  const clean = cleanForSpeech(text);
  if(!clean || !("speechSynthesis" in window)) return;
  stopSpeak();
  speakQueue = chunkThai(clean);
  speakErrs = 0; speakTotal = speakQueue.length;
  // หน่วงนิดนึงหลัง cancel() — กันบั๊ก Chrome: cancel+speak ใน tick เดียวกันแล้วเสียงหายเงียบ
  speakTimer = setTimeout(playNextChunk, SPK_START_DELAY);
}
function playNextChunk(){
  if(!speakQueue.length){
    speaking = false;
    if(speakTotal > 0 && speakErrs >= speakTotal){
      toast("⚠️ อ่านออกเสียงไม่ได้ในเบราว์เซอร์นี้ — ลองใช้ Chrome/Edge รุ่นใหม่");
    }
    speakTotal = 0;
    if($("chatStatus").textContent.indexOf("🔊 กำลังพูด") === 0) $("chatStatus").textContent = "● ออนไลน์ • ตอบทันที";
    return;
  }
  speaking = true;
  $("chatStatus").textContent = "● 🔊 กำลังพูด… (กด 🔊 บนหัวแชทเพื่อหยุด)";
  try{
    const u = new SpeechSynthesisUtterance(speakQueue.shift());
    u.lang = "th-TH"; u.rate = SPK_RATE; u.pitch = SPK_PITCH;
    const v = pickThaiVoice();
    if(v) u.voice = v;
    else { // ยังไม่มีเสียงไทยโหลดมา — กระตุ้นแล้วลองใหม่อีกครั้ง
      try{ speechSynthesis.getVoices(); }catch(e){}
    }
    u.onend = () => setTimeout(playNextChunk, SPK_GAP_MS);
    u.onerror = () => { speakErrs++; setTimeout(playNextChunk, SPK_GAP_MS); };
    speechSynthesis.speak(u);
  }catch(e){ speakErrs++; setTimeout(playNextChunk, SPK_GAP_MS); }
}
function stopSpeak(){
  if(speakTimer){ clearTimeout(speakTimer); speakTimer = null; }
  speakQueue = []; speaking = false;
  try{ speechSynthesis.cancel(); }catch(e){}
}
function toggleSpeak(){
  spkOn = !spkOn;
  $("spkBtn").textContent = spkOn ? "🔊" : "🔇";
  if(!spkOn){ stopSpeak(); }
  else if("speechSynthesis" in window){ speak("เปิดเสียงบอทแล้วค่ะ ถ้าได้ยินประโยคนี้แสดงว่าปกติ"); } // เทสเสียงทันทีที่เปิด
  toast(spkOn ? "🔊 เปิดเสียงบอทแล้ว (จะพูดทุกข้อความ)" : "🔇 ปิดเสียงบอทแล้ว (กด 🔊 ใต้ข้อความเพื่อฟังเป็นข้อ ๆ)");
}

/* ดัก JS error ทั้งหน้าแล้วรายงานในแชท (จะได้รู้ว่าพังตรงไหนโดยไม่ต้องเปิด DevTools) */
window.addEventListener("error", e => {
  try{
    const now = Date.now();
    if(now - errShownAt < 3000) return;
    errShownAt = now;
    const msg = "⚠️ ระบบขัดข้อง: " + ((e && e.message) || "ไม่ทราบสาเหตุ");
    if(!$("chatWin").classList.contains("hidden")) botSay(msg + "<br>ลองรีเฟรชหน้า (Ctrl+F5) แล้วทดสอบใหม่ค่ะ");
    else toast(msg);
  }catch(_){}
});

/* ทดสอบระบบเสียงทั้งชุด + รายงานผลในแชท */
function voiceTest(){
  openChat();
  const micOk = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const ttsOk = ("speechSynthesis" in window);
  let voices = "";
  try{
    const vs = ttsOk ? speechSynthesis.getVoices() : [];
    const th = vs.filter(v => v.lang && v.lang.toLowerCase().indexOf("th") === 0);
    voices = ` (เสียงทั้งหมด ${vs.length}, เสียงไทย ${th.length}${th.length ? ": " + th.slice(0, 3).map(v => v.name).join(" / ") : ""})`;
  }catch(e){}
  botSay(`🔧 <b>ผลตรวจระบบเสียง:</b><br>🎤 ไมค์อัดเสียง: ${micOk ? "✅ ใช้ได้" : "❌ ใช้ไม่ได้"}<br>🎤 ไมค์สำรอง (Web Speech): ${SR ? "✅ ใช้ได้" : "❌ ใช้ไม่ได้"}<br>🔊 ลำโพง: ${ttsOk ? "✅ ใช้ได้" + escapeHtml(voices) : "❌ ใช้ไม่ได้"}<br>🌐 Browser: ${escapeHtml((navigator.userAgent || "").slice(0, 80))}`);
  if(ttsOk) speak("ทดสอบเสียงค่ะ หนึ่ง สอง สาม ถ้าได้ยินชัดเจนแสดงว่าระบบเสียงปกติ");
}

/* ============ เสียง: ไมค์ → Whisper (fallback: ไมค์เบราว์เซอร์) ============ */

async function toggleMic(){
  // ปุ่มเดียวคุมทั้งหมด: แตะตอนว่าง = เปิดคุยต่อเนื่องแล้วเริ่มฟัง / แตะตอนกำลังคุย = หยุดทั้งหมด
  if((micRec && micRec.state === "recording") || voiceCont){
    if(micRec && micRec.state === "recording"){ stopMic(); }
    voiceCont = false; voiceStop(); paintMic();
    toast("🎤 หยุดแล้ว — แตะไมค์อีกครั้งเพื่อคุยต่อเนื่อง");
    return;
  }
  voiceCont = true; contTurns = 0; idleSilent = 0;
  paintMic();
  toast("🎤 คุยต่อเนื่อง: เปิดแล้ว — พูดได้เลย บอทตอบจบจะฟังต่อเอง แตะไมค์อีกครั้งเพื่อหยุด");
  startMic();
}

async function startMic(){
  if(micRec && micRec.state === "recording") return; // กันอัดซ้อน
  if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder){
    voiceCont = false; paintMic(); // เริ่มไม่ได้จริง -> ดับลูปไปด้วย (แตะใหม่เพื่อลองอีกครั้ง)
    return micFallback("เบราว์เซอร์นี้ใช้ไมค์อัดเสียงไม่ได้");
  }
  try{
    // echoCancellation กันไมค์ดูดเสียงลำโพงของบอทกลับมา (สำคัญมากในโหมดพูดต่อเนื่อง)
    micStream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
  }catch(e){
    voiceCont = false; paintMic(); // ขอสิทธิ์ไม่ผ่าน -> ดับลูปไปด้วย
    const n = (e && e.name) || "";
    if(n === "NotAllowedError" || n === "SecurityError")
      botSay("⚠️ เบราว์เซอร์ไม่อนุญาตใช้ไมค์ — กดไอคอน 🔒 ข้าง address bar → อนุญาต Microphone แล้วลองใหม่ค่ะ");
    else if(n === "NotFoundError" || n === "OverconstrainedError")
      botSay("⚠️ ไม่พบไมโครโฟนในอุปกรณ์นี้ — ตรวจว่าเสียบ/เปิดไมค์แล้ว หรือพิมพ์แทนได้ค่ะ");
    else
      botSay("⚠️ เปิดไมค์ไม่ได้ (" + escapeHtml(n || "ไม่ทราบสาเหตุ") + ") — ลองรีเฟรชหน้า (Ctrl+F5) แล้วกดใหม่ค่ะ");
    return;
  }
  const mime = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"].find(m => { try{ return MediaRecorder.isTypeSupported(m); }catch(e){ return false; } });
  micChunks = [];
  micRec = new MediaRecorder(micStream, mime ? { mimeType: mime, audioBitsPerSecond: 32000 } : undefined);
  micRec.ondataavailable = e => { if(e.data && e.data.size) micChunks.push(e.data); };
  micRec.onstop = onMicStop;
  micRec.start();
  micStart = Date.now();
  paintMic();
  micTick();
  micTimer = setInterval(micTick, 500);
  vadStart(micStream); // ตัดจบอัตโนมัติเมื่อเงียบเกิน 2.5 วิ (ไม่ต้องพูดยาว คลิปสั้น = แปลงเร็ว)
  setTimeout(() => { if(micRec && micRec.state === "recording") stopMic(); }, MIC_MAX_SEC * 1000);
}
function micTick(){
  const s = Math.floor((Date.now() - micStart) / 1000);
  $("chatStatus").textContent = `● 🎤 กำลังฟัง… 0:${String(s).padStart(2, "0")} / 0:45 — หยุดพูด 4 วิตัดจบเอง หรือกดไมค์เพื่อหยุด`;
}
/* ตรวจจับความเงียบฝั่ง browser: พูดจบแล้วหยุดเกิน 2.5 วิ = ตัดจบส่งเลย (คลิปสั้นลง แปลงเร็วขึ้นมาก) */
let vadCtx = null, vadAn = null, vadTimer = null, vadLastVoice = 0, vadArmed = false;
const VAD_SIL_MS = 4000; // หยุดพูด 4 วิถึงตัดจบ (เผื่อหายใจ/คิดระหว่างประโยค ไม่ตัดประโยคยาว)
function vadStart(stream){
  vadStop();
  try{
    const AC = window.AudioContext || window.webkitAudioContext;
    if(!AC || !stream) return;
    vadCtx = new AC();
    if(vadCtx.state === "suspended"){ vadCtx.resume().catch(() => {}); } // โหมดต่อเนื่องสั่งอัดเองโดยไม่มี gesture ต้องปลุก context
    const src = vadCtx.createMediaStreamSource(stream);
    vadAn = vadCtx.createAnalyser();
    vadAn.fftSize = 512;
    src.connect(vadAn);
    const buf = new Float32Array(vadAn.fftSize);
    vadLastVoice = Date.now(); vadArmed = false;
    vadTimer = setInterval(() => {
      try{
        vadAn.getFloatTimeDomainData(buf);
        let sum = 0;
        for(let i = 0; i < buf.length; i++) sum += buf[i] * buf[i];
        const rms = Math.sqrt(sum / buf.length);
        const now = Date.now();
        if(rms > 0.02){ vadLastVoice = now; vadArmed = true; }
        else if(vadArmed && now - vadLastVoice > VAD_SIL_MS){
          if(micRec && micRec.state === "recording"){ toast("🔇 หยุดพูดแล้ว กำลังแปลงเสียง…"); stopMic(); }
        }
      }catch(e){}
    }, 200);
  }catch(e){}
}
function vadStop(){
  try{
    if(vadTimer){ clearInterval(vadTimer); vadTimer = null; }
    if(vadCtx && vadCtx.close){ vadCtx.close(); }
  }catch(e){}
  vadCtx = null; vadAn = null;
}
/* นาฬิกานับวิตอนรอแปลงเสียง (เห็นว่าเดินอยู่ ไม่รู้สึกว่าค้าง) */
let sttTick = null, sttT0 = 0;
function sttTickStart(){
  sttTickStop();
  sttT0 = Date.now();
  sttTick = setInterval(() => {
    const s = Math.floor((Date.now() - sttT0) / 1000);
    $("chatStatus").textContent = `● 🎤 กำลังแปลงเสียง… (${s} วิ)`;
  }, 1000);
}
function sttTickStop(){ if(sttTick){ clearInterval(sttTick); sttTick = null; } }
function stopMic(){
  clearInterval(micTimer);
  if(micRec && micRec.state === "recording") micRec.stop();
}
async function onMicStop(){
  paintMic();
  vadStop(); // หยุดตัวจับความเงียบ
  const hadVoice = vadArmed; // มีเสียงพูดจริงในช่วงที่อัดหรือไม่
  if(micStream){ micStream.getTracks().forEach(t => t.stop()); micStream = null; }
  const secs = Math.max(1, Math.round((Date.now() - micStart) / 1000));
  micRec = null;
  const blob = new Blob(micChunks, { type: "audio/webm" });
  if(blob.size < 1000){
    $("chatStatus").textContent = "● ออนไลน์ • ตอบทันที";
    botSay("⚠️ ไม่ได้ยินเสียง — กดไมค์แล้วพูดใหม่อีกครั้งค่ะ");
    return;
  }
  if(!hadVoice && secs < 8){
    // คลิปสั้นและไม่มีเสียงพูดเลย: ไม่ส่งให้ Whisper (ต้นตอข้อความ error รัว ๆ)
    $("chatStatus").textContent = "● ออนไลน์ • ตอบทันที";
    if(voiceCont){ loopRearm(); return; } // โหมดต่อเนื่อง: เงียบ ๆ ฟังใหม่
    botSay("⚠️ ไม่ได้ยินเสียงพูดเลย — กดไมค์แล้วพูดใหม่อีกครั้งนะคะ");
    return;
  }
  idleSilent = 0; // มีของส่งจริง รีเซ็ตตัวนับเงียบ
  $("chatStatus").textContent = "● 🎤 กำลังแปลงเสียงเป็นข้อความ…";
  sttTickStart(); // นับวินาทีให้เห็นว่ากำลังทำงาน
  try{
    const fd = new FormData();
    fd.append("audio", blob, "voice.webm");
    fd.append("userId", cdGuestId());
    const ctl = new AbortController();
    const to = setTimeout(() => ctl.abort(), 100000);
    const r = await fetch(STT_URL, { method: "POST", body: fd, signal: ctl.signal });
    clearTimeout(to);
    const j = await r.json();
    if(j && j.ok && j.text) return onVoiceText(j.text, secs, "Whisper");
    if(j && !j.ok && j.error && j.error.indexOf("ไม่ได้ยินเสียง") >= 0){
      // Whisper ฟังไม่ออก: ไม่ใช่เน็ตล่ม ใช้ข้อความเบา ๆ (ข้อความ error เดิมอ่านเหมือนระบบพัง)
      return micFallback("ฟังไม่ชัดเลยค่ะ ");
    }
    throw new Error((j && j.error) || ("HTTP " + r.status));
  }catch(e){
    sttTickStop();
    const why = (e && e.name === "AbortError") ? "Whisper ตอบช้าเกิน 100 วิ" : ("ติดต่อ Whisper ไม่ได้ (" + ((e && e.message) || "เน็ตขัดข้อง") + ")");
    return micFallback(why + " — ");
  }
}
function micFallback(reason){
  // โหมดต่อเนื่อง: ไม่สแปมข้อความในแชท เงียบ ๆ ฟังใหม่ (นับครั้งรวมกับ loopRearm)
  if(voiceCont){ loopRearm(); return; }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SR){
    $("chatStatus").textContent = "● ออนไลน์ • ตอบทันที";
    botSay(`⚠️ ${escapeHtml(reason)}ระบบเสียงสำรองก็ใช้ไม่ได้ — พิมพ์ข้อความแทนได้เลยค่ะ`);
    return;
  }
  botSay(`🎤 ${escapeHtml(reason)}สลับเป็น<b>ไมค์ของเบราว์เซอร์</b>ให้อัตโนมัติ — กดปุ่มไมค์แล้วพูดได้เลยค่ะ`);
  startWebSpeech();
}
/* หัวหน้าลูปเงียบ/พัง: ฟังใหม่เงียบ ๆ ครบ IDLE_MAX ครั้งติดกัน = หยุดลูปพร้อมบอกครั้งเดียว */
function loopRearm(){
  if(!voiceCont) return;
  idleSilent++;
  if(idleSilent >= IDLE_MAX){
    voiceCont = false; paintMic();
    botSay("⏸️ ฟังไม่ชัดหลายครั้งติดกัน เลยหยุดฟังชั่วคราว — แตะไมค์เพื่อคุยต่อได้เลยค่ะ");
    return;
  }
  startMic();
}
function startWebSpeech(){
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SR) return;
  const rec = new SR();
  rec.lang = "th-TH"; rec.interimResults = false; rec.maxAlternatives = 1;
  const t0 = Date.now();
  paintMic();
  $("chatStatus").textContent = "● 🎤 กำลังฟัง (โหมดเบราว์เซอร์)… พูดได้เลย";
  rec.onresult = e => {
    const t = e.results[0][0].transcript;
    const s = Math.max(1, Math.round((Date.now() - t0) / 1000));
    onVoiceText(t, s, "เบราว์เซอร์");
  };
  rec.onerror = () => {
    paintMic();
    $("chatStatus").textContent = "● ออนไลน์ • ตอบทันที";
    botSay("⚠️ ฟังไม่ชัด — ลองพูดใหม่หรือพิมพ์แทนได้ค่ะ");
  };
  rec.onend = () => {
    paintMic();
    if($("chatStatus").textContent.indexOf("เบราว์เซอร์") >= 0) $("chatStatus").textContent = "● ออนไลน์ • ตอบทันที";
  };
  try{ rec.start(); }catch(e){}
  setTimeout(() => { try{ rec.stop(); }catch(e){} }, 30000);
}
/* ============ โหมดสนทนาเสียงสตรีมมิ่ง: Whisper -> Gemini -> Piper ทีละประโยค ============ */
const gemHistory = []; // บริบทบทสนทนาเสียง (เก็บใน session, ส่งให้ Gemini ทุกครั้ง)
let voiceRun = 0;      // ตัวนับรอบเสียง (barge-in = ตัดรอบเก่าทิ้ง)
let voiceAudioEl = null;
// โหมดพูดต่อเนื่อง: บอทพูดจบแล้วเปิดไมค์ฟังต่อเอง (กันลูปคุยกับตัวเองด้วย CONT_MAX)
let voiceCont = false, contTurns = 0;
const CONT_MAX = 15;

function voiceStop(){
  voiceRun++; // ทำให้รอบที่กำลังรันอยู่หยุดทั้งหมด
  try{ if(voiceAudioEl){ voiceAudioEl.pause(); voiceAudioEl.src = ""; } }catch(e){}
  voiceAudioEl = null;
  stopSpeak();
}
function paintMic(){
  const b = $("micBtn"); if(!b) return;
  const rec = !!(micRec && micRec.state === "recording");
  b.classList.toggle("rec", rec);
  b.classList.toggle("loop", voiceCont && !rec);
}
/* hook วินิจฉัย (ไม่มีผลตอนใช้จริง): ตรวจสอบ/จำลองสถานะเสียง */
window.__voiceDbg = {
  getCont: () => voiceCont,
  setCont: v => { voiceCont = !!v; paintMic(); },
  setVad: v => { vadArmed = !!v; },
  setMicStart: t => { micStart = t; },
  pushChunk: c => { micChunks.push(c); },
  getIdle: () => idleSilent
};
/* จบ 1 เทิร์นเสียง: ถ้าโหมดต่อเนื่องยังเปิดอยู่ ให้เปิดไมค์ฟังต่อเอง */
function voiceContinue(run){
  if(!voiceCont || run !== voiceRun) return;
  contTurns++;
  if(contTurns >= CONT_MAX){
    voiceCont = false; paintMic();
    botSay("⏸️ พักการคุยต่อเนื่องชั่วคราว (ครบ 15 เทิร์นป้องกันลูป) — แตะไมค์เพื่อคุยต่อได้เลยค่ะ");
    return;
  }
  startMic();
}
/* หยุดพักระหว่างประโยคแบบขัดจังหวะได้ (กดไมค์/ปิดเสียง = หยุดรอทันที) */
async function voicePause(ms, run){
  let waited = 0;
  while(waited < ms){
    if(run !== voiceRun) return false;
    await new Promise(r => setTimeout(r, Math.min(150, ms - waited)));
    waited += 150;
  }
  return run === voiceRun;
}
function voiceAppend(id, html, plainAdd){
  const d = $("say-" + id);
  if(d){ d.insertAdjacentHTML("beforeend", html); }
  if(plainAdd) sayMap[id] = ((sayMap[id] || "") + " " + plainAdd).trim();
  scrollChat();
}
function splitSentences(t){
  const parts = String(t).split(/(?<=[.!?…\n])/);
  const out = [];
  let cur = "";
  parts.forEach(p => {
    p = (p || "").trim();
    if(!p) return;
    if((cur + " " + p).trim().length > 240){ if(cur.trim()) out.push(cur.trim()); cur = p; }
    else cur = (cur + " " + p).trim();
  });
  if(cur.trim()) out.push(cur.trim());
  return out.length ? out : [String(t)];
}
function ttsFetch(sentence){
  return (async () => {
    try{
      if(typeof URL === "undefined" || !URL.createObjectURL) return null;
      const ctl = new AbortController();
      const to = setTimeout(() => ctl.abort(), 65000);
      const r = await fetch(new URL("api/tts.php", location.href).toString(), {
        method: "POST", headers: {"Content-Type": "application/json"}, signal: ctl.signal,
        body: JSON.stringify({ text: sentence.slice(0, 600), userId: cdGuestId() })
      });
      clearTimeout(to);
      if(!r.ok) return null;
      const b = await r.blob();
      if(!b || b.size < 1000) return null;
      return URL.createObjectURL(b);
    }catch(e){ return null; }
  })();
}
function playUrl(url){
  return new Promise(resolve => {
    if(typeof Audio === "undefined"){ resolve(); return; }
    let done = false;
    const fin = () => { if(!done){ done = true; resolve(); } };
    try{
      const a = new Audio(url);
      voiceAudioEl = a;
      a.onended = () => { if(voiceAudioEl === a) voiceAudioEl = null; fin(); };
      a.onerror = fin;
      a.play().catch(fin);
      setTimeout(fin, 60000);
    }catch(e){ fin(); }
  });
}
/* เทิร์นสนทนาเสียง 1 รอบ: ถาม Gemini -> พูดทีละประโยค (โหลดประโยคถัดไปรอไว้ก่อน) */
/* noContinue=true ใช้กับแชทพิมพ์: ตอบเงียบ ไม่เปิดไมค์ต่อ */
async function voiceTurn(text, noContinue){
  const run = ++voiceRun;
  if(!(await refreshBotMode())) return; // โหมดคนดูแล: ไม่ตอบ
  const bubble = botSay("🎤 <i>กำลังคิด…</i>", true); // quiet: ไม่ใช้เสียง browser ซ้ำซ้อน
  sayMap[bubble] = "";
  $("chatStatus").textContent = "● 🤖 กำลังคิด…";
  let answer = "";
  let ragImages = [], ragSources = [];
  try{
    const ctl = new AbortController();
    const to = setTimeout(() => ctl.abort(), 65000);
    const r = await fetch(new URL("api/gemini.php", location.href).toString(), {
      method: "POST", headers: {"Content-Type": "application/json"}, signal: ctl.signal,
      body: JSON.stringify({ text: text, userId: cdGuestId(), history: gemHistory.slice(-10) })
    });
    clearTimeout(to);
    const j = await r.json();
    if(j && j.ok && j.text){ answer = j.text.trim(); ragImages = j.images || []; ragSources = j.sources || []; }
  }catch(e){}
  if(run !== voiceRun) return;
  if(!answer){ // Gemini ล่ม -> fallback สมองเดิม
    const d = $("say-" + bubble);
    if(d) d.style.display = "none";
    aiReply(text);
    if(!noContinue) voiceContinue(run);
    return;
  }
  gemHistory.push({ role: "user", text: text.slice(0, 500) }, { role: "model", text: answer.slice(0, 500) });
  if(gemHistory.length > 10) gemHistory.splice(0, gemHistory.length - 10);
  cdForwardBot(answer); // สำเนาเข้า ChatDesk
  const d0 = $("say-" + bubble);
  if(d0){ const ph = d0.querySelector("i"); if(ph) ph.remove(); }
  const sentences = splitSentences(answer);
  // ลำโพงปิด = โหมดเงียบ: แสดงข้อความอย่างเดียว ไม่โหลด/เล่นเสียง Piper
  const silent = !spkOn;
  let nextP = null;
  for(let i = 0; i < sentences.length; i++){
    if(run !== voiceRun) return;
    const s = sentences[i];
    if(silent){ voiceAppend(bubble, escapeHtml(s) + " ", s); continue; }
    const cur = nextP || ttsFetch(s);
    nextP = (i + 1 < sentences.length) ? ttsFetch(sentences[i + 1]) : null;
    let url = null;
    try{ url = await cur; }catch(e){}
    if(run !== voiceRun) return;
    voiceAppend(bubble, escapeHtml(s) + " ", s);
    if(!url) continue; // ได้ข้อความแต่ไม่มีเสียง: แสดง text ต่อไป
    $("chatStatus").textContent = `● 🔊 กำลังพูด (${i + 1}/${sentences.length}) — กดไมค์เพื่อขัดจังหวะได้`;
    await playUrl(url);
    try{ URL.revokeObjectURL(url); }catch(e){}
    if(i + 1 < sentences.length){ if(!(await voicePause(VOICE_GAP_MS, run))) return; } // เว้นวรรคระหว่างประโยค
  }
  if(run !== voiceRun) return;
  voiceAttachMedia(bubble, ragImages, ragSources);
  $("chatStatus").textContent = "● ออนไลน์ • ตอบทันที";
  if(!noContinue) voiceContinue(run); // โหมดต่อเนื่อง: เปิดไมค์ฟังเทิร์นถัดไปเอง (เฉพาะเสียง)
  return run;
}

/* แปะรูป + ที่มาจาก RAG ใต้ bubble (ไม่เข้าข้อความเสียงอ่าน) */
function voiceAttachMedia(bubble, images, sources){
  const d = $("say-" + bubble);
  if(!d) return;
  (images || []).slice(0, 3).forEach(u => {
    if(!/^https?:\/\//i.test(u)) return;
    d.insertAdjacentHTML("beforeend", `<br><img src="${u}" alt="รูปประกอบ" loading="lazy" style="max-width:100%;border-radius:10px;margin-top:6px">`);
  });
  if(sources && sources.length){
    d.insertAdjacentHTML("beforeend", `<br><small style="color:#667">ที่มา: ${escapeHtml(sources.slice(0, 3).join(" • "))}</small>`);
  }
  scrollChat();
}

/* ข้อความเสียง: log + ส่ง ChatDesk + เข้าโหมดสนทนาเสียง (แทน aiReply เดิม) */
function onVoiceText(text, secs, via){
  sttTickStop();
  idleSilent = 0; // ได้ transcript แล้ว รีเซ็ตตัวนับเงียบ
  $("chatStatus").textContent = "● ออนไลน์ • ตอบทันที";
  userSay(`<span class="voice-tag">🎤 เสียง (${escapeHtml(via)} ${secs} วิ)</span>${text.replace(/</g, "&lt;")}`);
  if(cdAwaitName){ cdAwaitName = false; setGuestName(text); return; }
  cdForward(text);
  voiceTurn(text);
}
function quickAsk(q){ openChat(); userSay(q); setTimeout(() => aiGate(() => aiReply(q)), 400); }
function askHotel(id){
  const h=HOTELS.find(x=>x.id===id);
  userSay(`ขอข้อมูล ${h.name} หน่อย`);
  setTimeout(async () => { if(!(await refreshBotMode())) return; aiSay(`<b>${h.name}</b> ⭐${h.stars} คะแนน ${h.rating} (${h.reviews.toLocaleString()} รีวิว)<br><img src="${h.img}" alt="รูป ${h.name}" loading="lazy" style="max-width:100%;border-radius:10px;margin:6px 0"><br>📍 ${h.loc}<br>💰 คืนละ ${fmt(h.price)} <s>${fmt(h.old)}</s><br>${h.freeCancel?"✅ ยกเลิกฟรี":"⚠️ ยกเลิกมีค่าธรรมเนียม"}<br>${h.desc}<br><span class="hotel-link">👉 <a href="#" onclick="openHotel(${h.id});return false;">ดูรายละเอียด / จองเลย</a></span>`); },400);
}
function sendChat(){
  const inp=$("chatText"), t=inp.value.trim();
  if(!t) return;
  userSay(t.replace(/</g,"&lt;")); inp.value="";
  if(cdAwaitName){ cdAwaitName=false; setGuestName(t); return; }
  setTimeout(() => aiGate(() => textTurn(t)), 500);
  cdForward(t); // ส่งสำเนาเข้า ChatDesk ให้เจ้าหน้าที่เห็นทันที (ส่งเสมอ แม้โหมดคนดูแล)
}
/* แชทพิมพ์: ใช้ engine เส้นเดียวกับเสียง (RAG + รูป + memory) แบบเงียบ ไม่เปิดไมค์; engine ล่ม -> voiceTurn fallback สมองเดิมเอง */
async function textTurn(t){
  await voiceTurn(t, true);
}

function aiReply(q){
  const s=q.toLowerCase();
  const findBudget = s.match(/(\d[\d,]*)\s*(บาท|฿|bath)?/);
  const destKeys=["กรุงเทพ","เชียงใหม่","ภูเก็ต","พัทยา","กระบี่","หัวหิน","สมุย","เชียงราย","กรุงเทพฯ"];
  const dest = destKeys.find(d=>s.includes(d.replace("ฯ",""))||s.includes(d));

  if(/ยกเลิก|คืนเงิน|refund|cancel/.test(s))
    return aiSay(`❌ <b>วิธียกเลิก:</b> กด “🧾 การจองของฉัน” → เลือกรายการ → “ยกเลิกการจอง”<br>• ที่พักป้าย <b>ยกเลิกฟรี</b> = คืนเต็มจำนวน 3–5 วัน<br>• ต้องการให้เจ้าหน้าที่ช่วย พิมพ์ฝากข้อความไว้ได้เลยค่ะ เดี๋ยวมาตอบในแชทนี้`);

  if(/โปร|โค้ด|คูปอง|ส่วนลด|discount|promo/.test(s))
    return aiSay(`🎁 <b>โปรตอนนี้:</b><br>• โค้ด <b>TRIPTHAI100</b> ลด 100 บาท (กรอกตอนจอง)<br>• สมาชิกใหม่ลด 15% • สะสม coins คืน 5% ทุกการจอง<br>• ผ่อน 0% บัตรที่ร่วมรายการ`);

  if(/จองอย่างไร|วิธีจอง|จองยังไง|how.*book/.test(s))
    return aiSay(`📝 <b>วิธีจอง 3 ขั้น:</b><br>1) เลือกที่พัก → “จองห้องนี้เลย”<br>2) กรอกชื่อ/เบอร์/อีเมล + โค้ดส่วนลด<br>3) กดยืนยัน → ได้รหัสจองทันที (ไม่ต้องจ่ายก่อนถ้าเลือก “จ่ายที่ที่พัก”)`);

  if(/คน|เจ้าหน้าที่|พนักงาน|human|agent|chatdesk/.test(s)){
    return aiSay(`👩‍💼 รับทราบค่ะ ข้อความของคุณ<b>ส่งถึงเจ้าหน้าที่แล้ว</b> — พิมพ์ฝากไว้ตรงนี้ได้เลย เดี๋ยวเจ้าหน้าที่มาตอบในแชทนี้โดยตรงค่ะ`);
  }

  if(/สวัสดี|hello|hi\b/.test(s))
    return aiSay(`สวัสดีค่ะ 😊 ต้องการหาที่พักที่ไหนดีคะ? ลองพิมพ์ “หาที่พักเชียงใหม่” หรือเลือกปุ่มด่วนด้านล่างได้เลย`);

  // ค้นหาที่พัก
  if(/หา|โรงแรม|ที่พัก|รีสอร์ท|วิลล่า|หอ|โฮสเทล|แนะนำ/.test(s) || dest || findBudget){
    let pool=[...HOTELS];
    if(dest){ const d=dest.replace("ฯ",""); pool=pool.filter(h=>(h.loc+h.name).replace("ฯ","").includes(d)); }
    if(findBudget){
      const budget=parseInt(findBudget[1].replace(/,/g,""));
      if(!isNaN(budget)){ pool=pool.filter(h=>h.price<=budget); }
    }
    if(!pool.length) return aiSay(`😢 ไม่เจอที่พักตามเงื่อนไข ลองเพิ่มงบหรือเปลี่ยนจังหวัดดูนะคะ<br>หรือพิมพ์ฝากข้อความถึงเจ้าหน้าที่ได้เลยค่ะ`);
    const top=pool.sort((a,b)=>b.rating-a.rating).slice(0,3);
    return aiSay(`เจอ <b>${pool.length} แห่ง</b>${dest?`ใน${dest}`:""}${findBudget?` งบไม่เกิน ${fmt(parseInt(findBudget[1].replace(/,/g,"")))}`:""} ✨ แนะนำ:<br>`+
      top.map(h=>`🏨 <b>${h.name}</b> — ${fmt(h.price)}/คืน ⭐${h.rating} <a href="#" onclick="openHotel(${h.id});return false;">จอง →</a>`).join("<br>")+
      top.map(h=>`<br><img src="${h.img}" alt="รูป ${h.name}" loading="lazy" style="max-width:100%;border-radius:10px;margin-top:6px">`).join("")+
      `<br><br>เลื่อนดูทั้งหมดในหน้าหลัก หรือพิมพ์ถามเจ้าหน้าที่ได้เลย เดี๋ยวมาตอบในแชทนี้ค่ะ`);
  }

  if(/ราคา|เท่าไหร่|แพง|ถูก/.test(s))
    return aiSay(`💰 ที่พักบนเว็บเริ่ม <b>฿1,400/คืน</b> (เมืองเก่าภูเก็ต) ถึง <b>฿21,500/คืน</b> (พูลวิลล่าแม่ริม) บอกงบ + จังหวัดมาได้เลย เช่น “ภูเก็ต 2000 บาท”`);

  if(/ชำระ|จ่าย|โอน|บัตร/.test(s))
    return aiSay(`💳 ชำระได้ 3 แบบ: บัตรเครดิต / โอนธนาคาร / จ่ายที่ที่พัก<br>รองรับผ่อน 0% และออกใบเสร็จ/ใบกำกับภาษีได้ แจ้งใน “คำขอพิเศษ” ตอนจองค่ะ`);

  return aiSay(`เข้าใจค่ะ 🤖 หนูช่วยได้เรื่อง: <b>หาที่พักตามงบ/จังหวัด, วิธีจอง, ยกเลิก, โปรโมชั่น</b><br>ลองพิมพ์ “หาที่พักภูเก็ต 2000 บาท”<br>หรือพิมพ์ฝากข้อความถึงเจ้าหน้าที่ได้เลย เดี๋ยวมาตอบในแชทนี้ค่ะ`);
}

// ESC ปิด modal
document.addEventListener("keydown",e=>{ if(e.key==="Escape"){ ["hotelModal","bookModal","myModal"].forEach(closeModal); } });
document.querySelectorAll(".modal").forEach(m=>m.addEventListener("click",e=>{ if(e.target===m) m.classList.add("hidden"); }));
