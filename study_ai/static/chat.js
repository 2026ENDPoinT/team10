const chatText = value => typeof uiText === 'function' ? uiText(value) : value;
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const messages = byId('messages');
  const input = byId('message');
  const error = byId('error');
  const initialWelcome = messages.firstElementChild.cloneNode(true);
  let history = [];
  let quizContext = null;
  let busy = false;
  // 저장용: 화면에 보이는 전체 대화 + 현재 대화의 저장 번호 (새 대화면 null)
  let transcript = [];
  let conversationId = null;
  const savedChats = byId('saved-chats');
  const canSave = savedChats?.dataset.loggedIn === 'true';

  function showError(message) { error.textContent = message; error.hidden = !message; }
  function addMessage(role, text) {
    const article = document.createElement('article');
    article.className = `message ${role}`;
    const speaker = document.createElement('span');
    speaker.className = 'speaker'; speaker.textContent = role === 'user' ? 'YOU' : 'STUDY COMPANION';
    const body = document.createElement('p'); body.textContent = text;
    article.append(speaker, body); messages.append(article);
    messages.scrollTop = messages.scrollHeight;
    return article;
  }
  function resetConversation() {
    history = []; transcript = []; conversationId = null;
    messages.replaceChildren(initialWelcome.cloneNode(true)); showError('');
    markActiveChat();
  }

  /* ---------- 저장된 대화 (최근 3개, 학번 + 비밀번호 단위) ---------- */
  async function recordsRequest(url, payload) {
    const options = payload === undefined ? {headers: {'Accept': 'application/json'}}
      : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)};
    const response = await fetch(url, options);
    let data;
    try { data = await response.json(); } catch (_) { throw new Error(chatText('서버 응답을 확인해 주세요.')); }
    if (!response.ok) throw new Error(data.error || chatText('요청에 실패했습니다.'));
    return data;
  }
  function formatSavedTime(seconds) {
    const date = new Date(seconds * 1000);
    return date.toLocaleString(window.UI_LANGUAGE === 'en' ? 'en-US' : 'ko-KR',
      {month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'});
  }
  function markActiveChat() {
    document.querySelectorAll('#saved-chats-list [data-chat-id]').forEach(item => {
      item.classList.toggle('active', Number(item.dataset.chatId) === conversationId);
    });
  }
  function renderSavedChats(items, limit) {
    const list = byId('saved-chats-list');
    if (!list) return;
    list.replaceChildren();
    items.forEach(item => {
      const li = document.createElement('li'); li.dataset.chatId = item.id;
      const open = document.createElement('button'); open.type = 'button'; open.className = 'saved-chat-open';
      const title = document.createElement('strong'); title.textContent = item.title;
      const meta = document.createElement('span');
      meta.textContent = `${formatSavedTime(item.updated_at)} · ${item.messages.length}${chatText('개 메시지')}`;
      open.append(title, meta);
      open.addEventListener('click', () => loadSavedChat(item));
      const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'saved-chat-delete';
      remove.textContent = '✕'; remove.title = chatText('삭제'); remove.setAttribute('aria-label', chatText('삭제') + ': ' + item.title);
      remove.addEventListener('click', () => deleteSavedChat(item));
      li.append(open, remove); list.append(li);
    });
    byId('saved-chats-empty').hidden = items.length > 0;
    byId('saved-chats-count').textContent = `${items.length} / ${limit || 3}`;
    markActiveChat();
  }
  async function loadSavedChats() {
    if (!canSave) return;
    try { const data = await recordsRequest('/api/conversations'); renderSavedChats(data.items, data.limit); }
    catch (err) { showError(err.message); }
  }
  async function saveCurrentChat() {
    if (!canSave || !transcript.length) return;
    try {
      const data = await recordsRequest('/api/conversations', {id: conversationId, messages: transcript.slice(-60)});
      conversationId = data.id; renderSavedChats(data.items, data.limit);
    } catch (err) { showError(chatText('대화를 저장하지 못했습니다: ') + err.message); }
  }
  function loadSavedChat(item) {
    if (busy) return;
    resetConversation();
    item.messages.forEach(m => addMessage(m.role, m.content));
    transcript = item.messages.map(m => ({role: m.role, content: m.content}));
    // 이어서 질문할 때 AI 에게는 최근 대화만 전달 (서버 제한: 12개, 30000자)
    history = transcript.slice(-12);
    while (history.reduce((total, m) => total + m.content.length, 0) > 30000) history.splice(0, 2);
    conversationId = item.id; markActiveChat();
    input.focus();
  }
  async function deleteSavedChat(item) {
    if (busy || !window.confirm(chatText('이 대화를 삭제할까요?'))) return;
    try {
      const data = await recordsRequest(`/api/conversations/${item.id}/delete`, {});
      if (conversationId === item.id) conversationId = null;   // 화면의 대화는 그대로, 다음 답변부터 새 대화로 저장
      renderSavedChats(data.items, data.limit);
    } catch (err) { showError(err.message); }
  }
  function addVideoResources(article, videos, topic) {
    if (!videos || (!videos.search_url && !videos.items?.length)) return;
    const section = document.createElement('section'); section.className = 'video-resources';
    const heading = document.createElement('h3'); heading.textContent = topic ? `Video lessons · ${topic}` : 'Video lessons';
    section.append(heading);
    function linkToYouTube(url, label) {
      try {
        const parsed = new URL(url);
        if (parsed.protocol !== 'https:' || parsed.hostname !== 'www.youtube.com' ||
            !['/watch', '/results'].includes(parsed.pathname)) return null;
        const link = document.createElement('a'); link.href = parsed.href;
        link.textContent = label; link.target = '_blank'; link.rel = 'noopener noreferrer';
        return link;
      } catch (_) { return null; }
    }
    for (const video of videos.items || []) {
      const link = linkToYouTube(video.url, video.title);
      if (!link) continue;
      const card = document.createElement('div'); card.className = 'video-card';
      const channel = document.createElement('span'); channel.textContent = video.channel;
      card.append(link, channel); section.append(card);
    }
    if (videos.search_url) {
      const search = linkToYouTube(videos.search_url, chatText('유튜브에서 관련 강의 찾기 ↗'));
      if (search) section.append(search);
    }
    if (videos.notice) {
      const notice = document.createElement('p'); notice.className = 'resource-note';
      notice.textContent = videos.notice; section.append(notice);
    }
    article.append(section); messages.scrollTop = messages.scrollHeight;
  }
  function setContext(context) {
    quizContext = context;
    resetConversation();
    const questions = context?.questions || [];
    byId('context-count').textContent = questions.length;
    byId('context-summary').textContent = context ? `Attached subject: ${context.subject || 'General study'}` : 'No quiz question attached. General study chat is ready.';
    byId('clear-context').hidden = !context;
    byId('context-list').replaceChildren();
    questions.forEach(q => {
      const li = document.createElement('li'); li.textContent = q.question;
      byId('context-list').append(li);
    });
    input.value = context ? chatText('이 퀴즈 결과를 바탕으로 잘한 부분과 복습할 부분을 근거와 함께 설명해 주세요.') : '';
  }
  byId('sample').addEventListener('click', () => setContext({
    subject: 'Introduction to Programming 1 (sample)',
    questions: [{question: '7 // 2 의 결과는?', choices: ['3.5', '4', '3', '2'], answer: 2, selected_answer: 0,
      explanation: '// 는 몫만 구하는 정수 나눗셈 연산자입니다. 7을 2로 나눈 몫은 3입니다.'}]
  }));
  byId('clear-context').addEventListener('click', () => setContext(null));
  byId('new-chat').addEventListener('click', () => { resetConversation(); input.value = ''; input.focus(); });
  input.addEventListener('keydown', event => {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      event.preventDefault(); byId('chat-form').requestSubmit();
    }
  });
  byId('chat-form').addEventListener('submit', async event => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message || busy) return;
    busy = true; showError('');
    const controls = ['send', 'sample', 'clear-context', 'new-chat', 'teaching-mode', 'language', 'level', 'video-duration'];
    controls.forEach(id => { byId(id).disabled = true; }); input.disabled = true;
    byId('status').textContent = chatText('답변을 준비하고 있어요…');
    const pending = addMessage('user', message);
    const recent = history.slice(-12);
    while (recent.reduce((total, item) => total + item.content.length, 0) > 30000) recent.splice(0, 2);
    try {
      const response = await fetch(document.querySelector('main').dataset.endpoint, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message, history: recent, quiz_context: quizContext, mode: byId('teaching-mode').value,
          preferences: {language: byId('language').value, level: byId('level').value, video_duration: byId('video-duration').value}})
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Could not send your question.');
      if (typeof result.reply !== 'string') throw new Error('The server returned an invalid reply.');
      const answer = addMessage('assistant', result.reply);
      addVideoResources(answer, result.videos, result.study_topic);
      // Demo fixture text must not become conversation context for a real model.
      if (result.mode !== 'demo') history.push({role: 'user', content: message}, {role: 'assistant', content: result.reply});
      transcript.push({role: 'user', content: message}, {role: 'assistant', content: result.reply});
      input.value = '';
      saveCurrentChat();   // 답변을 받을 때마다 자동 저장
    } catch (err) {
      pending.remove(); showError(err.message || 'Connection failed. Check that the server is running.');
    } finally {
      busy = false; controls.forEach(id => { byId(id).disabled = false; }); input.disabled = false;
      byId('status').textContent = chatText('Ctrl + Enter로 보내기'); input.focus();
    }
  });
  loadSavedChats();
  // After merging, the existing quiz sends context on the SAME origin using the bridge.
  try {
    const raw = sessionStorage.getItem('team10.studyQuizContext');
    if (raw && !document.getElementById('assignment-plan-context')) {
      sessionStorage.removeItem('team10.studyQuizContext');
      const context = JSON.parse(raw);
      if (!context || typeof context.subject !== 'string' || !Array.isArray(context.questions) ||
          !context.questions.length || context.questions.length > 10 ||
          !context.questions.every(q => q && typeof q.question === 'string')) throw new Error('Invalid quiz context');
      setContext(context);
    }
  } catch (_) { quizContext = null; showError('The quiz context could not be loaded. Return to the quiz and try again.'); }
  const planElement = document.getElementById('assignment-plan-context');
  if (planElement) {
    const plan = JSON.parse(planElement.textContent);
    quizContext = null;
    const prompt = window.UI_LANGUAGE === 'en'
      ? 'Help me plan this assignment. Ask how much time I can spend today, then suggest realistic steps based on the deadline and unfinished tasks. Do not claim to have saved changes or submitted the assignment. Assignment data:\n'
      : '이 과제를 함께 계획해 주세요. 오늘 사용할 수 있는 시간을 먼저 물어보고, 마감과 미완료 할 일을 바탕으로 현실적인 순서를 제안해 주세요. 과제를 저장하거나 제출했다고 말하지 마세요. 과제 정보:\n';
    input.value = prompt + JSON.stringify(plan, null, 2);
    input.focus();
  }
})();
