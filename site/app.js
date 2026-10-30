import { METHODS, LEGACY_METHODS, createState, validState, personalCounts, percentage, rememberLegacy, nextUnanswered, countsForGroup } from './logic.mjs';

const $ = id => document.getElementById(id);
const STORAGE = 'blind-translation-v1';
const LABELS = { skilled: 'AI + craft', published: 'Опубликованный перевод', baseline: 'AI: короткий запрос', reviewed: 'AI + craft + QA' };
const REACTIONS = {
  skilled: ['Твой выбор — перевод с craft.', 'Sol работал с английскими оригиналами, подготовленным брифом, глоссарием и навыком художественного перевода. Опубликованный перевод генератору не передавался.'],
  published: ['Ты выбрал опубликованный перевод.', 'Никаких медалей за «правильный» выбор. Просто этот голос тебе ближе. Автор перевода и источник — на карточке.'],
  baseline: ['Твой выбор — короткий запрос.', 'Та же Sol и тот же английский контекст, но короткая просьба перевести и без переводческих skills. Ответ получен в отдельной сессии.'],
  reviewed: ['Твой выбор — craft и QA.', 'Craft-черновик прошёл отдельную QA-сверку и редакторские решения в новых сессиях той же модели. Человеческой редакторской проверки не было.'],
};
let data, config, state, screen = 'home', memoryOnly = false, eraseBusy = false;
const LEGACY_STORAGE = 'blind-translation-legacy-participants-v1';
const inFlight = new Map();
let statsRequest = 0;
let reading = { size: 18, single: false };
try { const saved = JSON.parse(localStorage.getItem('blind-reading-settings')); if (saved && [16,18,20,22,24].includes(saved.size) && typeof saved.single === 'boolean') reading = saved; } catch {}

function el(tag, className, text) { const node = document.createElement(tag); if (className) node.className = className; if (text !== undefined) node.textContent = text; return node; }
function literaryText(node, text) {
  // Plain-text source editions use single asterisks for emphasis; never parse HTML.
  for (const part of text.split(/((?<!\*)\*[^*\n]+\*(?!\*))/g)) {
    node.append(/^\*[^*\n]+\*$/.test(part) ? el('em', '', part.slice(1, -1)) : document.createTextNode(part));
  }
  return node;
}
function safeLink(label, href) { const a = el('a', '', label); a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; return a; }
function persist() { try { localStorage.setItem(STORAGE, JSON.stringify(state)); } catch { memoryOnly = true; } }
function toast(text) { $('toast').textContent = text; $('toast').hidden = false; clearTimeout(toast.timer); toast.timer = setTimeout(() => { $('toast').hidden = true; }, 4000); }
function pluralRu(n, one, few, many) { const last = n % 10, lastTwo = n % 100; return lastTwo >= 11 && lastTwo <= 14 ? many : last === 1 ? one : last >= 2 && last <= 4 ? few : many; }
function answered() { return Object.keys(state.choices).length; }
function pendingCount() { return state.order.filter(id => !state.choices[id] && !(state.skipped || []).includes(id)).length; }
function currentRound() { return data.rounds.find(r => r.id === state.order[state.index]); }
function readingSettings() {
  document.documentElement.style.setProperty('--reading-size', `${reading.size}px`);
  $('candidates').classList.toggle('single-column', reading.single);
  $('text-size').textContent = `${reading.size} px`;
  $('text-smaller').disabled = reading.size <= 16;
  $('text-larger').disabled = reading.size >= 24;
  $('reading-layout').setAttribute('aria-pressed', String(reading.single));
  $('reading-layout').textContent = reading.single ? 'Сравнить в две колонки' : 'В одну колонку';
  try { localStorage.setItem('blind-reading-settings', JSON.stringify(reading)); } catch {}
}
function goToRound(index) {
  if (!Number.isInteger(index) || index < 0 || index >= state.order.length) return;
  state.index = index; persist(); $('source-text').closest('details').open = false; $('round-list').closest('details').open = false; show('arena');
}
function renderRoundList() {
  $('round-list').replaceChildren();
  $('rounds-summary').textContent = `${answered()} выбрано · ${(state.skipped || []).length} пропущено`;
  state.order.forEach((id, index) => {
    const status = state.choices[id] ? 'выбран' : (state.skipped || []).includes(id) ? 'пропущен' : 'без выбора';
    const button = el('button', 'round-number', `${index + 1}${state.choices[id] ? ' ✓' : (state.skipped || []).includes(id) ? ' —' : ''}`);
    button.setAttribute('aria-label', `Раунд ${index + 1}, ${status}`);
    if (index === state.index) button.setAttribute('aria-current', 'step');
    button.addEventListener('click', () => goToRound(index)); $('round-list').append(button);
  });
}
function show(view, focus = true) {
  screen = view;
  if (view === 'results' && !state.resultsViewedAt) { state.resultsViewedAt = Date.now(); persist(); }
  for (const id of ['home', 'arena', 'results']) $(id).hidden = id !== view;
  $('ground-rules').hidden = view !== 'home';
  if (view === 'arena') renderRound();
  if (view === 'results') renderResults();
  if (focus) { window.scrollTo({ top: 0, behavior: 'instant' }); $('main').focus({ preventScroll: true }); }
}
function updateStart() { $('start-button').textContent = !pendingCount() ? 'Открыть итоги ↗' : answered() || (state.skipped || []).length ? `Продолжить · ${answered()} выбрано ↗` : 'Начать вслепую ↗'; $('start-button').disabled = false; $('home-results-button').disabled = false; }
function start() {
  if (!pendingCount()) { show('results'); return; }
  if (state.choices[state.order[state.index]] || (state.skipped || []).includes(state.order[state.index])) state.index = nextUnanswered(state);
  persist(); show('arena');
}
function renderRound() {
  const round = currentRound(); const choice = state.choices[round.id];
  $('progress-text').textContent = `ВЫБРАНО ${answered()} / ${state.order.length}`;
  $('progress-fill').style.width = `${answered() / state.order.length * 100}%`;
  $('round-label').textContent = `РАУНД ${state.index + 1} / ${state.order.length} · ${choice ? 'МАСКИ СНЯТЫ' : 'АВТОРСТВО СКРЫТО'}`;
  $('round-title').textContent = choice ? 'Твой выбор — сохранён.' : 'Какой вариант хочется читать?';
  $('round-title').style.whiteSpace = 'pre-line';
  $('round-tag').textContent = round.tag;
  $('source-text').replaceChildren(); literaryText($('source-text'), round.source);
  $('source-credit').textContent = `${round.author} · ${round.title}`;
  $('source-link').href = round.sourceUrl;
  $('arena-hint').textContent = choice ? 'Сравни впечатление с лейблом. Изменить отправленный выбор нельзя.' : 'Читай в любом порядке. Авторство покажем только после твоего выбора.';
  $('candidates').replaceChildren();
  state.candidateOrders[round.id].forEach((id, index) => {
    const candidate = round.candidates.find(c => c.id === id); const selected = choice?.candidateId === id;
    const card = el('article', `candidate${selected ? ' selected' : ''}`);
    const top = el('div', 'candidate-top'); top.append(el('span', 'candidate-letter', `ВАРИАНТ ${['А', 'Б', 'В', 'Г'][index]}`), el('span', 'candidate-eye')); top.lastChild.setAttribute('aria-hidden', 'true');
    card.append(top, literaryText(el('p', 'candidate-text'), candidate.text));
    if (!choice) {
      const button = el('button', 'vote-button', 'Беру этот ↗'); button.setAttribute('aria-label', `Выбрать вариант ${['А', 'Б', 'В', 'Г'][index]}`); button.addEventListener('click', () => choose(round.id, id)); card.append(button);
    } else {
      const identity = el('details', 'identity');
      identity.append(el('summary', '', `${selected ? '✓ Твой выбор · ' : ''}${LABELS[candidate.method]} · источник`));
      if (selected) identity.append(el('span', 'choice-badge', '✓ ТВОЙ ВЫБОР'));
      identity.append(el('strong', '', LABELS[candidate.method]), el('p', '', candidate.credit), el('p', '', candidate.note));
      if (candidate.sourceUrl) identity.append(safeLink('Источник перевода ↗', candidate.sourceUrl));
      if (candidate.licenseUrl) identity.append(el('p', '', `${round.author} · производные AI-версии отмечены отдельно.`), safeLink(candidate.license, candidate.licenseUrl));
      card.append(identity);
    }
    $('candidates').append(card);
  });
  const panel = $('reveal-panel'); panel.hidden = !choice; panel.replaceChildren();
  if (choice) {
    const candidate = round.candidates.find(c => c.id === choice.candidateId); const [title, text] = REACTIONS[candidate.method];
    const explanation = round.comparisonGroup === 'shared_context' && candidate.method !== 'published' ? 'Этот AI-вариант создан в общем контексте с другими переводами. Сравнивай сами тексты; такой выбор не измеряет отдельный эффект навыка.' : text;
    const body = el('div'); body.append(el('h3', '', title), el('p', '', explanation)); panel.append(el('span', 'reveal-icon', '↗'), body);
  }
  $('next-button').hidden = !choice;
  $('next-button').textContent = pendingCount() ? 'Дальше →' : 'К итогам ↗';
  $('skip-button').hidden = !!choice;
  $('skip-button').textContent = (state.skipped || []).includes(round.id) ? 'Оставить пропущенным →' : 'Пропустить →';
  $('previous-button').disabled = state.index === 0;
  renderRoundList(); readingSettings();
  renderSync(); updateStart();
}
function choose(roundId, candidateId) {
  if (state.choices[roundId] || eraseBusy) return;
  state.skipped = (state.skipped || []).filter(id => id !== roundId);
  state.choices[roundId] = { candidateId, voteId: crypto.randomUUID(), status: 'pending', selectedAt: Date.now(), resultsSeenBeforeChoice: !!state.resultsViewedAt };
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
  const submittedCandidateId = choice.candidateId;
  const task = (async () => {
    try {
      const { response, payload } = await api('/votes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      if (response.status === 409 && payload.error === 'already_voted') {
        const round = data.rounds.find(r => r.id === roundId);
        if (!round.candidates.some(c => c.id === payload.candidateId)) throw new Error('bad_response');
        choice.candidateId = payload.candidateId; choice.status = 'saved';
        toast('У этого браузера уже был голос за этот текст. Показываем сохранённый выбор.');
      } else if (response.ok && payload.dataset === data.version && payload.candidateId === choice.candidateId && payload.fragmentId === roundId && typeof payload.voteId === 'string' && /^[a-f0-9-]{36}$/i.test(payload.voteId)) { choice.status = 'saved'; choice.voteId = payload.voteId; }
      else if (response.status === 410 && payload.error === 'participant_erased') { state = createState(data); persist(); updateStart(); show('home'); toast('Эта сессия уже удалена. Создали новый локальный идентификатор.'); }
      else { choice.status = 'failed'; choice.error = payload.error || 'unavailable'; }
    } catch { choice.status = 'failed'; choice.error = 'network'; }
    finally {
      inFlight.delete(roundId); persist();
      if (screen === 'arena' && currentRound().id === roundId) {
        if (choice.candidateId !== submittedCandidateId) renderRound();
        else renderSync();
      }
      if (screen === 'results') renderResults();
    }
  })();
  inFlight.set(roundId, task); return task;
}
function renderSync() {
  const choice = state.choices[currentRound().id]; const target = $('sync-status'); target.replaceChildren();
  if (!choice) { target.textContent = memoryOnly ? 'Хранилище браузера недоступно: прогресс сохранится только до закрытия страницы.' : (state.skipped || []).includes(currentRound().id) ? 'Фрагмент пропущен без голоса. Можно прочитать его и выбрать вариант сейчас.' : 'Можно пропустить фрагмент без голоса. Прогресс сохранится в этом браузере.'; return; }
  if (choice.status === 'saved') target.textContent = '✓ Голос принят общим счётчиком.';
  else if (choice.status === 'pending') target.textContent = 'Выбор сохранён здесь. Отправляем в общий счётчик…';
  else {
    target.textContent = choice.error === 'rate_limited' ? 'Выбор сохранён здесь. Сегодня с этой сети слишком много запросов — сервер временно не принял голос.' : 'Выбор сохранён здесь. Общий счётчик пока не подтвердил голос.';
    const retry = el('button', 'inline-button', 'Отправить снова'); retry.addEventListener('click', () => submit(currentRound().id)); target.append(' ', retry);
  }
}
function next() {
  const index = nextUnanswered(state);
  if (index < 0) { show('results'); return; }
  goToRound(index);
}
function skip() {
  const id = currentRound().id;
  if (state.choices[id] || eraseBusy) return;
  state.skipped = [...new Set([...(state.skipped || []), id])];
  persist(); updateStart(); next();
}
function renderResults() {
  const n = answered(); const counts = personalCounts(state, data); const highest = Math.max(...Object.values(counts));
  $('results-title').textContent = n ? 'Вот какой\nу тебя вкус.' : 'Итоги\nголосования.';
  $('results-title').style.whiteSpace = 'pre-line';
  $('personal-caption').textContent = n ? `Ты выбрал ${n} ${n === 1 ? 'фрагмент' : n < 5 ? 'фрагмента' : 'фрагментов'} из ${state.order.length}. Это профиль твоих предпочтений в этой подборке. Не экзамен. И не диагноз.` : 'Твоих голосов пока нет. Общие итоги — ниже.';
  const saved = Object.values(state.choices).filter(choice => choice.status === 'saved').length;
  $('personal-caption').textContent += ` Пропущено: ${(state.skipped || []).length}. Сервер подтвердил ${saved} из ${n} голосов.`;
  const afterResults = Object.values(state.choices).filter(choice => choice.resultsSeenBeforeChoice).length;
  if (afterResults) $('personal-caption').textContent += ` После просмотра итогов сделано ${afterResults} ${pluralRu(afterResults, 'выбор', 'выбора', 'выборов')}.`;
  $('personal-result').hidden = !n;
  $('share-button').hidden = !n;
  $('personal-result').replaceChildren();
  for (const method of METHODS) { const card = el('div', `score-card${counts[method] && counts[method] === highest ? ' leading' : ''}`); card.append(el('span', '', 'ТВОЙ ВЫБОР'), el('strong', '', `${counts[method]} / ${n}`), el('p', '', LABELS[method])); $('personal-result').append(card); }
  $('continue-button').textContent = !pendingCount() ? (state.skipped || []).length ? 'Вернуться к пропущенным ↗' : 'Перечитать раунды ↗' : 'Продолжить чтение ↗';
  $('history-list').replaceChildren();
  for (const [index, id] of state.order.entries()) {
    const choice = state.choices[id];
    if (!choice && !(state.skipped || []).includes(id)) continue;
    if (!choice) {
      const row = el('div', 'history-item'); row.append(el('span', '', `РАУНД ${index + 1} · пропущен, голоса нет`));
      const button = el('button', 'text-button', 'Прочитать ↗'); button.addEventListener('click', () => goToRound(index)); row.append(button); $('history-list').append(row); continue;
    }
    const round = data.rounds.find(r => r.id === id); const candidate = round.candidates.find(c => c.id === choice.candidateId);
    const row = el('div', 'history-item'); const copy = el('div'); copy.append(el('span', '', `РАУНД ${index + 1} · ${round.author}`), el('b', '', LABELS[candidate.method]), el('span', '', (choice.status === 'saved' ? 'В общем счётчике' : 'Пока только в этом браузере') + (choice.resultsSeenBeforeChoice ? ' · после просмотра итогов' : '')));
    const button = el('button', 'text-button', 'Перечитать ↗'); button.addEventListener('click', () => { state.index = index; persist(); show('arena'); }); row.append(copy, button); $('history-list').append(row);
  }
  if (!n && !(state.skipped || []).length) $('history-list').append(el('p', 'section-description', 'Пока здесь чистый лист.'));
  renderWorld();
  renderPreviousWorld();
}
async function renderWorld() {
  const target = $('world-stats');
  const requestId = ++statsRequest;
  const group = $('stats-group').value;
  $('stats-context').textContent = 'Классические варианты сохранены из v5; современный рассказ добавлен отдельным новым запуском. Внутри каждого запуска AI-условия получили одинаковый английский контекст. Craft+QA требует больше этапов. Различия между произведениями не измеряют эффект навыков.';
  target.replaceChildren(el('p', 'section-description', 'Считаем голоса…'));
  try {
    const { response, payload } = await api(`/stats?dataset=${encodeURIComponent(data.version)}`);
    if (requestId !== statsRequest) return;
    if (!response.ok || payload.dataset !== data.version || !Number.isSafeInteger(payload.totalVotes) || !Number.isSafeInteger(payload.participantBrowsers)) throw new Error('stats');
    if (!METHODS.every(m => Number.isSafeInteger(payload.methods?.[m]) && payload.methods[m] >= 0) || METHODS.reduce((n,m) => n + payload.methods[m],0) !== payload.totalVotes) throw new Error('stats');
    if (group !== 'all' && (!payload.fragments || Object.keys(payload.fragments).length !== data.rounds.filter(r=>r.votingEligible!==false).length || data.rounds.filter(r=>r.votingEligible!==false).some(r => !Object.hasOwn(payload.fragments,r.id)))) throw new Error('stats');
    const counts = countsForGroup(payload, group, data.rounds);
    const total = METHODS.reduce((n,m) => n + counts[m],0);
    target.replaceChildren();
    const totals = el('div', 'world-counts');
    const metrics = [[total, pluralRu(total, 'голос', 'голоса', 'голосов')]];
    if (group === 'all') metrics.push([payload.participantBrowsers, pluralRu(payload.participantBrowsers, 'браузер', 'браузера', 'браузеров')]);
    for (const [number, text] of metrics) { const item = el('span'); item.append(el('b', '', String(number)), document.createTextNode(text)); totals.append(item); }
    target.append(totals);
    if (!total) { target.append(el('p', 'empty-stats', 'В этой подборке пока нет голосов. Можно начать читать или вернуться позже.')); return; }
    for (const method of METHODS) {
      const row = el('div', 'stat-row'); const bar = el('div', 'stat-bar'); const fill = el('div'); fill.style.width = `${percentage(counts[method], total)}%`; bar.append(fill);
      row.append(el('span', '', LABELS[method]), bar, el('span', 'stat-percent', `${counts[method]} · ${percentage(counts[method], total)}%`)); row.setAttribute('aria-label', `${LABELS[method]}: ${counts[method]} из ${total} голосов`); target.append(row);
    }
  } catch { if (requestId === statsRequest) target.replaceChildren(el('p', 'empty-stats', 'Общий счётчик сейчас не отвечает. Твои локальные выборы на месте. Попробуй «Обновить».')); }
}
async function renderPreviousWorld() {
  const target = $('previous-stats');
  const previousLabels = { skilled: 'AI + навыки (прежний запуск)', published: 'Опубликованный перевод', baseline: 'AI: короткий запрос', reviewed: 'AI + редактура (прежний запуск)' };
  if (!data.previousDataset) { target.replaceChildren(); return; }
  target.replaceChildren(el('p', 'section-description', 'Загружаем прежние голоса…'));
  try {
    const [{ response, payload }, catalogResponse] = await Promise.all([
      api(`/stats?dataset=${encodeURIComponent(data.previousDataset)}`),
      fetch('./research/legacy_catalog.json')
    ]);
    if (!response.ok || payload.dataset !== data.previousDataset || !Number.isSafeInteger(payload.totalVotes) || !LEGACY_METHODS.every(m => Number.isSafeInteger(payload.methods?.[m]) && payload.methods[m] >= 0) || LEGACY_METHODS.reduce((n,m) => n + payload.methods[m],0) !== payload.totalVotes || !catalogResponse.ok) throw new Error('stats');
    const catalog = await catalogResponse.json();
    target.replaceChildren(el('p', 'section-description', `Всего голосов: ${payload.totalVotes}. Эти голоса не входят в текущие итоги.`));
    for (const method of LEGACY_METHODS) {
      const row = el('div', 'stat-row'); const bar = el('div', 'stat-bar'); const fill = el('div');
      fill.style.width = `${percentage(payload.methods[method], payload.totalVotes)}%`; bar.append(fill);
      row.append(el('span', '', previousLabels[method]), bar, el('span', 'stat-percent', `${percentage(payload.methods[method], payload.totalVotes)}%`)); target.append(row);
    }
    let legacy = [];
    try { legacy = JSON.parse(localStorage.getItem(LEGACY_STORAGE) || '[]'); } catch {}
    const entry = Array.isArray(legacy) ? legacy.find(item => item.dataset === data.previousDataset && item.choices) : null;
    if (entry && catalog[entry.dataset]) {
      const counts = Object.fromEntries(LEGACY_METHODS.map(method => [method, 0]));
      for (const [id, choice] of Object.entries(entry.choices)) {
        const method = catalog[entry.dataset]?.[id]?.[choice?.candidateId];
        if (LEGACY_METHODS.includes(method)) counts[method]++;
      }
      const total = Object.values(counts).reduce((a,b) => a+b,0);
      if (total) target.append(el('p', 'section-description', `Твои прежние выборы (${total}): ${LEGACY_METHODS.map(m => `${previousLabels[m]} — ${counts[m]}`).join('; ')}.`));
    }
  } catch { target.replaceChildren(el('p', 'empty-stats', 'Не удалось загрузить результаты предыдущей подборки. Попробуй обновить страницу.')); }
}
function showDialog(kind) {
  const node = $('dialog-content'); node.replaceChildren();
  if (kind === 'method') {
    node.append(el('h2', '', 'Тексты дерутся. Лейблы молчат.'), el('p', '', 'В каждом раунде один оригинал и три русских перевода: опубликованный, короткий AI-запрос и полный craft+QA. Авторы скрыты до выбора. Порядок текстов и карточек перемешан и сохраняется в браузере.'));
    const eligible = data.rounds.filter(r => r.votingEligible !== false).length;
    node.append(el('h3', '', 'Что именно сравниваем'), el('p', '', `В базе ${data.rounds.length} фрагментов; ${eligible} доступны для голосования. Одинаковые простой и полный AI-ответы сохранены в протоколе, но исключены из голосования. Подборка до 20 включает современные отрывки и классику. Короткий запрос работает без skills. Craft использует план, глоссарий и калибровку на четырёх сценах. Craft+QA — тот же черновик после отдельной сверки и редактуры. Каждый этап запущен в новой сессии Sol с одинаковыми настройками. Опубликованные переводы и ответы другого условия генераторам не передавались. Классические ответы сохранены из v5; современный рассказ получил собственный полный запуск.`));
    node.append(el('h3', '', 'Это пилот читательских предпочтений'), el('p', '', 'Эпоха, жанр, узнаваемость, длина и твой вкус влияют на выбор. Один современный рассказ не представляет всю современную литературу. Голоса не доказывают превосходство модели или навыка. Полный цикл требует больше вызовов; в памяти обучения модели могли быть эти произведения. Изоляция запуска не устраняет такое предварительное знание. Атрибуция скрыта в интерфейсе до выбора, но доступна в исходниках.'));
    node.append(el('h3', '', 'Откуда опубликованные тексты'), el('p', '', 'Классика: По в переводе Бальмонта и Уайльд в переводе Ликиардопуло; общественное достояние в юрисдикциях со сроком «жизнь + 70 лет». Современная проза: «Земля сисадминов» Кори Доктороу (2006), перевод Михаила Карпова; оригинал, опубликованный перевод и производные AI-переводы — CC BY-NC-SA 2.5, только некоммерческое использование с атрибуцией и сохранением лицензии. Цифровые источники открываются после выбора.'));
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
$('skip-button').addEventListener('click', skip);
$('previous-button').addEventListener('click', () => goToRound(state.index - 1));
$('text-smaller').addEventListener('click', () => { reading.size = Math.max(16, reading.size - 2); readingSettings(); });
$('text-larger').addEventListener('click', () => { reading.size = Math.min(24, reading.size + 2); readingSettings(); });
$('reading-layout').addEventListener('click', () => { reading.single = !reading.single; readingSettings(); });
$('continue-button').addEventListener('click', () => {
  if (pendingCount()) { start(); return; }
  const skippedIndex = state.order.findIndex(id => (state.skipped || []).includes(id));
  goToRound(skippedIndex < 0 ? 0 : skippedIndex);
});
for (const id of ['method-button', 'footer-method']) $(id).addEventListener('click', () => showDialog('method'));
for (const id of ['privacy-button', 'footer-privacy']) $(id).addEventListener('click', () => showDialog('privacy'));
$('close-dialog').addEventListener('click', () => $('info-dialog').close());
$('info-dialog').addEventListener('click', e => { if (e.target === $('info-dialog')) { const r = e.target.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) e.target.close(); } });
$('refresh-stats').addEventListener('click', () => { renderWorld(); renderPreviousWorld(); });
$('stats-group').addEventListener('change', renderWorld);
$('modern-button').addEventListener('click', () => {
  const indices = state.order.map((id, index) => ({round: data.rounds.find(r => r.id === id), index})).filter(({round}) => round.era === 'contemporary');
  const next = indices.find(({round}) => !state.choices[round.id] && !(state.skipped || []).includes(round.id)) || indices[0];
  if (next) goToRound(next.index);
});
$('share-button').addEventListener('click', async () => { const c = personalCounts(state, data); const message = `Мой вкус в «Без лица»: опубликованный ${c.published}, AI короткий запрос ${c.baseline}, AI + craft + QA ${c.reviewed}. Выбирай вслепую: ${location.href.split('#')[0]}`; try { await navigator.clipboard.writeText(message); toast('Результат скопирован. Пускай друзья тоже снимут погоны.'); } catch { toast('Буфер обмена недоступен. Ссылку на сайт можно скопировать из адресной строки.'); } });

async function init() {
  try {
    const responses = await Promise.all([fetch('./data.json', {cache: 'no-store'}), fetch('./config.json', {cache: 'no-store'})]); if (responses.some(r => !r.ok)) throw new Error('load');
    [data, config] = await Promise.all(responses.map(r => r.json()));
    if (data.rounds?.length < 30 || data.cohortSize !== 20 || data.rounds.some(r => r.candidates?.length !== METHODS.length)) throw new Error('dataset');
    const eligible = data.rounds.filter(r => r.votingEligible !== false);
    $('corpus-summary').textContent = `До 20 раундов из ${eligible.length} оценочных фрагментов. Можно пропускать и остановиться в любой момент.`;
    $('stats-group').replaceChildren(new Option(`Все ${eligible.length} оценочных фрагментов`, 'all'));
    for (const workId of new Set(eligible.map(r => r.workId))) {
      const rows = eligible.filter(r => r.workId === workId);
      $('stats-group').append(new Option(`${rows[0].title.split(' / ').at(-1)} · ${rows.length}`, workId));
    }
    $('modern-button').disabled = !eligible.some(r => r.era === 'contemporary');
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
