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
    history = []; messages.replaceChildren(initialWelcome.cloneNode(true)); showError('');
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
      const search = linkToYouTube(videos.search_url, '유튜브에서 관련 강의 찾기 ↗');
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
    input.value = context ? '이 퀴즈 결과를 바탕으로 잘한 부분과 복습할 부분을 근거와 함께 설명해 주세요.' : '';
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
    byId('status').textContent = '답변을 준비하고 있어요…';
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
      input.value = '';
    } catch (err) {
      pending.remove(); showError(err.message || 'Connection failed. Check that the server is running.');
    } finally {
      busy = false; controls.forEach(id => { byId(id).disabled = false; }); input.disabled = false;
      byId('status').textContent = 'Ctrl + Enter로 보내기'; input.focus();
    }
  });
  // After merging, the existing quiz sends context on the SAME origin using the bridge.
  try {
    const raw = sessionStorage.getItem('team10.studyQuizContext');
    if (raw) {
      sessionStorage.removeItem('team10.studyQuizContext');
      const context = JSON.parse(raw);
      if (!context || typeof context.subject !== 'string' || !Array.isArray(context.questions) ||
          !context.questions.length || context.questions.length > 10 ||
          !context.questions.every(q => q && typeof q.question === 'string')) throw new Error('Invalid quiz context');
      setContext(context);
    }
  } catch (_) { quizContext = null; showError('The quiz context could not be loaded. Return to the quiz and try again.'); }
})();
