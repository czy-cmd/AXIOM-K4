/* AXIOM · Model K4 / Alpha 3 · 网页版主逻辑（纯原生 JS，无依赖） */
(function () {
  'use strict';

  const C = window.K4_CONFIG;
  const ARTICLES = window.K4_ARTICLES;
  const LEVEL_CATS = window.K4_LEVEL_CATEGORIES;
  const $ = (id) => document.getElementById(id);
  const SKIP = new Set("，。！？；：、“”‘’（）《》〈〉【】「」『』…—·,.;!?:'\"()".split(''));
  const KEY = C.store_key;

  /* ---------- 存档 ---------- */
  function defaultSave() {
    return {
      users: {},
      session: { user: null, mode: 'normal' },
      temp: { points: 0, records: [], favorites: [], mistakes: {}, unlocked: {}, agreement: true },
      settings: { theme: 'system', openMode: 'html', punct: true, debug: false, difficulty: 3 }
    };
  }
  function loadSave() {
    const d = defaultSave();
    try {
      const raw = localStorage.getItem(KEY);
      if (!raw) return d;
      const o = JSON.parse(raw);
      const settings = Object.assign({}, d.settings, o.settings || {});
      delete settings.debugSalt; delete settings.debugHash;
      return {
        users: o.users && typeof o.users === 'object' ? o.users : {},
        session: o.session && typeof o.session === 'object' ? o.session : d.session,
        temp: Object.assign({}, d.temp, o.temp || {}),
        settings
      };
    } catch (e) { return d; }
  }
  let S = loadSave();

  const LOG = [];
  function logLine(msg) {
    LOG.push(new Date().toLocaleTimeString('zh-CN', { hour12: false }) + '  ' + msg);
    if (LOG.length > 500) LOG.shift();
  }
  function persist() {
    if (S.session.mode === 'incognito' || S.session.mode === 'debug') return;
    try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { /* 存储不可用则静默 */ }
  }
  function applySession() {
    document.body.dataset.session = S.session.mode || 'normal';
  }
  function ud() {
    if (S.session.mode === 'normal') {
      if (!S.users[S.session.user]) S.users[S.session.user] = newUserData();
      return S.users[S.session.user];
    }
    return S.temp;
  }
  function newUserData() {
    const unlocked = {};
    LEVEL_CATS.forEach(c => unlocked[c] = 1);
    return { hash: '', salt: '', points: 0, records: [], favorites: [], mistakes: {}, unlocked, agreement: false };
  }
  function hash(str, salt) {
    let h = 2166136261 >>> 0;
    const s = (salt || '') + '|' + str;
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
    return h.toString(16).padStart(8, '0');
  }
  function randSalt() { return Math.random().toString(36).slice(2, 10); }

  /* ---------- 通用 ---------- */
  let currentView = 'login-view';
  let toastTimer = null;

  /* 动效：错峰进场（PCL 风格）。给容器内匹配元素打上 .anim-in 并逐项启动。
     opts = {x:true 横向进场, step:25 每项间隔ms, max:12 最多参与项数} */
  const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function animateIn(container, selector, opts) {
    if (!container || reduceMotion) return;
    opts = opts || {};
    const nodes = Array.prototype.slice.call(container.querySelectorAll(selector || ':scope > *'));
    const step = opts.step || 25;
    const max = opts.max || 12;
    nodes.slice(0, max).forEach((n, i) => {
      n.classList.add('anim-in');
      if (opts.x) n.classList.add('anim-in-x');
      n.style.setProperty('--i', i);
      n.classList.remove('run');
      // 强制回流，确保移除后重新触发动画
      void n.offsetWidth;
      n.classList.add('run');
    });
  }
  // 清理动画类，避免下次渲染时以透明态闪一下
  function clearAnim(container, selector) {
    if (!container) return;
    container.querySelectorAll(selector || '.anim-in').forEach(n => {
      n.classList.remove('anim-in', 'anim-in-x', 'run');
      n.style.removeProperty('--i');
    });
  }

  function toast(msg) {
    const t = $('toast');
    t.textContent = msg; t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.hidden = true, 2600);
  }
  const DEBUG_HIDDEN_VIEWS = ['levels-view', 'records-view', 'settings-view', 'changelog-view'];
  function showView(id) {
    if (S.session.mode === 'debug' && DEBUG_HIDDEN_VIEWS.includes(id)) id = 'menu-view';
    if (typing && id !== 'typing-view') stopTyping();
    document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.id === id));
    currentView = id;
    if (id === 'menu-view') renderMenu();
    if (id === 'articles-view') renderArticles();
    if (id === 'versus-view') renderVersus();
    if (id === 'levels-view') renderLevels();
    if (id === 'records-view') renderRecords();
    if (id === 'settings-view') renderSettings();
    if (id === 'changelog-view') renderChangelog();
    if (id === 'typing-view') updateCaret();
    updateDebugOverlay();
    // 视图进场后对静态卡片做错峰动画（动态列表在各 render 内部处理）
    const view = $(id);
    if (view && id === 'menu-view') animateIn(view, '.menu-card', { step: 35 });
    if (view && id === 'login-view') animateIn(view, '.brand-title, .brand-rule, .brand-slogan, .login-card', { step: 45 });
    if (view && id === 'versus-view') animateIn(view, '.difficulty-box, .field-row, .button-row', { step: 40 });
  }
  document.querySelectorAll('[data-goto]').forEach(b => {
    b.addEventListener('click', () => showView(b.dataset.goto));
  });
  function setTip(el, text, color) {
    el.textContent = text || '';
    el.style.color = color || 'var(--red)';
  }
  function download(name, content, type) {
    const blob = new Blob([content], { type: type || 'text/plain;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  /* ---------- 主题 / 打开模式 ---------- */
  function applyTheme() {
    document.documentElement.dataset.theme = S.settings.theme;
    document.querySelectorAll('input[name="theme"]').forEach(r => r.checked = r.value === S.settings.theme);
  }
  function applyMode() {
    const m = S.settings.openMode;
    document.body.dataset.mode = m;
    document.querySelectorAll('input[name="openmode"]').forEach(r => r.checked = r.value === m);
    const detail = {
      exe: '桌面宽屏布局 · 存档写入本机 data/user_data.json（exe 端）',
      html: '浏览器宽屏布局 · 存档写入浏览器 localStorage，可导出 JSON',
      mobile: '单列触屏布局 · 存档写入浏览器 localStorage，按钮加大并唤起软键盘'
    };
    $('mode-detail').textContent = detail[m] || '';
    $('mode-banner').textContent = '当前：' + ({ exe: 'exe 打开模式', html: 'html 打开模式', mobile: '手机端打开模式' }[m] || m);
  }
  document.querySelectorAll('input[name="theme"]').forEach(r => r.addEventListener('change', () => {
    S.settings.theme = r.value; applyTheme(); persist();
  }));
  document.querySelectorAll('input[name="openmode"]').forEach(r => r.addEventListener('change', () => {
    S.settings.openMode = r.value; applyMode(); persist();
  }));
  $('punct-toggle').addEventListener('change', e => { S.settings.punct = e.target.checked; persist(); });
  applyTheme(); applyMode();

  /* ---------- 登录 ---------- */
  $('pwd-toggle').addEventListener('click', () => {
    const p = $('login-pwd');
    const show = p.type === 'password';
    p.type = show ? 'text' : 'password';
    $('pwd-toggle').textContent = show ? '隐藏' : '显示';
  });
  function validateLogin() {
    const name = $('login-user').value.trim();
    const pwd = $('login-pwd').value;
    if (!name) { setTip($('login-tip'), '请输入用户名'); return null; }
    if (name.length > 20) { setTip($('login-tip'), '用户名太长（最多 20 字）'); return null; }
    if (!pwd) { setTip($('login-tip'), '请输入密码'); return null; }
    if (pwd.length < 6) { setTip($('login-tip'), '密码至少 6 位'); return null; }
    return [name, pwd];
  }
  function enterMenu() {
    const d = ud();
    if (!d.agreement) { showAgreement(); return; }
    showView('menu-view');
  }
  $('btn-login').addEventListener('click', () => {
    setTip($('login-tip'), '');
    const v = validateLogin(); if (!v) return;
    const [name, pwd] = v;
    const d = S.users[name];
    if (!d || !d.hash) { setTip($('login-tip'), '用户不存在，请先点“注册”'); return; }
    if (hash(pwd, d.salt) !== d.hash) {
      setTip($('login-tip'), '密码错误，请重新输入'); $('login-pwd').value = ''; return;
    }
    S.session = { user: name, mode: 'normal' }; applySession(); persist(); logLine('login: ' + name); enterMenu();
  });
  $('btn-register').addEventListener('click', () => {
    setTip($('login-tip'), '');
    const v = validateLogin(); if (!v) return;
    const [name, pwd] = v;
    if (S.users[name] && S.users[name].hash) { setTip($('login-tip'), '用户名已存在，请直接登录'); return; }
    const d = S.users[name] || newUserData();
    d.salt = randSalt(); d.hash = hash(pwd, d.salt);
    S.users[name] = d;
    S.session = { user: name, mode: 'normal' }; applySession(); persist(); logLine('login: ' + name); enterMenu();
  });
  function quickLogin(mode, label) {
    S.session = { user: label, mode: mode };
    S.temp = Object.assign(newUserData(), { agreement: true });
    applySession(); persist(); logLine('session start: ' + mode);
    showView('menu-view');
  }
  $('btn-guest').addEventListener('click', () => quickLogin('guest', '游客'));
  $('btn-incognito').addEventListener('click', () => quickLogin('incognito', '无痕'));
  $('btn-debug-guest').addEventListener('click', () => openDebugPwd('guest'));
  $('login-pwd').addEventListener('keydown', e => { if (e.key === 'Enter') $('btn-login').click(); });
  $('login-user').addEventListener('keydown', e => { if (e.key === 'Enter') $('login-pwd').focus(); });
  $('btn-logout').addEventListener('click', () => {
    logLine('session end: ' + S.session.mode);
    S.session = { user: null, mode: 'normal' }; persist(); applySession();
    $('login-user').value = ''; $('login-pwd').value = ''; setTip($('login-tip'), '');
    showView('login-view');
  });

  /* ---------- 协议 ---------- */
  function showAgreement() {
    const a = window.K4_AGREEMENT;
    $('agreement-title').textContent = a.title;
    $('agreement-body').innerHTML = a.paragraphs.map(p => '<p>' + escapeHtml(p) + '</p>').join('');
    $('agreement-modal').hidden = false;
  }
  $('btn-agree').addEventListener('click', () => {
    ud().agreement = true; persist();
    $('agreement-modal').hidden = true; showView('menu-view');
  });
  $('btn-disagree').addEventListener('click', () => {
    $('agreement-modal').hidden = true;
    S.session = { user: null, mode: 'normal' }; persist(); showView('login-view');
  });

  /* ---------- 菜单 ---------- */
  function renderMenu() {
    const d = ud();
    const isDebug = S.session.mode === 'debug';
    $('menu-user').textContent = isDebug ? 'DEBUG SESSION' : '你好，' + (S.session.user || '玩家');
    $('menu-points').textContent = '积分 ' + (d.points || 0);
    applySession();
    if (isDebug) {
      $('debug-panel-info').textContent =
        'version=' + C.version + '\narticles=' + ARTICLES.length +
        '\nview=' + currentView + '\nstorage=none\nlog_lines=' + LOG.length;
    }
  }

  /* ---------- 选文 ---------- */
  let articleCat = '全部';
  let selectedArticle = null;
  function renderArticles() {
    const box = $('article-cats');
    box.innerHTML = '';
    window.K4_CATEGORIES.forEach(c => {
      const b = document.createElement('button');
      b.className = 'chip' + (c === articleCat ? ' active' : '');
      b.textContent = c;
      b.addEventListener('click', () => { articleCat = c; renderArticles(); });
      box.appendChild(b);
    });
    const favs = ud().favorites || [];
    let list = ARTICLES.filter(a => articleCat === '全部' || (articleCat === '收藏' ? favs.includes(a.id) : a.category === articleCat));
    if (!list.length && articleCat !== '全部') selectedArticle = null;
    $('article-count').textContent = '共 ' + list.length + ' 篇' + (selectedArticle ? ' · 已选：' + (ARTICLES.find(a => a.id === selectedArticle) || {}).title : '');
    const wrap = $('article-list');
    wrap.innerHTML = '';
    list.forEach(a => {
      const row = document.createElement('div');
      row.className = 'list-row' + (selectedArticle === a.id ? ' selected' : '');
      row.innerHTML =
        '<div class="row-main"><div class="row-title">' + escapeHtml(a.title) + '</div>' +
        '<div class="row-sub">' + escapeHtml(a.category) + ' · ' + escapeHtml(a.tags.join(' / ')) + '</div></div>' +
        '<div class="row-meta">' + a.text.length + ' 字</div>';
      const star = document.createElement('button');
      star.className = 'star-btn' + (favs.includes(a.id) ? ' on' : '');
      star.textContent = favs.includes(a.id) ? '★' : '☆';
      star.title = '收藏';
      star.addEventListener('click', e => {
        e.stopPropagation();
        const d = ud(); d.favorites = d.favorites || [];
        const i = d.favorites.indexOf(a.id);
        if (i >= 0) d.favorites.splice(i, 1); else d.favorites.push(a.id);
        persist(); renderArticles();
      });
      row.appendChild(star);
      row.addEventListener('click', () => { selectedArticle = a.id; renderArticles(); });
      wrap.appendChild(row);
    });
    animateIn(box, '.chip', { step: 18, max: 12 });
    animateIn(wrap, '.list-row', { step: 18, max: 14 });
  }
  $('btn-start-article').addEventListener('click', () => {
    const a = ARTICLES.find(x => x.id === selectedArticle);
    if (!a) { toast('请先选择一篇文章'); return; }
    startTyping({ text: a.text, title: a.title, mode: '练习', backView: 'articles-view' });
  });

  /* ---------- 人机对战设置 ---------- */
  let selectedPool = 0;
  let sliderAnim = null;
  function diffIndex() {
    const v = Number($('diff-slider').value);
    return Math.max(0, Math.min(C.difficulties.length - 1, Math.round(v) - 1));
  }
  /* 原生 range 的滑块中心并不在 0%/100%，而在 thumb 半径处；
     文字与刻度按同一公式定位，才不会跟进度条错位。 */
  const THUMB = 20;
  function thumbPos(pct) {
    return 'calc(' + pct + '% + ' + ((0.5 - pct / 100) * THUMB).toFixed(2) + 'px)';
  }
  function paintSlider() {
    const v = Number($('diff-slider').value);
    const pct = (v - 1) / (C.difficulties.length - 1) * 100;
    $('diff-slider').style.setProperty('--diff-pct', pct + '%');
    const marker = $('diff-marker');
    if (marker) {
      marker.style.left = thumbPos(pct);
      marker.textContent = C.difficulties[diffIndex()].code.toUpperCase();
    }
  }
  function renderVersus() {
    const idx = diffIndex();
    const d = C.difficulties[idx];
    $('diff-code').textContent = String(idx + 1).padStart(2, '0') + ' / ' + d.code.toUpperCase();
    $('diff-label').textContent = d.label;
    $('diff-desc').textContent = d.desc + ' · ' + d.min.toFixed(1) + '–' + d.max.toFixed(1) + ' 字/秒';
    document.querySelectorAll('#diff-ticks span').forEach((s, i) => s.classList.toggle('active', i === idx));
    paintSlider();
    const wrap = $('versus-pool');
    wrap.innerHTML = '';
    ARTICLES.slice(0, 10).forEach((a, i) => {
      const row = document.createElement('div');
      row.className = 'list-row' + (selectedPool === i ? ' selected' : '');
      row.innerHTML = '<div class="row-main"><div class="row-title">' + escapeHtml(a.title) +
        '</div><div class="row-sub">' + escapeHtml(a.category) + '</div></div><div class="row-meta">' + a.text.length + ' 字</div>';
      row.addEventListener('click', () => { selectedPool = i; renderVersus(); });
      wrap.appendChild(row);
    });
  }
  function saveDifficulty(v) {
    if (S.settings.difficulty === v) return;
    S.settings.difficulty = v; persist();
    logLine('difficulty=' + C.difficulties[v - 1].code);
  }
  function snapSlider() {
    const target = diffIndex() + 1;
    const slider = $('diff-slider');
    const from = Number(slider.value);
    if (sliderAnim) { cancelAnimationFrame(sliderAnim); sliderAnim = null; }
    if (Math.abs(target - from) < 0.002) {
      slider.value = String(target); renderVersus(); saveDifficulty(target); return;
    }
    const t0 = performance.now(), dur = 260;
    const step = (now) => {
      const p = Math.min(1, (now - t0) / dur);
      const e = 1 - Math.pow(1 - p, 3);
      slider.value = String(from + (target - from) * e);
      renderVersus();
      if (p < 1) sliderAnim = requestAnimationFrame(step);
      else { sliderAnim = null; slider.value = String(target); renderVersus(); saveDifficulty(target); }
    };
    sliderAnim = requestAnimationFrame(step);
  }
  $('diff-ticks').innerHTML = C.difficulties.map((d, i) =>
    '<span style="left:' + thumbPos(i / (C.difficulties.length - 1) * 100) + '">' + d.code.toUpperCase() + '</span>').join('');
  $('diff-slider').value = String(S.settings.difficulty || 3);
  $('diff-slider').addEventListener('input', renderVersus);
  ['pointerup', 'mouseup', 'touchend', 'change', 'keyup'].forEach(ev => {
    $('diff-slider').addEventListener(ev, snapSlider);
  });
  $('btn-start-versus').addEventListener('click', () => {
    const a = ARTICLES[selectedPool] || ARTICLES[0];
    startTyping({
      text: a.text, title: 'VERSUS · ' + a.title, mode: '人机对战', backView: 'versus-view',
      difficulty: diffIndex() + 1, agents: Number($('agent-count').value)
    });
  });

  /* ---------- 关卡 ---------- */
  let levelCat = LEVEL_CATS[0];
  function levelArticle(cat, n) {
    const pool = ARTICLES.filter(a => a.category === cat);
    const base = pool.length ? pool : ARTICLES;
    return base[n % base.length];
  }
  function renderLevels() {
    const box = $('level-cats');
    box.innerHTML = '';
    LEVEL_CATS.forEach(c => {
      const b = document.createElement('button');
      b.className = 'chip' + (c === levelCat ? ' active' : '');
      b.textContent = c;
      b.addEventListener('click', () => { levelCat = c; renderLevels(); });
      box.appendChild(b);
    });
    const unlocked = ud().unlocked || {};
    const cur = unlocked[levelCat] || 1;
    const grid = $('level-grid');
    grid.innerHTML = '';
    for (let i = 1; i <= 4; i++) {
      const b = document.createElement('button');
      b.className = 'level-btn';
      b.disabled = i > cur;
      b.innerHTML = '<div class="lv-num">0' + i + '</div><div class="lv-sub">' +
        (i > cur ? '未解锁' : escapeHtml(levelArticle(levelCat, i - 1).title)) + '</div>';
      b.addEventListener('click', () => {
        const a = levelArticle(levelCat, i - 1);
        startTyping({ text: a.text, title: levelCat + ' · 第 ' + i + ' 关', mode: '关卡', backView: 'levels-view',
          finishCb: (res) => {
            if (res.gradeIndex <= 3 && i === cur && cur < 4) {
              ud().unlocked[levelCat] = cur + 1; persist(); toast('已解锁下一关');
            }
          }
        });
      });
      grid.appendChild(b);
    }
    animateIn(box, '.chip', { step: 18, max: 12 });
    animateIn(grid, '.level-btn', { step: 30, max: 8 });
  }

  /* ---------- 打字核心 ---------- */
  let typing = null;
  function gradeOf(score) {
    const t = [[450, 'S', 0], [320, 'A', 1], [200, 'B', 2], [110, 'C', 3], [45, 'D', 4], [0, 'F', 5]];
    for (const row of t) if (score >= row[0]) return { grade: row[1], index: row[2] };
    return { grade: 'F', index: 5 };
  }
  function calcScore(correct, wrong) {
    const acc = (correct + wrong) ? correct / (correct + wrong) : 0;
    return Math.floor(correct * (200 / 300) * (0.5 + 0.5 * acc));
  }
  function rand(a, b) { return a + Math.random() * (b - a); }

  function startTyping(opts) {
    if (typing) stopTyping();
    const punct = S.settings.punct;
    const chars = [];
    for (const c of opts.text) chars.push({ c, skip: !punct && SKIP.has(c), state: '' });
    const spans = [];
    const panel = $('type-text');
    panel.innerHTML = '';
    chars.forEach((ch, i) => {
      const s = document.createElement('span');
      s.textContent = ch.c === ' ' ? '\u00a0' : ch.c;
      if (ch.skip) s.className = 'ch-skip';
      panel.appendChild(s); spans.push(s);
    });
    $('type-title').textContent = opts.title || '练习';
    $('race-hud').style.display = opts.mode === '人机对战' ? '' : 'none';

    const t = {
      chars, spans, pos: 0, correct: 0, wrong: 0, len: chars.length,
      start: 0, elapsed: 0, timer: null, botTimer: null, lastTick: Date.now(),
      mode: opts.mode || '练习', backView: opts.backView || 'menu-view',
      finishCb: opts.finishCb || null, difficulty: opts.difficulty || 3,
      agents: opts.agents || Number($('agent-count').value), bots: [], ended: false
    };
    typing = t;
    logLine('typing start: ' + t.mode + ' / ' + (opts.title || '-') + ' / diff=' + t.difficulty);
    if (t.mode === '人机对战') initBots(t);
    renderAgentBars(t);
    renderHud(t);
    updateStats(t);
    showView('typing-view');
    t.start = Date.now();
    t.timer = setInterval(() => tick(t), 100);
    $('ghost-input').value = '';
    composing = false; composedText = ''; skipNextInput = false;
    try { $('ghost-input').focus(); } catch (e) { /* 桌面端靠 document 监听 */ }
  }
  function initBots(t) {
    const d = C.difficulties[t.difficulty - 1] || C.difficulties[2];
    t.bots = [];
    for (let i = 0; i < t.agents; i++) {
      t.bots.push({ name: 'AGENT-' + String(i + 1).padStart(2, '0'), pos: 0, speed: rand(d.min, d.max), done: false });
    }
  }
  function tick(t) {
    if (t.ended) return;
    const now = Date.now();
    const dt = (now - t.lastTick) / 1000; t.lastTick = now;
    t.elapsed = (now - t.start) / 1000;
    const remain = Math.max(0, C.time_limit - t.elapsed);
    const m = Math.floor(remain / 60), s = Math.floor(remain % 60);
    $('type-timer').textContent = String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
    if (t.mode === '人机对战') {
      t.bots.forEach(b => {
        if (!b.done) {
          b.pos += b.speed * dt * rand(0.75, 1.25);
          if (b.pos >= t.len) { b.pos = t.len; b.done = true; }
        }
      });
      renderAgentBars(t); renderHud(t);
    }
    if (remain <= 0) finishTyping(t);
  }
  function advanceSkip(t, dir) {
    while (t.pos >= 0 && t.pos < t.len && t.chars[t.pos].skip) t.pos += dir;
  }
  function typeChar(ch) {
    const t = typing;
    if (!t || t.ended) return;
    advanceSkip(t, 1);
    if (t.pos >= t.len) return;
    const c = t.chars[t.pos];
    const ok = c.c === ch;
    c.state = ok ? 'correct' : 'wrong';
    t.spans[t.pos].className = (c.skip ? 'ch-skip ' : '') + (ok ? 'ch-correct' : 'ch-wrong');
    if (ok) t.correct++; else {
      t.wrong++;
      const d = ud(); d.mistakes = d.mistakes || {};
      d.mistakes[ch] = (d.mistakes[ch] || 0) + 1;
    }
    t.pos++;
    advanceSkip(t, 1);
    highlight(t); updateStats(t); renderHud(t);
    if (t.pos >= t.len) finishTyping(t);
  }
  function moveBack(t) {
    if (t.pos <= 0) return;
    t.pos--;
    while (t.pos >= 0 && t.chars[t.pos].skip) t.pos--;
    if (t.pos < 0) { t.pos = 0; return; }
    const c = t.chars[t.pos];
    if (c.state === 'correct') t.correct = Math.max(0, t.correct - 1);
    if (c.state === 'wrong') t.wrong = Math.max(0, t.wrong - 1);
    c.state = '';
    t.spans[t.pos].className = c.skip ? 'ch-skip' : '';
    highlight(t); updateStats(t); renderHud(t);
  }
  function moveForward(t) {
    t.pos++; advanceSkip(t, 1);
    if (t.pos > t.len) t.pos = t.len;
    highlight(t);
  }
  function highlight(t) {
    t.spans.forEach((s, i) => s.classList.toggle('ch-current', i === t.pos));
    updateCaret();
    const span = t.spans[t.pos];
    if (span) {
      const wrap = $('type-text-wrap');
      const r = span.getBoundingClientRect(), w = wrap.getBoundingClientRect();
      if (r.bottom > w.bottom - 10) wrap.scrollTop += r.bottom - w.bottom + 40;
      if (r.top < w.top + 10) wrap.scrollTop -= w.top - r.top + 40;
    }
  }
  function updateCaret() {
    const t = typing, caret = $('caret');
    if (!t || !t.spans[t.pos]) { caret.style.display = 'none'; return; }
    const wrap = $('type-text-wrap');
    const r = t.spans[t.pos].getBoundingClientRect();
    const w = wrap.getBoundingClientRect();
    caret.style.display = 'block';
    caret.style.left = (r.left - w.left + wrap.scrollLeft + r.width / 2) + 'px';
    caret.style.top = (r.top - w.top + wrap.scrollTop - 13) + 'px';
    /* 隐藏输入框贴到当前字旁：中文输入法的候选框会跟着光标出现 */
    const gi = $('ghost-input');
    if (gi) { gi.style.left = Math.round(r.left) + 'px'; gi.style.top = Math.round(r.top) + 'px'; }
  }
  function updateStats(t) {
    const acc = (t.correct + t.wrong) ? Math.round(t.correct / (t.correct + t.wrong) * 100) : 100;
    $('type-acc').textContent = '准确率 ' + acc + '%';
    $('type-score').textContent = calcScore(t.correct, t.wrong) + ' 分';
    $('type-progress').textContent = t.pos + ' / ' + t.len + ' 字　正确 ' + t.correct + '　错误 ' + t.wrong;
  }
  function renderHud(t) {
    if (t.mode !== '人机对战') return;
    const youPct = Math.min(100, Math.round(t.correct / t.len * 100));
    $('you-bar').style.width = youPct + '%';
    $('you-pct').textContent = youPct + '%';
    $('you-count').textContent = t.correct + ' 字';
    const lead = t.bots.reduce((m, b) => Math.max(m, b.pos), 0);
    const leadPct = Math.min(100, Math.round(lead / t.len * 100));
    $('lead-bar').style.width = leadPct + '%';
    $('lead-pct').textContent = leadPct + '%';
    $('lead-count').textContent = Math.floor(lead) + ' 字';
  }
  function renderAgentBars(t) {
    const box = $('agent-bars');
    if (!box) return;
    const sorted = t.bots.slice().sort((a, b) => b.pos - a.pos);
    let html = '';
    sorted.forEach(b => {
      const pct = Math.min(100, Math.round(b.pos / t.len * 100));
      html += '<div class="agent-row' + (b.done ? ' done' : '') + '">' +
        '<div class="agent-head"><span>' + b.name + '</span><span>' + pct + '%' +
        (S.settings.debug ? ' · ' + b.speed.toFixed(2) : '') + '</span></div>' +
        '<div class="bar"><div class="fill" style="width:' + pct + '%"></div></div></div>';
    });
    const myRank = sorted.filter(b => b.pos > t.correct).length + 1;
    html += '<div class="agent-row me"><div class="agent-head"><span>YOU / 名次 ' + myRank + '</span><span>' +
      Math.min(100, Math.round(t.correct / t.len * 100)) + '%</span></div>' +
      '<div class="bar"><div class="fill" style="width:' + Math.min(100, Math.round(t.correct / t.len * 100)) + '%"></div></div></div>';
    box.innerHTML = html;
  }
  function stopTyping() {
    if (!typing) return;
    clearInterval(typing.timer);
    typing.ended = true; typing = null;
  }
  function finishTyping(t) {
    if (t.ended) return;
    t.ended = true;
    clearInterval(t.timer);
    const typed = t.correct + t.wrong;
    const acc = typed ? t.correct / typed * 100 : 0;
    const speed = t.elapsed > 0 ? t.correct / (t.elapsed / 60) : 0;
    const score = calcScore(t.correct, t.wrong);
    const g = gradeOf(score);
    logLine('typing finish: ' + g.grade + ' / ' + score + ' / acc=' + Math.round(acc) + '%');
    const d = ud();
    d.points = (d.points || 0) + score;
    const rec = {
      date: new Date().toLocaleString('zh-CN'), mode: t.mode, title: $('type-title').textContent,
      score, grade: g.grade, acc: Math.round(acc), speed: Math.round(speed),
      difficulty: t.mode === '人机对战' ? C.difficulties[t.difficulty - 1].code : ''
    };
    d.records = d.records || []; d.records.unshift(rec);
    d.records = d.records.slice(0, 300);
    persist();
    if (t.finishCb) { try { t.finishCb({ score, grade: g.grade, gradeIndex: g.index }); } catch (e) { /* ignore */ } }
    let extra = '';
    if (t.mode === '人机对战') {
      const rank = t.bots.filter(b => b.pos > t.correct).length + 1;
      extra = '<div class="result-line"><span>名次</span><b>' + rank + ' / ' + (t.bots.length + 1) + '</b></div>' +
        '<div class="result-line"><span>难度</span><b>' + C.difficulties[t.difficulty - 1].code.toUpperCase() + '</b></div>';
    }
    $('result-body').innerHTML =
      '<div class="grade" style="color:var(--accent)">' + g.grade + '</div>' +
      '<div class="result-line"><span>得分</span><b>' + score + '</b></div>' +
      '<div class="result-line"><span>准确率</span><b>' + Math.round(acc) + '%</b></div>' +
      '<div class="result-line"><span>速度</span><b>' + Math.round(speed) + ' 字/分</b></div>' + extra;
    $('result-modal').hidden = false;
    typing = null;
  }
  $('btn-result-close').addEventListener('click', () => {
    $('result-modal').hidden = true;
    const back = typing ? typing.backView : null;
    const view = back || lastTypingBack || 'menu-view';
    showView(view);
  });
  let lastTypingBack = 'menu-view';
  const origStartTyping = startTyping;
  startTyping = function (opts) { lastTypingBack = opts.backView || 'menu-view'; return origStartTyping(opts); };
  function quitTyping() {
    logLine('typing quit: ' + (typing ? typing.mode : '-'));
    stopTyping(); showView(lastTypingBack);
  }
  $('btn-quit-type').addEventListener('click', quitTyping);
  $('btn-type-back').addEventListener('click', quitTyping);
  $('btn-focus-input').addEventListener('click', () => {
    try { $('ghost-input').focus(); toast('键盘已就绪，开始输入'); }
    catch (e) { toast('无法唤起键盘'); }
  });
  $('btn-move-back').addEventListener('click', () => { if (typing) moveBack(typing); });
  $('btn-move-forward').addEventListener('click', () => { if (typing) moveForward(typing); });

  let immersive = false;
  let fsNativeExiting = false;
  function fsActive() {
    return !!(document.fullscreenElement || document.webkitFullscreenElement || immersive);
  }
  function toggleFullscreen() {
    if (document.fullscreenElement || document.webkitFullscreenElement) {
      fsNativeExiting = true;
      const exit = document.exitFullscreen || document.webkitExitFullscreen;
      if (exit) { try { const p = exit.call(document); if (p && p.catch) p.catch(() => {}); } catch (e) { /* noop */ } }
      return;
    }
    if (immersive) {
      immersive = false; document.body.classList.remove('immersive');
      $('btn-fullscreen').textContent = '全屏'; return;
    }
    const el = document.documentElement;
    const req = el.requestFullscreen || el.webkitRequestFullscreen;
    immersive = true; document.body.classList.add('immersive');
    $('btn-fullscreen').textContent = '退出全屏';
    if (req) {
      try { const p = req.call(el); if (p && p.catch) p.catch(() => {}); } catch (e) { /* 保留沉浸式布局 */ }
    } else {
      toast('浏览器不支持原生全屏，已切换沉浸式布局');
    }
  }
  $('btn-fullscreen').addEventListener('click', toggleFullscreen);
  document.addEventListener('fullscreenchange', () => {
    if (!document.fullscreenElement && !document.webkitFullscreenElement && fsNativeExiting) {
      immersive = false; fsNativeExiting = false;
      document.body.classList.remove('immersive');
    }
    $('btn-fullscreen').textContent = fsActive() ? '退出全屏' : '全屏';
  });
  $('btn-export-log').addEventListener('click', () => {
    const head = [
      'AXIOM / MODEL K4 / ALPHA 3 DEBUG LOG',
      'generated=' + new Date().toLocaleString('zh-CN'),
      'version=' + C.version, 'session=' + S.session.mode,
      'view=' + currentView, 'articles=' + ARTICLES.length,
      'storage=' + (S.session.mode === 'debug' ? 'off' : 'on'), ''
    ];
    download('k4_debug.log', head.concat(LOG).join('\r\n'), 'text/plain;charset=utf-8');
    logLine('log exported');
    toast('log 已导出');
  });

  /* ---------- 键盘与输入法 ----------
     唯一输入源是 #ghost-input 的 input / compositionend。
     document.keydown 只负责功能键和「输入框没聚焦时」的兜底字符；
     对已聚焦输入框的可打印键绝不 preventDefault，否则中文输入法拿不到击键。 */
  const ghost = $('ghost-input');
  let composing = false;
  let composedText = '';
  let skipNextInput = false;
  let skipInputTimer = null;

  function feedText(text) {
    if (!typing || typing.ended) return;
    for (const ch of String(text)) {
      if (!typing || typing.ended) break;
      typeChar(ch);
    }
  }
  ghost.addEventListener('compositionstart', () => {
    composing = true; composedText = ''; ghost.value = '';
  });
  ghost.addEventListener('compositionupdate', e => { composedText = e.data || ''; });
  ghost.addEventListener('compositionend', e => {
    composing = false;
    const data = (e.data != null && e.data !== '') ? e.data : (ghost.value || composedText);
    ghost.value = ''; composedText = '';
    skipNextInput = true;
    clearTimeout(skipInputTimer);
    skipInputTimer = setTimeout(() => { skipNextInput = false; }, 0);
    if (data) feedText(data);
  });
  ghost.addEventListener('input', e => {
    if (skipNextInput) { skipNextInput = false; clearTimeout(skipInputTimer); ghost.value = ''; return; }
    if (composing || e.isComposing || e.keyCode === 229) return;
    const v = ghost.value;
    ghost.value = '';
    if (v) feedText(v);
  });
  ghost.addEventListener('blur', () => { composing = false; composedText = ''; });

  document.addEventListener('keydown', e => {
    const imeBusy = composing || e.isComposing || e.keyCode === 229;
    if (imeBusy) return;
    if (e.key === 'F9') { e.preventDefault(); toggleDebugOverlay(); return; }
    if (e.key === 'F10') { e.preventDefault(); copyDiagnostics(); return; }
    if (!typing || !$('result-modal').hidden || !$('agreement-modal').hidden || !$('pwd-modal').hidden) return;
    if (e.key === 'Escape') { e.preventDefault(); quitTyping(); return; }
    if (e.key === 'Backspace') { e.preventDefault(); moveBack(typing); return; }
    if (e.key === 'ArrowLeft') { e.preventDefault(); moveBack(typing); return; }
    if (e.key === 'ArrowRight') { e.preventDefault(); moveForward(typing); return; }
    if (e.target === ghost) return; /* 已聚焦：交给 input 事件，避免重复输入 */
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key.length === 1) { e.preventDefault(); typeChar(e.key); }
  });
  $('type-text-wrap').addEventListener('click', () => { try { ghost.focus(); } catch (e) { /* noop */ } });
  window.addEventListener('resize', () => { if (typing) updateCaret(); });
  $('type-text-wrap').addEventListener('scroll', () => { if (typing) updateCaret(); });

  /* ---------- 纪录 ---------- */
  function renderRecords() {
    const d = ud(), recs = d.records || [];
    const best = recs.reduce((m, r) => Math.max(m, r.score || 0), 0);
    const avg = recs.length ? Math.round(recs.reduce((s, r) => s + (r.acc || 0), 0) / recs.length) : 0;
    const stats = [
      { num: d.points || 0, lab: '总积分' }, { num: recs.length, lab: '练习次数' },
      { num: best, lab: '最高分' }, { num: avg + '%', lab: '平均准确率' }
    ];
    $('rec-stats').innerHTML = stats.map(s => '<div class="stat-card"><div class="num">' + s.num + '</div><div class="lab">' + s.lab + '</div></div>').join('');
    const mistakes = Object.entries(d.mistakes || {}).sort((a, b) => b[1] - a[1]).slice(0, 16);
    $('notebook').innerHTML = mistakes.length
      ? mistakes.map(m => '<div class="list-row"><div class="row-main"><span class="row-title">' + escapeHtml(m[0]) + '</span></div><div class="row-meta">错 ' + m[1] + ' 次</div></div>').join('')
      : '<div class="list-row muted">暂无错字记录</div>';
    $('rec-table').innerHTML = recs.length
      ? recs.slice(0, 20).map(r => '<div class="list-row"><div class="row-main"><div class="row-title">' +
          escapeHtml(r.title) + '</div><div class="row-sub">' + escapeHtml(r.date) + ' · ' + escapeHtml(r.mode) +
          (r.difficulty ? ' · ' + escapeHtml(r.difficulty) : '') + '</div></div><div class="row-meta">' +
          r.score + ' 分 · ' + r.grade + '</div></div>').join('')
      : '<div class="list-row muted">暂无成绩</div>';
    animateIn($('rec-stats'), '.stat-card', { step: 35, max: 4 });
  }
  $('btn-export-records').addEventListener('click', () => {
    const recs = (ud().records || []).slice().reverse();
    if (!recs.length) { toast('暂无成绩可导出'); return; }
    const head = ['date', 'mode', 'title', 'difficulty', 'score', 'grade', 'acc', 'speed'];
    const lines = [head.join(',')].concat(recs.map(r => head.map(k => '"' + String(r[k] == null ? '' : r[k]).replace(/"/g, '""') + '"').join(',')));
    download('k4_results.csv', '\ufeff' + lines.join('\r\n'), 'text/csv;charset=utf-8');
  });
  $('btn-mistake-practice').addEventListener('click', () => {
    const m = Object.entries(ud().mistakes || {}).sort((a, b) => b[1] - a[1]).map(x => x[0]);
    if (!m.length) { toast('错字本为空'); return; }
    let text = '';
    while (text.length < 220) text += m.join('');
    text = text.slice(0, 220);
    startTyping({ text, title: '错字专项练习', mode: '练习', backView: 'records-view' });
  });

  /* ---------- 调试密码：固定口令，仅验证，不提供设置/修改 ---------- */
  let debugPwdContext = 'settings';
  function openDebugPwd(context) {
    debugPwdContext = context;
    $('debug-pwd').value = '';
    setTip($('pwd-tip'), '');
    $('pwd-modal').hidden = false;
    setTimeout(() => { try { $('debug-pwd').focus(); } catch (e) { /* noop */ } }, 30);
  }
  function confirmDebugPwd() {
    if ($('debug-pwd').value !== C.debug_password) {
      setTip($('pwd-tip'), '调试密码不正确');
      logLine('debug password rejected'); return;
    }
    $('pwd-modal').hidden = true;
    logLine('debug password accepted: ' + debugPwdContext);
    if (debugPwdContext === 'guest') {
      quickLogin('debug', 'DEBUG');
      toast('已进入调试会话：无存储');
    } else {
      S.settings.debug = true; persist();
      $('debug-toggle').checked = true;
      renderSettings(); toast('调试模式已开启'); updateDebugOverlay();
    }
  }
  $('pwd-cancel').addEventListener('click', () => {
    $('pwd-modal').hidden = true;
    $('debug-toggle').checked = S.settings.debug;
  });
  $('pwd-ok').addEventListener('click', confirmDebugPwd);
  $('debug-pwd').addEventListener('keydown', e => { if (e.key === 'Enter') confirmDebugPwd(); });
  $('debug-toggle').addEventListener('change', e => {
    if (e.target.checked) {
      e.target.checked = S.settings.debug;
      openDebugPwd('settings');
    } else {
      S.settings.debug = false; persist();
      $('debug-overlay').hidden = true; renderSettings(); updateDebugOverlay();
    }
  });

  function renderSettings() {
    $('punct-toggle').checked = S.settings.punct;
    applyTheme(); applyMode();
    $('debug-toggle').checked = S.settings.debug;
    $('debug-box').innerHTML =
      '<div class="debug-line">状态：' + (S.settings.debug ? '已开启（F9 显示 / F10 复制诊断）' : '已关闭') + '</div>' +
      '<div class="debug-line">密码：固定口令，设置内不可修改</div>' +
      (S.settings.debug ? '<div class="button-row"><button id="btn-debug-info" class="btn ghost">诊断信息</button></div>' : '');
    const b2 = $('btn-debug-info');
    if (b2) b2.addEventListener('click', () => toast(diagnostics()));
  }
  $('btn-changelog').addEventListener('click', () => showView('changelog-view'));

  /* ---------- 更新日志 ---------- */
  function renderChangelog() {
    $('changelog-body').innerHTML = window.K4_CHANGELOG.map(c => {
      const group = (title, arr) => arr && arr.length
        ? '<div class="change-group"><b>' + title + '</b><ul>' + arr.map(x => '<li>' + escapeHtml(x) + '</li>').join('') + '</ul></div>'
        : '';
      return '<div class="change-block"><div class="change-head"><h3>' + escapeHtml(c.version) + '</h3><span>' +
        escapeHtml(c.date) + '</span></div>' + group('ADDED', c.added) + group('CHANGED', c.changed) + group('FIXED', c.fixed) + '</div>';
    }).join('');
    animateIn($('changelog-body'), '.change-block', { step: 45, max: 10 });
  }

  /* ---------- 数据导入导出 / 清空 ---------- */
  $('btn-export-data').addEventListener('click', () => {
    download('k4_alpha3_backup.json', JSON.stringify(S, null, 2), 'application/json');
  });
  $('btn-import-data').addEventListener('click', () => $('import-file').click());
  $('import-file').addEventListener('change', e => {
    const f = e.target.files[0]; if (!f) return;
    const r = new FileReader();
    r.onload = () => {
      try {
        const o = JSON.parse(r.result);
        if (!o || !o.settings || !o.session) throw new Error('格式不正确');
        if (!confirm('导入将覆盖当前浏览器中的存档，确定继续？')) return;
        S = Object.assign(defaultSave(), o); persist(); applyTheme(); applyMode();
        showView('menu-view'); toast('导入成功');
      } catch (err) { toast('导入失败：' + err.message); }
    };
    r.readAsText(f, 'utf-8');
    e.target.value = '';
  });
  $('btn-wipe').addEventListener('click', () => {
    if (!confirm('确定清空当前用户的全部数据？此操作不可撤销。')) return;
    const keep = { theme: S.settings.theme, openMode: S.settings.openMode,
      debug: S.settings.debug, difficulty: S.settings.difficulty };
    const fresh = defaultSave();
    fresh.settings = Object.assign(fresh.settings, keep);
    S = fresh; persist(); applyTheme(); applyMode(); showView('menu-view'); toast('已清空');
  });

  /* ---------- 调试覆盖层 ---------- */
  function diagnostics() {
    return [
      'app=AXIOM model=K4 edition=Alpha3', 'view=' + currentView,
      'theme=' + S.settings.theme, 'mode=' + S.settings.openMode,
      'user=' + (S.session.user || '-'), 'session=' + S.session.mode,
      'articles=' + ARTICLES.length, 'records=' + ((ud().records || []).length),
      'screen=' + window.screen.width + 'x' + window.screen.height,
      'scale=' + (window.devicePixelRatio || 1),
      'ua=' + navigator.userAgent.slice(0, 80)
    ].join('\n');
  }
  function toggleDebugOverlay() {
    if (!S.settings.debug) { toast('请先开启调试模式'); return; }
    const o = $('debug-overlay'); o.hidden = !o.hidden; updateDebugOverlay();
  }
  function updateDebugOverlay() {
    const o = $('debug-overlay');
    if (!S.settings.debug || o.hidden) return;
    const t = typing;
    const speeds = t && t.bots.length ? t.bots.slice(0, 3).map(b => b.speed.toFixed(2)).join(' ') : '-';
    o.textContent = 'DEBUG / ' + currentView + '\n' +
      'tick=100ms  bots=' + (t ? t.bots.length : 0) + '\n' +
      'ai_speed=' + speeds + '\n' +
      'theme=' + S.settings.theme + '  mode=' + S.settings.openMode + '\n' +
      'F9 hide  F10 copy';
  }
  function copyDiagnostics() {
    if (!S.settings.debug) { toast('请先开启调试模式'); return; }
    const text = diagnostics();
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => toast('诊断信息已复制'), () => toast(text));
    } else { toast(text); }
  }
  setInterval(() => { if (S.settings.debug) updateDebugOverlay(); }, 1000);

  /* ---------- 启动 ---------- */
  if (!['normal', 'guest', 'incognito', 'debug'].includes(S.session.mode)) S.session = { user: null, mode: 'normal' };
  applySession();
  logLine('app start: ' + C.version + ' / session=' + S.session.mode);
  if (S.session.user && S.session.mode && S.session.mode !== 'normal') showView('menu-view');
  else if (S.session.user && S.users[S.session.user]) showView('menu-view');
  else showView('login-view');
})();
