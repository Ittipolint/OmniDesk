/* ChatDesk — หน้าจอกล่องข้อความ */
(function () {
  'use strict';

  var cfg = window.CD;

  var convList  = document.getElementById('convList');
  var listEmpty = document.getElementById('listEmpty');
  var searchBox = document.getElementById('searchBox');
  var tabs      = document.getElementById('tabs');
  var placeholder = document.getElementById('placeholder');
  var chatWrap  = document.getElementById('chatWrap');
  var thread    = document.getElementById('thread');
  var composer  = document.getElementById('composer');
  var input     = document.getElementById('msgInput');
  var btnSend   = document.getElementById('btnSend');
  var btnBot    = document.getElementById('btnBot');
  var btnClose  = document.getElementById('btnClose');
  var btnDelete = document.getElementById('btnDelete');
  var btnUpload = document.getElementById('btnUpload');
  var btnSticker = document.getElementById('btnSticker');
  var fileInput = document.getElementById('fileInput');
  var stickerPanel = document.getElementById('stickerPanel');
  var liveDot   = document.getElementById('liveDot');
  var liveText  = document.getElementById('liveText');
  var toastEl   = document.getElementById('toast');

  var filter    = 'all';
  var search    = '';
  var currentId = 0;
  var cursor    = 0;
  var botOn     = true;
  var sending   = false;
  var toastTimer = null;

  /* ------------------------------- utilities ------------------------------ */

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function toast(msg, bad) {
    toastEl.textContent = msg;
    toastEl.className = 'toast' + (bad ? ' bad' : '');
    toastEl.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.hidden = true; }, 3200);
  }

  function live(state, text) {
    liveDot.className = 'dot' + (state ? ' ' + state : '');
    liveText.textContent = text;
  }

  function postJson(url, data) {
    data.csrf = cfg.csrf;
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(data)
    }).then(function (r) {
      return r.json().then(function (d) { return { status: r.status, data: d }; });
    });
  }

  /* ---------------------------- รายการห้องแชท ----------------------------- */

  // ฟังคลิกที่ <ul> ครั้งเดียว (event delegation) — ไม่ผูกกับ <li> แต่ละตัว
  // เพราะรายการถูกวาดใหม่ทุกไม่กี่วินาที ถ้าผูกที่ <li> คลิกจะหลุดตอนวาดใหม่พอดี
  convList.addEventListener('click', function (ev) {
    var li = ev.target.closest('li[data-id]');
    if (li) { openConversation(parseInt(li.getAttribute('data-id'), 10)); }
  });

  var lastListSig = '';

  function renderList(items) {
    listEmpty.hidden = items.length > 0;

    // ถ้าหน้าตาเหมือนเดิมทุกอย่าง ไม่ต้องวาดใหม่ — กันจอกระพริบและกันตำแหน่ง scroll เด้ง
    var sig = items.map(function (c) {
      return [c.id, c.unread, c.botEnabled ? 1 : 0, c.time, c.preview, c.name, c.source || '',
              c.id === currentId ? 1 : 0].join('|');
    }).join('~');
    if (sig === lastListSig) { return; }
    lastListSig = sig;

    var html = items.map(function (c) {
      var avatar = c.picture ? '<img src="' + esc(c.picture) + '" alt="">' : '👤';
      return '<li data-id="' + c.id + '" class="' + (c.id === currentId ? 'on' : '') + '">' +
        '<div class="av">' + avatar + '</div>' +
        '<div class="body">' +
          '<div class="r1">' +
            '<b>' + esc(c.name) + '</b>' +
            (c.unread ? '<span class="badge">' + c.unread + '</span>' : '') +
            (c.botEnabled ? '' : '<span class="pill human">คนดูแล</span>') +
            (c.source ? '<span class="pill bot">' + esc(c.source) + '</span>' : '') +
            '<span class="t">' + esc(c.time) + '</span>' +
          '</div>' +
          '<div class="r2">' + esc(c.preview || '—') + '</div>' +
        '</div>' +
      '</li>';
    }).join('');

    var keepScroll = convList.scrollTop;
    convList.innerHTML = html;
    convList.scrollTop = keepScroll;
  }

  function loadInbox() {
    var url = cfg.api.inbox + '?filter=' + encodeURIComponent(filter) +
              '&q=' + encodeURIComponent(search);
    return fetch(url, { credentials: 'same-origin' })
      .then(function (r) {
        if (r.status === 401) { location.reload(); return null; }
        return r.json();
      })
      .then(function (d) {
        if (!d) { return; }
        if (!d.ok) { live('err', d.error || 'โหลดรายการไม่สำเร็จ'); return; }
        renderList(d.items);
        document.getElementById('n-all').textContent    = d.counts.open;
        document.getElementById('n-unread').textContent = d.counts.unread;
        document.getElementById('n-human').textContent  = d.counts.human;
        document.getElementById('n-closed').textContent = d.counts.closed;
        live('on', 'เชื่อมต่ออยู่');
      })
      .catch(function () { live('err', 'ขาดการเชื่อมต่อ'); });
  }

  /* -------------------------------- ห้องแชท ------------------------------- */

  function bubble(m) {
    var el = document.createElement('div');
    el.className = 'msg ' + m.sender + (m.status === 'error' ? ' err' : '');
    el.setAttribute('data-id', m.id);

    var who = { customer: 'ลูกค้า', bot: 'บอท', agent: 'เรา', system: '' }[m.sender] || '';
    var tag = '';
    if (m.sender === 'bot')   { tag = '<span class="tag bot">บอทตอบ</span>'; }
    if (m.sender === 'agent') { tag = '<span class="tag agent">เราตอบ</span>'; }

    // สถานะส่ง/อ่าน — LINE ไม่มี read receipt ให้บอท ดังนั้น "✓✓" คือคนดูแลเปิดดูในหน้านี้แล้วเท่านั้น
    var ticks = '';
    if (m.sender !== 'system') {
      if (m.status === 'error') {
        ticks = '<span class="ticks err" title="ส่งไม่สำเร็จ">!</span>';
      } else if (m.sender === 'customer') {
        ticks = m.read
          ? '<span class="ticks read" title="เปิดดูแล้ว (ในหน้านี้)">✓✓</span>'
          : '<span class="ticks" title="ยังไม่ได้เปิดดู">✓✓</span>';
      } else {
        // ส่งไปยัง LINE สำเร็จ — ไม่มีข้อมูลว่าลูกค้าอ่านหรือยัง (LINE ไม่แจ้งให้บอท)
        ticks = m.read
          ? '<span class="ticks read" title="เปิดดูแล้ว (ในหน้านี้)">✓✓</span>'
          : '<span class="ticks" title="ส่งแล้ว">✓</span>';
      }
    }

    var delBtn = (m.sender === 'bot' || m.sender === 'agent')
      ? '<button type="button" class="msg-del" data-del="' + m.id + '" title="ลบข้อความ (เฉพาะหน้านี้ — LINE ไม่มี API ให้ลบข้อความที่ส่งไปแล้ว)">'
        + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'
        + '<path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>'
        + '</button>'
      : '';

    var meta = m.sender === 'system' ? '' :
      '<div class="meta">' + tag + '<span>' + esc(m.time) + '</span>' + ticks + '</div>';

    var body = bodyFor(m);
    el.innerHTML = '<div class="bubble-wrap">' + delBtn + '<div class="bubble">' + body + '</div></div>' + meta +
      (m.status === 'error' && m.error ? '<div class="err-note">⚠️ ' + esc(m.error) + '</div>' : '');
    return el;
  }

  function bodyFor(m) {
    if (m.type === 'image' && m.mediaUrl) {
      return '<a href="' + esc(m.mediaUrl) + '" target="_blank" rel="noopener noreferrer" class="media-wrap">' +
             '<img src="' + esc(m.mediaPreviewUrl || m.mediaUrl) + '" alt="ภาพ" loading="lazy"></a>';
    }
    if (m.type === 'video' && m.mediaUrl) {
      return '<video class="media-video" controls preload="metadata" src="' + esc(m.mediaUrl) + '"></video>';
    }
    if (m.type === 'sticker' && m.stickerId) {
      var pkg = m.stickerPackage || '11537';
      var stk = m.stickerId;
      return '<img class="media-sticker" src="https://stickershop.line-scdn.net/stickershop/v1/sticker/' +
             encodeURIComponent(stk) + '/android/sticker.png" alt="สติกเกอร์">';
    }
    return m.html;
  }

  function appendMessages(list) {
    list.forEach(function (m) { thread.appendChild(bubble(m)); });
    thread.scrollTop = thread.scrollHeight;
  }

  // ลบข้อความ (บอท / เจ้าหน้าที่) — event delegation เพราะ thread ถูกวาดใหม่บ่อย
  thread.addEventListener('click', function (ev) {
    var btn = ev.target.closest('.msg-del');
    if (!btn || !currentId) { return; }
    var msgId = parseInt(btn.getAttribute('data-del'), 10);
    if (!msgId) { return; }
    if (!confirm('ลบข้อความนี้?\n(เฉพาะหน้าจอแชทของ ChatDesk — ข้อความที่ลูกค้าเห็นใน LINE จะถูกลบไม่ได้ ป้องกันโดย LINE)')) { return; }
    postJson(cfg.api.action, { conversationId: currentId, action: 'delete_message', messageId: msgId })
      .then(function (res) {
        var d = res.data || {};
        if (!d.ok) { toast(d.error || 'ลบข้อความไม่สำเร็จ', true); return; }
        toast('ลบข้อความแล้ว');
        var el = thread.querySelector('.msg[data-id="' + msgId + '"]');
        if (el) { el.remove(); }
        loadInbox();
      })
      .catch(function () { toast('ลบข้อความไม่สำเร็จ ตรวจการเชื่อมต่อ', true); });
  });

  function setBotState(on) {
    botOn = on;
    btnBot.className = 'btn bot-btn' + (on ? '' : ' off');
    document.getElementById('botIcon').textContent = on ? '🤖' : '🙋';
    document.getElementById('botLabel').textContent = on ? 'บอทตอบอยู่' : 'คนดูแลอยู่';
    document.getElementById('composerNote').textContent = on
      ? 'พิมพ์ตอบแล้วระบบจะปิดบอทห้องนี้ให้อัตโนมัติ'
      : 'บอทหยุดตอบห้องนี้แล้ว — กดปุ่ม 🙋 เพื่อให้บอทกลับมาตอบ';
  }

  function openConversation(id) {
    currentId = id;
    cursor = 0;
    thread.innerHTML = '';
    stickerPanel.hidden = true;
    placeholder.hidden = true;
    chatWrap.hidden = false;

    fetch(cfg.api.thread + '?id=' + id, { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d.ok) { toast(d.error || 'เปิดห้องแชทไม่สำเร็จ', true); return; }
        var c = d.conversation;
        document.getElementById('convName').textContent = c.name;
        document.getElementById('convMeta').textContent =
          'LINE • ' + c.userId + ' • เริ่มคุย ' + c.since + (c.status === 'closed' ? ' • ปิดเคสแล้ว' : '');
        document.getElementById('convAvatar').innerHTML =
          c.picture ? '<img src="' + esc(c.picture) + '" alt="">' : '👤';
        btnClose.textContent = c.status === 'closed' ? 'เปิดเคสใหม่' : 'ปิดเคส';
        setBotState(c.botEnabled);
        appendMessages(d.messages);
        cursor = d.lastId;
        loadInbox();
        input.focus();
      })
      .catch(function () { toast('เปิดห้องแชทไม่สำเร็จ', true); });
  }

  function pollThread() {
    if (!currentId) { return Promise.resolve(); }
    return fetch(cfg.api.thread + '?id=' + currentId + '&since=' + cursor, { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d.ok) { return; }
        if (d.messages && d.messages.length) {
          appendMessages(d.messages);
          cursor = d.lastId;
          setBotState(d.conversation.botEnabled);
        }
      })
      .catch(function () {});
  }

  /* --------------------------------- ส่งข้อความ --------------------------- */

  composer.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var text = input.value.trim();
    if (!text || sending || !currentId) { return; }

    sending = true;
    btnSend.disabled = true;

    postJson(cfg.api.send, { conversationId: currentId, text: text })
      .then(function (res) {
        var d = res.data || {};
        if (!d.ok) {
          toast(d.error || 'ส่งไม่สำเร็จ', true);
        } else {
          input.value = '';
          autoGrow();
          if (d.botMuted) { setBotState(false); toast('ปิดบอทห้องนี้ให้อัตโนมัติแล้ว'); }
        }
        return pollThread();
      })
      .catch(function () { toast('ส่งไม่สำเร็จ ตรวจการเชื่อมต่อ', true); })
      .then(function () {
        sending = false;
        btnSend.disabled = false;
        input.focus();
        loadInbox();
      });
  });

  function autoGrow() {
    input.style.height = 'auto';
    var h = Math.min(input.scrollHeight, 130);
    input.style.height = h + 'px';
    input.style.overflowY = input.scrollHeight > 130 ? 'auto' : 'hidden';
  }
  input.addEventListener('input', autoGrow);
  input.addEventListener('keydown', function (ev) {
    if (ev.key === 'Enter' && !ev.shiftKey) {
      ev.preventDefault();
      composer.dispatchEvent(new Event('submit', { cancelable: true }));
    }
  });

  /* ------------------------------ ส่งภาพ / วิดีโอ --------------------------- */

  btnUpload.addEventListener('click', function () { fileInput.click(); });

  fileInput.addEventListener('change', function () {
    var file = fileInput.files && fileInput.files[0];
    if (!file || !currentId) { fileInput.value = ''; return; }

    var isImage = /^image\//.test(file.type);
    var isVideo = /^video\//.test(file.type);
    if (!isImage && !isVideo) {
      toast('รองรับเฉพาะไฟล์ภาพหรือวิดีโอ', true);
      fileInput.value = '';
      return;
    }

    var fd = new FormData();
    fd.append('file', file, file.name);
    fd.append('csrf', cfg.csrf);

    var xhr = new XMLHttpRequest();
    xhr.open('POST', cfg.api.upload);
    xhr.withCredentials = true;
    xhr.onload = function () {
      fileInput.value = '';
      if (xhr.status !== 200) {
        var err = 'อัปโหลดไม่สำเร็จ';
        try { err = JSON.parse(xhr.responseText).error || err; } catch (e) {}
        toast(err, true);
        return;
      }
      var d;
      try { d = JSON.parse(xhr.responseText); } catch (e) { d = null; }
      if (!d || !d.ok || !d.url) { toast('อัปโหลดไม่สำเร็จ', true); return; }
      sendMedia(isImage ? 'image' : 'video', d.url, d.url);
    };
    xhr.onerror = function () { fileInput.value = ''; toast('อัปโหลดไม่สำเร็จ ตรวจการเชื่อมต่อ', true); };
    xhr.send(fd);
  });

  function sendMedia(type, url, previewUrl) {
    if (sending || !currentId) { return; }
    sending = true;
    btnSend.disabled = true;

    var payload = {
      conversationId: currentId,
      type: type,
      mediaUrl: url,
      mediaPreviewUrl: previewUrl || ''
    };
    if (type === 'image' && previewUrl) { payload.mediaPreviewUrl = previewUrl; }

    postJson(cfg.api.send, payload)
      .then(function (res) {
        var d = res.data || {};
        if (!d.ok) {
          toast(d.error || 'ส่งไม่สำเร็จ', true);
        } else {
          if (d.botMuted) { setBotState(false); toast('ปิดบอทห้องนี้ให้อัตโนมัติแล้ว'); }
        }
        return pollThread();
      })
      .catch(function () { toast('ส่งไม่สำเร็จ ตรวจการเชื่อมต่อ', true); })
      .then(function () {
        sending = false;
        btnSend.disabled = false;
        loadInbox();
      });
  }

  /* -------------------------------- สติกเกอร์ ------------------------------ */

  var STICKER_SETS = [
    { pkg: '11537', name: 'Nyan Cat / สัตว์น่ารัก', ids: ['52002734','52002735','52002736','52002737','52002738','52002739'] },
    { pkg: '11539', name: 'สติกเกอร์คลาสสิก', ids: ['51626496','51626497','51626498','51626499'] },
    { pkg: '11610', name: 'สติกเกอร์มินิมอล', ids: ['51626552','51626553','51626554','51626555'] }
  ];

  btnSticker.addEventListener('click', function () {
    if (!currentId) { return; }
    stickerPanel.hidden = !stickerPanel.hidden;
    if (!stickerPanel.hidden && stickerPanel.children.length === 0) {
      STICKER_SETS.forEach(function (set) {
        set.ids.forEach(function (stid) {
          var img = document.createElement('img');
          img.className = 'stk';
          img.src = 'https://stickershop.line-scdn.net/stickershop/v1/sticker/' +
                    encodeURIComponent(stid) + '/android/sticker.png';
          img.alt = set.name;
          img.title = set.name;
          img.dataset.pkg = set.pkg;
          img.dataset.id = stid;
          img.loading = 'lazy';
          stickerPanel.appendChild(img);
        });
      });
    }
  });

  stickerPanel.addEventListener('click', function (ev) {
    var img = ev.target.closest('img.stk');
    if (!img || !currentId) { return; }
    stickerPanel.hidden = true;
    sendSticker(img.dataset.pkg, img.dataset.id);
  });

  function sendSticker(pkg, stid) {
    if (sending || !currentId) { return; }
    sending = true;
    btnSend.disabled = true;

    postJson(cfg.api.send, {
      conversationId: currentId,
      type: 'sticker',
      stickerPackage: pkg,
      stickerId: stid
    })
      .then(function (res) {
        var d = res.data || {};
        if (!d.ok) {
          toast(d.error || 'ส่งสติกเกอร์ไม่สำเร็จ', true);
        } else {
          if (d.botMuted) { setBotState(false); toast('ปิดบอทห้องนี้ให้อัตโนมัติแล้ว'); }
        }
        return pollThread();
      })
      .catch(function () { toast('ส่งสติกเกอร์ไม่สำเร็จ', true); })
      .then(function () {
        sending = false;
        btnSend.disabled = false;
        loadInbox();
      });
  }

  /* ---------------------------------- คำสั่ง ------------------------------ */

  function doAction(action, confirmText) {
    if (!currentId) { return; }
    if (confirmText && !confirm(confirmText)) { return; }
    postJson(cfg.api.action, { conversationId: currentId, action: action })
      .then(function (res) {
        var d = res.data || {};
        if (!d.ok) { toast(d.error || 'ทำรายการไม่สำเร็จ', true); return; }
        toast(d.message || 'เรียบร้อย');
        if (d.deleted) {
          currentId = 0;
          chatWrap.hidden = true;
          placeholder.hidden = false;
        } else {
          if (typeof d.botEnabled === 'boolean') { setBotState(d.botEnabled); }
          if (d.status) { btnClose.textContent = d.status === 'closed' ? 'เปิดเคสใหม่' : 'ปิดเคส'; }
          pollThread();
        }
        loadInbox();
      })
      .catch(function () { toast('ทำรายการไม่สำเร็จ', true); });
  }

  btnBot.addEventListener('click', function () { doAction(botOn ? 'bot_off' : 'bot_on'); });
  btnClose.addEventListener('click', function () {
    doAction(btnClose.textContent === 'ปิดเคส' ? 'close' : 'reopen');
  });
  if (btnDelete) btnDelete.addEventListener('click', function () {
    doAction('delete', 'ลบห้องแชทนี้พร้อมข้อความทั้งหมด?\nข้อมูลที่ลบแล้วกู้คืนไม่ได้');
  });

  /* --------------------------------- ฟิลเตอร์ ----------------------------- */

  tabs.addEventListener('click', function (ev) {
    var b = ev.target.closest('.tab');
    if (!b) { return; }
    Array.prototype.forEach.call(tabs.querySelectorAll('.tab'), function (t) { t.classList.remove('on'); });
    b.classList.add('on');
    filter = b.getAttribute('data-filter');
    loadInbox();
  });

  var searchTimer = null;
  searchBox.addEventListener('input', function () {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(function () {
      search = searchBox.value.trim();
      loadInbox();
    }, 350);
  });

  /* ---------------------------------- เริ่ม ------------------------------- */

  loadInbox();
  setInterval(loadInbox, Math.max(3, cfg.pollInbox) * 1000);
  setInterval(pollThread, Math.max(2, cfg.pollThread) * 1000);
  autoGrow();
})();
