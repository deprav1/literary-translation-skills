import { METHODS, createState, validState, personalCounts, percentage, rememberLegacy } from './logic.mjs';

const $ = id => document.getElementById(id);
const STORAGE = 'blind-translation-v1';
const LABELS = { skilled: 'AI + навыки', published: 'Опубликованный перевод', baseline: 'AI: короткий запрос', reviewed: 'AI + редактура' };
const REACTIONS = {
  skilled: ['Тебе зашёл AI с инструкциями.', 'Здесь модель работала с навыком художественного перевода. Получился именно этот текст — не обещание, что он лучше во всём.'],
  published: ['Ты выбрал опубликованный перевод.', 'Никаких медалей за «правильный» выбор. Просто этот голос тебе ближе. Автор перевода и источник — на карточке.'],
  baseline: ['Короткий запрос тоже умеет попадать.', 'Это та же модель, но без подключённого переводческого навыка. Не плохой вариант «для контраста», а обычный независимый ответ.'],
  reviewed: ['Твой выбор — AI с редактурой.', 'Модель перевела фрагмент и отдельно сверила его с оригиналом и контекстом рассказа. Человеческой редакторской проверки не было.'],
};
let data, config, state, screen = 'home', memoryOnly = false, eraseBusy = false;
const LEGACY_STORAGE = 'blind-translation-legacy-participants-v1';
const inFlight = new Map();

function el(tag, className, text) { const node = document.createElement(tag); if (className) node.className = className; if (text !== undefined) node.textContent = text; return node; }
function safeLink(label, href) { const a = el('a', '', label); a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; return a; }
function persist() { try { localStorage.setItem(STORAGE, JSON.stringify(state)); } catch { memoryOnly = true; } }
function toast(text) { $('toast').textContent = text; $('toast').hidden = false; clearTimeout(toast.timer); toast.timer = setTimeout(() => { $('toast').hidden = true; }, 4000); }
function pluralRu(n, one, few, many) { const last = n % 10, lastTwo = n % 100; return lastTwo >= 11 && lastTwo <= 14 ? many : last === 1 ? one : last >= 2 && last <= 4 ? few : many; }
function answered() { return Object.keys(state.choices).length; }
function currentRound() { return data.rounds.find(r => r.id === state.order[state.index]); }
function show(view, focus = true) {
  screen = view;
  for (const id of ['home', 'arena', 'results']) $(id).hidden = id !== view;
  $('ground-rules').hidden = view !== 'home';
  if (view === 'arena') renderRound();
  if (view === 'results') renderResults();
  if (focus) { window.scrollTo({ top: 0, behavior: 'instant' }); $('main').focus({ preventScroll: true }); }
}
function updateStart() { $('start-button').textContent = answered() ? `Продолжить · ${answered()} из ${state.order.length} ↗` : 'Начать вслепую ↗'; $('start-button').disabled = false; $('home-results-button').disabled = false; }
function start() {
  if (answered() === state.order.length) { show('results'); return; }
  const index = state.order.findIndex(id => !state.choices[id]);
  if (index >= 0) state.index = index;
  persist(); show('arena');
}
function renderRound() {
  const round = currentRound(); const choice = state.choices[round.id];
  $('progress-text').textContent = `ВЫБРАНО ${answered()} / ${state.order.length}`;
  $('progress-fill').style.width = `${answered() / state.order.length * 100}%`;
  $('round-label').textContent = `РАУНД ${state.index + 1} / ${state.order.length} · ${choice ? 'МАСКИ СНЯТЫ' : 'АВТОРСТВО СКРЫТО'}`;
  $('round-title').textContent = choice ? 'Твой выбор.\nБез фильтров.' : 'Какой вариант\nпопал в нерв?';
  $('round-title').style.whiteSpace = 'pre-line';
  $('round-tag').textContent = round.tag;
  $('source-text').textContent = round.source;
  $('source-credit').textContent = `${round.author} · ${round.title}`;
  $('arena-hint').textContent = choice ? 'Сравни впечатление с лейблом. Изменить отправленный выбор нельзя.' : 'Читай в любом порядке. Авторство покажем только после твоего выбора.';
  $('candidates').replaceChildren();
  state.candidateOrders[round.id].forEach((id, index) => {
    const candidate = round.candidates.find(c => c.id === id); const selected = choice?.candidateId === id;
    const card = el('article', `candidate${selected ? ' selected' : ''}`);
    const top = el('div', 'candidate-top'); top.append(el('span', 'candidate-letter', `ВАРИАНТ ${['А', 'Б', 'В', 'Г'][index]}`), el('span', 'candidate-eye')); top.lastChild.setAttribute('aria-hidden', 'true');
    card.append(top, el('p', 'candidate-text', candidate.text));
    if (!choice) {
      const button = el('button', 'vote-button', 'Беру этот ↗'); button.setAttribute('aria-label', `Выбрать вариант ${['А', 'Б', 'В', 'Г'][index]}`); button.addEventListener('click', () => choose(round.id, id)); card.append(button);
    } else {
      const identity = el('div', 'identity');
      if (selected) identity.append(el('span', 'choice-badge', '✓ ТВОЙ ВЫБОР'));
      identity.append(el('strong', '', LABELS[candidate.method]), el('p', '', candidate.credit), el('p', '', candidate.note));
      if (candidate.sourceUrl) identity.append(safeLink('Источник перевода ↗', candidate.sourceUrl));
      card.append(identity);
    }
    $('candidates').append(card);
  });
  const panel = $('reveal-panel'); panel.hidden = !choice; panel.replaceChildren();
  if (choice) {
    const candidate = round.candidates.find(c => c.id === choice.candidateId); const [title, text] = REACTIONS[candidate.method];
    const body = el('div'); body.append(el('h3', '', title), el('p', '', text)); panel.append(el('span', 'reveal-icon', '↗'), body);
  }
  $('next-button').hidden = !choice;
  $('round-results-button').hidden = !choice;
  $('next-button').textContent = answered() === state.order.length ? 'Посмотреть мой вкус ↗' : 'Следующий раунд →';
  renderSync(); updateStart();
}
function choose(roundId, candidateId) {
  if (state.choices[roundId] || eraseBusy) return;
  state.choices[roundId] = { candidateId, voteId: crypto.randomUUID(), status: 'pending', selectedAt: Date.now() };
  persist(); renderRound();
  submit(roundId);
}
async function api(path, options = {}) {
  if (!config?.apiBase) throw new Error('unconfigured');
  const controller = new AbortController(); const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(config.apiBase + path, { ...options, credentials: 'omit', signal: controller.signal });
    let payload; try { payload = await response.json(); } catch { throw new Error('bad_response'); }
    return { response, payload };
  } finally { clearTimeout(timeout); }
}
async function submit(roundId) {
  if (inFlight.has(roundId)) return inFlight.get(roundId);
  const choice = state.choices[roundId]; if (!choice || choice.status === 'saved' || eraseBusy) return;
  choice.status = 'pending'; persist(); if (screen === 'arena' && currentRound().id === roundId) renderSync();
  const body = { dataset: data.version, fragmentId: roundId, candidateId: choice.candidateId, participantId: state.participantId, voteId: choice.voteId };
  const task = (async () => {
    try {
      const { response, payload } = await api('/votes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      if (response.status === 409 && payload.error === 'already_voted') {
        const round = data.rounds.find(r => r.id === roundId);
        if (!round.candidates.some(c => c.id === payload.candidateId)) throw new Error('bad_response');
        choice.candidateId = payload.candidateId; choice.status = 'saved';
        toast('У этого браузера уже был голос за этот текст. Показываем сохранённый выбор.');
      } else if (response.ok && payload.dataset === data.version && payload.candidateId === choice.candidateId && payload.fragmentId === roundId && typeof payload.voteId === 'string' && /^[a-f0-9-]{36}$/i.test(payload.voteId)) { choice.status = 'saved'; choice.voteId = payload.voteId; }
      else if (response.status === 410 && payload.error === 'participant_erased') { state = createState(data); persist(); choice.status = 'failed'; choice.error = 'participant_erased'; toast('Эта сессия уже удалена. Создали новый локальный идентификатор.'); }
      else { choice.status = 'failed'; choice.error = payload.error || 'unavailable'; }
    } catch { choice.status = 'failed'; choice.error = 'network'; }
    finally {
      inFlight.delete(roundId); persist();
      if (screen === 'arena' && currentRound().id === roundId) renderRound();
      if (screen === 'results') renderResults();
    }
  })();
  inFlight.set(roundId, task); return task;
}
function renderSync() {
  const choice = state.choices[currentRound().id]; const target = $('sync-status'); target.replaceChildren();
  if (!choice) { target.textContent = memoryOnly ? 'Хранилище браузера недоступно: прогресс сохранится только до закрытия страницы.' : 'Один выбор на текст. При перезагрузке прогресс останется в этом браузере.'; return; }
  if (choice.status === 'saved') target.textContent = '✓ Голос принят общим счётчиком.';
  else if (choice.status === 'pending') target.textContent = 'Выбор сохранён здесь. Отправляем в общий счётчик…';
  else {
    target.textContent = choice.error === 'rate_limited' ? 'Выбор сохранён здесь. Сегодня с этой сети слишком много запросов — сервер временно не принял голос.' : 'Выбор сохранён здесь. Общий счётчик пока не подтвердил голос.';
    const retry = el('button', 'inline-button', 'Отправить снова'); retry.addEventListener('click', () => submit(currentRound().id)); target.append(' ', retry);
  }
}
function next() {
  if (answered() === state.order.length) { show('results'); return; }
  const nextIndex = state.order.findIndex((id, i) => i > state.index && !state.choices[id]);
  state.index = nextIndex >= 0 ? nextIndex : state.order.findIndex(id => !state.choices[id]); persist(); $('source-text').closest('details').open = false; show('arena');
}
function renderResults() {
  const n = answered(); const counts = personalCounts(state, data); const highest = Math.max(...Object.values(counts));
  $('results-title').textContent = n ? 'Вот какой\nу тебя вкус.' : 'Итоги\nголосования.';
  $('results-title').style.whiteSpace = 'pre-line';
  $('personal-caption').textContent = n ? `Ты выбрал ${n} ${n === 1 ? 'фрагмент' : n < 5 ? 'фрагмента' : 'фрагментов'} из ${state.order.length}. Это профиль твоих предпочтений в этой подборке. Не экзамен. И не диагноз.` : 'Твоих голосов пока нет. Общие итоги — ниже.';
  $('personal-result').hidden = !n;
  $('share-button').hidden = !n;
  $('personal-result').replaceChildren();
  for (const method of METHODS) { const card = el('div', `score-card${counts[method] && counts[method] === highest ? ' leading' : ''}`); card.append(el('span', '', 'ТВОЙ ВЫБОР'), el('strong', '', `${counts[method]} / ${n}`), el('p', '', LABELS[method])); $('personal-result').append(card); }
  $('continue-button').textContent = !n ? 'Начать вслепую ↗' : n === state.order.length ? 'Посмотреть раунды ещё раз ↗' : 'Вернуться на ринг ↗';
  $('history-list').replaceChildren();
  for (const [index, id] of state.order.entries()) {
    const choice = state.choices[id]; if (!choice) continue;
    const round = data.rounds.find(r => r.id === id); const candidate = round.candidates.find(c => c.id === choice.candidateId);
    const row = el('div', 'history-item'); const copy = el('div'); copy.append(el('span', '', `РАУНД ${index + 1} · ${round.author}`), el('b', '', LABELS[candidate.method]), el('span', '', choice.status === 'saved' ? 'В общем счётчике' : 'Пока только в этом браузере'));
    const button = el('button', 'text-button', 'Перечитать ↗'); button.addEventListener('click', () => { state.index = index; persist(); show('arena'); }); row.append(copy, button); $('history-list').append(row);
  }
  if (!n) $('history-list').append(el('p', 'section-description', 'Пока здесь чистый лист.'));
  renderWorld();
  renderPreviousWorld();
}
async function renderWorld() {
  const target = $('world-stats');
  target.replaceChildren(el('p', 'section-description', 'Считаем голоса…'));
  try {
    const { response, payload } = await api(`/stats?dataset=${encodeURIComponent(data.version)}`);
    if (!response.ok || !Number.isSafeInteger(payload.totalVotes) || !Number.isSafeInteger(payload.participantBrowsers)) throw new Error('stats');
    const counts = payload.methods;
    if (!METHODS.every(m => Number.isSafeInteger(counts?.[m]) && counts[m] >= 0) || METHODS.reduce((n, m) => n + counts[m], 0) !== payload.totalVotes) throw new Error('stats');
    target.replaceChildren();
    const totals = el('div', 'world-counts');
    for (const [number, text] of [[payload.totalVotes, pluralRu(payload.totalVotes, 'голос', 'голоса', 'голосов')], [payload.participantBrowsers, pluralRu(payload.participantBrowsers, 'браузер', 'браузера', 'браузеров')]]) { const item = el('span'); item.append(el('b', '', String(number)), document.createTextNode(text)); totals.append(item); }
    target.append(totals);
    if (!payload.totalVotes) { target.append(el('p', 'empty-stats', 'Первый голос ещё не добрался до сервера. Попробуй обновить через пару секунд — или отправь свой выбор снова.')); return; }
    for (const method of METHODS) {
      const row = el('div', 'stat-row'); const bar = el('div', 'stat-bar'); const fill = el('div'); fill.style.width = `${percentage(counts[method], payload.totalVotes)}%`; bar.append(fill);
      row.append(el('span', '', LABELS[method]), bar, el('span', 'stat-percent', `${percentage(counts[method], payload.totalVotes)}%`)); row.setAttribute('aria-label', `${LABELS[method]}: ${counts[method]} из ${payload.totalVotes} голосов`); target.append(row);
    }
  } catch { target.replaceChildren(el('p', 'empty-stats', 'Общий счётчик сейчас не отвечает. Никаких нарисованных процентов: твои локальные выборы на месте. Попробуй «Обновить».')); }
}
async function renderPreviousWorld() {
  const target = $('previous-stats');
  const previousLabels = { ...LABELS, reviewed: 'AI + самопроверка' };
  if (!data.previousDataset) { target.replaceChildren(); return; }
  target.replaceChildren(el('p', 'section-description', 'Загружаем прежние голоса…'));
  try {
    const [{ response, payload }, catalogResponse] = await Promise.all([
      api(`/stats?dataset=${encodeURIComponent(data.previousDataset)}`),
      fetch('./research/legacy_catalog.json')
    ]);
    if (!response.ok || payload.dataset !== data.previousDataset || !Number.isSafeInteger(payload.totalVotes) || !METHODS.every(m => Number.isSafeInteger(payload.methods?.[m]) && payload.methods[m] >= 0) || METHODS.reduce((n,m) => n + payload.methods[m],0) !== payload.totalVotes || !catalogResponse.ok) throw new Error('stats');
    const catalog = await catalogResponse.json();
    target.replaceChildren(el('p', 'section-description', `Всего голосов: ${payload.totalVotes}. Эти голоса не входят в текущие итоги.`));
    for (const method of METHODS) {
      const row = el('div', 'stat-row'); const bar = el('div', 'stat-bar'); const fill = el('div');
      fill.style.width = `${percentage(payload.methods[method], payload.totalVotes)}%`; bar.append(fill);
      row.append(el('span', '', previousLabels[method]), bar, el('span', 'stat-percent', `${percentage(payload.methods[method], payload.totalVotes)}%`)); target.append(row);
    }
    let legacy = [];
    try { legacy = JSON.parse(localStorage.getItem(LEGACY_STORAGE) || '[]'); } catch {}
    const entry = Array.isArray(legacy) ? legacy.find(item => item.dataset === data.previousDataset && item.choices) : null;
    if (entry && catalog[entry.dataset]) {
      const counts = Object.fromEntries(METHODS.map(method => [method, 0]));
      for (const [id, choice] of Object.entries(entry.choices)) {
        const method = catalog[entry.dataset]?.[id]?.[choice?.candidateId];
        if (METHODS.includes(method)) counts[method]++;
      }
      const total = Object.values(counts).reduce((a,b) => a+b,0);
      if (total) target.append(el('p', 'section-description', `Твои прежние выборы (${total}): ${METHODS.map(m => `${previousLabels[m]} — ${counts[m]}`).join('; ')}.`));
    }
  } catch { target.replaceChildren(el('p', 'empty-stats', 'Не удалось загрузить результаты предыдущей подборки. Попробуй обновить страницу.')); }
}
function showDialog(kind) {
  const node = $('dialog-content'); node.replaceChildren();
  if (kind === 'method') {
    node.append(el('h2', '', 'Тексты дерутся. Лейблы молчат.'), el('p', '', 'В каждом раунде один оригинал и четыре русских перевода: исторический опубликованный и три варианта AI. Авторы скрыты до выбора. Порядок текстов и карточек перемешан и сохраняется в браузере.'));
    node.append(el('h3', '', 'Что именно сравниваем'), el('p', '', 'В базе 40 фрагментов трёх произведений. Каждый браузер получает 20 фрагментов. Три варианта AI: короткий запрос, запрос с навыком и новый перевод с модельной редактурой по оригиналу. Для редактуры модель учитывала контекст рассказов; независимой человеческой проверки не было. В десяти новых фрагментах все варианты AI созданы в общем контексте, где был доступен исторический перевод; это неконтролируемое сравнение.'));
    node.append(el('h3', '', 'Это пилот читательских предпочтений'), el('p', '', 'Опубликованные переводы исторические, в современной орфографии цифрового источника. Эпоха, узнаваемость, длина и твой вкус влияют на выбор. Голоса не доказывают превосходство модели или навыка. Атрибуция скрыта в интерфейсе до выбора, но доступна в исходниках.'));
    node.append(el('h3', '', 'Откуда опубликованные тексты'), el('p', '', 'Эдгар По — перевод Константина Бальмонта, издание 1913 года. Оскар Уайльд — перевод Михаила Ликиардопуло, публикация 1911 года. Оригиналы и эти переводы находятся в общественном достоянии в юрисдикциях со сроком «жизнь автора + 70 лет». Цифровые источники и точная атрибуция открываются после выбора.'));
    node.append(safeLink('Методика, источники и условия публикации ↗', './CONTENT.md'), el('p', '', 'Цель простая: сначала услышать текст, потом прочитать бейдж. Можно предпочесть любой вариант. Можно вообще не продолжать.'));
  } else {
    node.append(el('h2', '', 'Про данные. Без тумана.'), el('p', '', 'В браузере остаются случайный идентификатор, порядок вариантов и твои выборы, включая сохранённые выборы предыдущей подборки. Сервер хранит хеш идентификатора, выбранный вариант, версию подборки, случайный ID голоса и время. Имя и почту не спрашиваем. Сырые IP-адреса в нашу базу не записываем.'));
    node.append(el('p', '', 'Для защиты от частого голосования сервер использует суточный HMAC-хеш IP. Его срок — 48 часов; просроченные записи очищаются при следующем запросе записи. Cloudflare обрабатывает сетевые данные при обслуживании запросов. Общий счётчик показывает только суммы, без списка участников.'));
    node.append(el('p', '', 'Один браузер — один голос за каждый фрагмент этой версии. Это не защита от человека с несколькими устройствами. Сброс или потеря идентификатора мешает связать прежние голоса с этим браузером и удалить их отсюда.'));
    const remove = el('button', 'danger-button', eraseBusy ? 'Удаляем…' : 'Удалить мои голоса и локальный прогресс'); remove.disabled = eraseBusy || !data; remove.addEventListener('click', erase); node.append(remove);
  }
  if (!$('info-dialog').open) $('info-dialog').showModal();
}
async function erase() {
  if (eraseBusy) return;
  eraseBusy = true; showDialog('privacy');
  try {
    await Promise.allSettled([...inFlight.values()]);
    const legacy = JSON.parse(localStorage.getItem(LEGACY_STORAGE) || '[]');
    for (const entry of [...legacy, { dataset: data.version, participantId: state.participantId }]) {
      const { response, payload } = await api('/votes', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ dataset: entry.dataset, participantId: entry.participantId }) });
      if (!response.ok || payload.dataset !== entry.dataset || !Number.isInteger(payload.deletedVotes) || payload.deletedVotes < 0) throw new Error('delete');
    }
    localStorage.removeItem(LEGACY_STORAGE);
    state = createState(data); persist(); updateStart(); $('info-dialog').close(); show('home'); toast('Серверные голоса удалены. Локальный прогресс сброшен.');
  } catch { toast('Сервер не подтвердил удаление. Идентификатор и прогресс сохранены — можно повторить.'); }
  finally { eraseBusy = false; if ($('info-dialog').open) showDialog('privacy'); }
}

$('start-button').addEventListener('click', start);
$('home-results-button').addEventListener('click', () => show('results'));
$('round-results-button').addEventListener('click', () => show('results'));
$('home-button').addEventListener('click', () => show('home'));
document.querySelectorAll('a[href="#"]').forEach(a => a.addEventListener('click', event => { event.preventDefault(); if (data) show('home'); }));
$('profile-button').addEventListener('click', () => show('results'));
$('next-button').addEventListener('click', next);
$('continue-button').addEventListener('click', () => answered() === state.order.length ? (state.index = 0, show('arena')) : start());
for (const id of ['method-button', 'footer-method']) $(id).addEventListener('click', () => showDialog('method'));
for (const id of ['privacy-button', 'footer-privacy']) $(id).addEventListener('click', () => showDialog('privacy'));
$('close-dialog').addEventListener('click', () => $('info-dialog').close());
$('info-dialog').addEventListener('click', e => { if (e.target === $('info-dialog')) { const r = e.target.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) e.target.close(); } });
$('refresh-stats').addEventListener('click', () => { renderWorld(); renderPreviousWorld(); });
$('share-button').addEventListener('click', async () => { const c = personalCounts(state, data); const message = `Мой вкус в «Без лица»: AI + навыки ${c.skilled}, опубликованный ${c.published}, AI короткий запрос ${c.baseline}, AI с редактурой ${c.reviewed}. Выбирай вслепую: ${location.href.split('#')[0]}`; try { await navigator.clipboard.writeText(message); toast('Результат скопирован. Пускай друзья тоже снимут погоны.'); } catch { toast('Буфер обмена недоступен. Ссылку на сайт можно скопировать из адресной строки.'); } });

async function init() {
  try {
    const responses = await Promise.all([fetch('./data.json'), fetch('./config.json')]); if (responses.some(r => !r.ok)) throw new Error('load');
    [data, config] = await Promise.all(responses.map(r => r.json()));
    if (data.rounds?.length < 30 || data.cohortSize !== 20 || data.rounds.some(r => r.candidates?.length !== METHODS.length)) throw new Error('dataset');
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE));
      if (saved?.version && saved.version !== data.version && /^[a-f0-9-]{36}$/i.test(saved.participantId || '')) {
        const legacy = rememberLegacy(saved, JSON.parse(localStorage.getItem(LEGACY_STORAGE) || '[]'), data.version);
        localStorage.setItem(LEGACY_STORAGE, JSON.stringify(legacy));
      }
      const sameDatasetId = saved?.version === data.version && /^[a-f0-9-]{36}$/i.test(saved.participantId || '') ? saved.participantId : undefined;
      state = validState(saved, data) ? saved : createState(data, sameDatasetId);
    } catch { state = createState(data); }
    persist(); updateStart();
    for (const id of Object.keys(state.choices)) if (state.choices[id].status !== 'saved') submit(id);
  } catch { $('load-error').textContent = 'Не удалось загрузить подборку. Обнови страницу — тексты никуда не убежали.'; $('load-error').hidden = false; $('start-button').textContent = 'Нужна перезагрузка'; }
}
init();
