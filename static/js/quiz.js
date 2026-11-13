const quizText = value => typeof uiText === 'function' ? uiText(value) : value;
/*quiz 기능 구현*/

/* 학습 퀴즈 기능 */

// 보기 번호 표시용 기호 (4지선다)
const CHOICE_MARKS = ['①', '②', '③', '④'];

// 사용자가 고를 수 있는 문제 수 범위 (AI 생성 문제만 사용: 1~5문제)
const MIN_COUNT = 1;
const MAX_COUNT = 5;

// 퀴즈 진행 상태
let quizQuestions = [];   // 이번 퀴즈에 출제된 문제 목록
let userAnswers = [];     // 문제별 선택한 보기 (선택 안 함: null, 선택: 0~3)

let generatedQuizId = null;
let quizBusy = false;
let currentIndex = 0;     // 현재 풀고 있는 문제 위치

// 화면 요소
const quizMessage = document.getElementById('quiz-message');
const quizSetup = document.getElementById('quiz-setup');
const quizPlay = document.getElementById('quiz-play');
const quizResult = document.getElementById('quiz-result');

const quizSubjectSelect = document.getElementById('quiz-subject');
const quizCountSelect = document.getElementById('quiz-count');
const quizStartBtn = document.getElementById('quiz-start-btn');

const quizSubjectLabel = document.getElementById('quiz-subject-label');
const quizProgressText = document.getElementById('quiz-progress-text');
const quizProgressFill = document.getElementById('quiz-progress-fill');
const quizQuestion = document.getElementById('quiz-question');
const quizChoices = document.getElementById('quiz-choices');
const quizPrevBtn = document.getElementById('quiz-prev-btn');
const quizNextBtn = document.getElementById('quiz-next-btn');

const quizResultScore = document.getElementById('quiz-result-score');
const quizResultDetail = document.getElementById('quiz-result-detail');
const quizReviewList = document.getElementById('quiz-review-list');
const quizRetryBtn = document.getElementById('quiz-retry-btn');

// 오류 메시지 표시 / 숨김
function showMessage(text) {
    quizMessage.innerHTML = '';
    const li = document.createElement('li');
    li.className = 'error';
    li.textContent = text;
    quizMessage.appendChild(li);
    quizMessage.hidden = false;
}

function clearMessage() {
    quizMessage.innerHTML = '';
    quizMessage.hidden = true;
}

// 저장된 오답 영역 (quiz.html #wrong-notes)
const wrongNotes = document.getElementById('wrong-notes');

// 화면 전환: 'setup' | 'play' | 'result'
function showSection(sectionName) {
    quizSetup.hidden = sectionName !== 'setup';
    wrongNotes.hidden = sectionName !== 'setup';   // 저장된 오답은 설정 화면에서만 표시
    quizPlay.hidden = sectionName !== 'play';
    quizResult.hidden = sectionName !== 'result';
}

// 퀴즈 시작

async function startQuiz() {
    if (quizBusy) return;
    clearMessage();

    const subject = quizSubjectSelect.value;
    if (!subject) {
        showMessage(quizText('과목을 선택해주세요.'));
        return;
    }

    const count = Number(quizCountSelect.value);
    if (!Number.isInteger(count) || count < MIN_COUNT || count > MAX_COUNT) {
        showMessage(quizText('문제 수를 ') + MIN_COUNT + '~' + MAX_COUNT + quizText(' 사이에서 선택해주세요.'));
        return;
    }


    // 학습 주제: 공백을 제외하고 한 글자 이상 필수
    const topicInput = document.getElementById('quiz-topic');
    const topic = topicInput.value.trim();
    if (topic.length < 1) {
        showMessage(quizText('학습 주제를 한 글자 이상 입력해 주세요.'));
        if (typeof topicInput.focus === 'function') topicInput.focus();
        return;
    }

    // AI 문제 생성 (기존 문제은행은 삭제됨)
    quizBusy = true;
    quizStartBtn.disabled = true;
    const status = document.getElementById('quiz-generation-status');
    status.textContent = quizText('문제와 해설을 생성하고 있습니다. 잠시 기다려 주세요…');
    try {
        const data = await quizRequest('/ai/api/quiz/generate', {
            subject, count, topic
        });
        generatedQuizId = data.quiz_id;
        quizQuestions = data.questions;
        userAnswers = new Array(quizQuestions.length).fill(null);
        currentIndex = 0;
        quizSubjectLabel.textContent = subject + quizText(' · AI 생성');
        status.textContent = data.usage?.total_tokens ? quizText('이번 생성 사용량: ') + data.usage.total_tokens + quizText('토큰') : quizText('생성 완료');
        renderQuestion();
        showSection('play');
    } catch (error) { showMessage(error.message); status.textContent = quizText('생성하지 못했습니다. 설정을 확인하고 다시 시도하세요.'); }
    finally { quizBusy = false; quizStartBtn.disabled = false; }
}

// 현재 문제 화면 그리기
function renderQuestion() {
    const q = quizQuestions[currentIndex];
    const total = quizQuestions.length;

    quizProgressText.textContent = quizText('문제 ') + (currentIndex + 1) + ' / ' + total;
    quizProgressFill.style.width = ((currentIndex + 1) / total * 100) + '%';
    quizQuestion.textContent = 'Q' + (currentIndex + 1) + '. ' + q.question;

    const labels = quizChoices.querySelectorAll('label');
    labels.forEach(function (label, i) {
        label.querySelector('span').textContent = CHOICE_MARKS[i] + ' ' + q.choices[i];
        label.querySelector('input').checked = (userAnswers[currentIndex] === i);
    });

    // 첫 문제에서는 quizText('이전') 숨김, 마지막 문제에서는 quizText('다음') → quizText('결과 보기')
    quizPrevBtn.style.visibility = (currentIndex === 0) ? 'hidden' : 'visible';
    quizNextBtn.textContent = (currentIndex === total - 1) ? quizText('결과 보기') : quizText('다음');
}

// 보기 선택 / 해제: 이미 선택된 보기를 다시 누르면 선택 해제
function handleChoiceClick(event) {
    const input = event.target;
    if (input.tagName !== 'INPUT') {
        return;
    }

    const value = Number(input.value);
    if (userAnswers[currentIndex] === value) {
        userAnswers[currentIndex] = null;
        input.checked = false;
    } else {
        userAnswers[currentIndex] = value;
    }
}

// 이전 / 다음 문제 이동
function goPrev() {
    if (currentIndex > 0) {
        currentIndex--;
        renderQuestion();
    }
}


async function goNext() {
    if (quizBusy) return;
    if (currentIndex < quizQuestions.length - 1) {
        currentIndex++;
        renderQuestion();
    } else {
        showResult();
        if (generatedQuizId) {
            quizBusy = true;
            quizNextBtn.disabled = true;
            try {
                const data = await quizRequest('/ai/api/quiz/grade', {quiz_id: generatedQuizId, answers: userAnswers});
                quizQuestions = data.questions;
                clearMessage();
                showResult();
                if (data.wrong_answers_saved) loadWrongNotes();   // 오답 노트 새로고침
            } catch (error) { showMessage(error.message); }
            finally { quizBusy = false; quizNextBtn.disabled = false; }
        } else { showResult(); }
    }
}

// 결과 화면에 들어갈 텍스트 한 줄 만들기 (textContent 사용)
function createReviewLine(label, text) {
    const p = document.createElement('p');
    p.className = 'quiz-review-line';
    const strong = document.createElement('strong');
    strong.textContent = label + ' ';
    p.appendChild(strong);
    p.appendChild(document.createTextNode(text));
    return p;
}

// 문제 한 개의 결과 카드 만들기 (맞음: O / 틀림: X + 해설)
function buildReviewItem(index) {
    const q = quizQuestions[index];
    const mine = userAnswers[index];
    const isCorrect = (mine === q.answer);

    const item = document.createElement('div');
    item.className = 'quiz-review-item ' + (isCorrect ? 'correct' : 'wrong');

    // 머리글: O / X 표시 + 문제
    const head = document.createElement('div');
    head.className = 'quiz-review-head';

    const mark = document.createElement('span');
    mark.className = 'quiz-mark';
    mark.textContent = isCorrect ? 'O' : 'X';
    head.appendChild(mark);

    const title = document.createElement('strong');
    title.textContent = 'Q' + (index + 1) + '. ' + q.question;
    head.appendChild(title);
    item.appendChild(head);

    // 내 답 / 정답
    const myText = (mine === null) ? quizText('선택 안 함') : CHOICE_MARKS[mine] + ' ' + q.choices[mine];
    const answerText = CHOICE_MARKS[q.answer] + ' ' + q.choices[q.answer];

    item.appendChild(createReviewLine(quizText('내 답:'), myText));

    if (!isCorrect || generatedQuizId) {
        item.appendChild(createReviewLine(quizText('정답:'), answerText));

        // 틀린 문제에만 해설 표시
        const explain = document.createElement('div');
        explain.className = 'quiz-review-explain';
        explain.textContent = quizText('💡 해설: ') + q.explanation;
        item.appendChild(explain);
    }


    const helpButton = document.createElement('button');
    helpButton.type = 'button';
    helpButton.className = 'btn-primary';
    helpButton.textContent = quizText('AI에게 이 문제 질문하기');
    helpButton.addEventListener('click', function () {
        try {
            const context = StudyQuizBridge.buildContext(
                quizSubjectSelect.value, [q], [mine], false
            );
            StudyQuizBridge.openTutor(context);
        } catch (error) {
            showMessage(error.message);
        }
    });
    item.appendChild(helpButton);
    return item;
}

// 결과 화면 그리기: 출제된 모든 문제를 순서대로 표시
function showResult() {
    const total = quizQuestions.length;
    let correctCount = 0;

    quizReviewList.innerHTML = '';

    quizQuestions.forEach(function (q, i) {
        if (userAnswers[i] === q.answer) {
            correctCount++;
        }
        quizReviewList.appendChild(buildReviewItem(i));
    });

    quizResultScore.textContent = correctCount + ' / ' + total;
    quizResultDetail.textContent = Math.round(correctCount / total * 100);

    showSection('result');
}

// 다시 풀기: 설정 화면으로 돌아감 (다시 시작하면 문제가 새로 무작위 출제됨)
function retryQuiz() {
    clearMessage();
    userAnswers = new Array(quizQuestions.length).fill(null);
    currentIndex = 0;
    renderQuestion();
    showSection('play');
}

// 이벤트 연결
quizStartBtn.addEventListener('click', startQuiz);
quizChoices.addEventListener('click', handleChoiceClick);
quizPrevBtn.addEventListener('click', goPrev);
quizNextBtn.addEventListener('click', goNext);

quizRetryBtn.addEventListener('click', retryQuiz);

document.getElementById('quiz-ai-review-btn').addEventListener('click', function () {
    try {
        const context = StudyQuizBridge.buildContext(
            quizSubjectSelect.value, quizQuestions, userAnswers
        );
        if (!StudyQuizBridge.openTutor(context)) {
            showMessage(quizText('모두 정답입니다! 개별 문제의 AI 질문 버튼을 이용해 보세요.'));
        }
    } catch (error) {
        showMessage(error.message);
    }
});

// 전체 결과를 전달해야 정답과 오답을 함께 근거로 삼을 수 있습니다.
document.getElementById('quiz-ai-analysis-btn').addEventListener('click', function () {
    try {
        StudyQuizBridge.openTutor(StudyQuizBridge.buildContext(
            quizSubjectSelect.value, quizQuestions, userAnswers, false
        ));
    } catch (error) { showMessage(error.message); }
});


async function quizRequest(url, payload) {
    const response = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
    let data;
    try { data = await response.json(); } catch (_) { throw new Error(quizText('서버 응답을 확인해 주세요.')); }
    if (!response.ok) throw new Error(data.error || quizText('요청에 실패했습니다.'));
    return data;
}

document.getElementById('quiz-new-btn').addEventListener('click', function () {
    clearMessage(); showSection('setup');
});


/* ------------------------------------------------------------------
 * 저장된 오답 (학번 + 비밀번호 단위로 서버 DB 에 최대 10개 저장)
 *  - 저장: 채점할 때 서버가 자동 저장 (/ai/api/quiz/grade)
 *  - 조회: GET /api/wrong-answers   삭제: POST /api/wrong-answers/<id>/delete
 * ------------------------------------------------------------------ */
function noteLine(label, text, className) {
    const p = document.createElement('p');
    p.className = 'note-line' + (className ? ' ' + className : '');
    const strong = document.createElement('strong');
    strong.textContent = label + ' ';
    p.append(strong, document.createTextNode(text));
    return p;
}

function buildWrongNote(item) {
    const details = document.createElement('details');
    details.className = 'note-item';

    const summary = document.createElement('summary');
    const subject = document.createElement('span');
    subject.className = 'chip chip-blue';
    subject.textContent = quizText(item.subject);
    const question = document.createElement('span');
    question.className = 'note-question';
    question.textContent = item.question;
    summary.append(subject, question);
    details.appendChild(summary);

    const body = document.createElement('div');
    body.className = 'note-body';
    const choices = document.createElement('ol');
    choices.className = 'note-choices';
    item.choices.forEach(function (choice, i) {
        const li = document.createElement('li');
        li.textContent = CHOICE_MARKS[i] + ' ' + choice;
        if (i === item.answer) li.className = 'is-answer';
        else if (i === item.selected_answer) li.className = 'is-mine';
        choices.appendChild(li);
    });
    body.appendChild(choices);

    const mine = item.selected_answer === null ? quizText('선택 안 함') : CHOICE_MARKS[item.selected_answer] + ' ' + item.choices[item.selected_answer];
    body.appendChild(noteLine(quizText('내 답:'), mine, 'mine'));
    body.appendChild(noteLine(quizText('정답:'), CHOICE_MARKS[item.answer] + ' ' + item.choices[item.answer], 'answer'));

    const explain = document.createElement('div');
    explain.className = 'quiz-review-explain';
    explain.textContent = quizText('💡 해설: ') + item.explanation;
    body.appendChild(explain);

    const actions = document.createElement('div');
    actions.className = 'btn-row note-actions';
    const ask = document.createElement('button');
    ask.type = 'button';
    ask.className = 'btn-edit';
    ask.textContent = quizText('AI에게 이 문제 질문하기');
    ask.addEventListener('click', function () {
        try {
            StudyQuizBridge.openTutor(StudyQuizBridge.buildContext(item.subject, [item], [item.selected_answer], false));
        } catch (error) { showMessage(error.message); }
    });
    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'btn-delete';
    remove.textContent = quizText('삭제');
    remove.addEventListener('click', async function () {
        if (!window.confirm(quizText('이 오답을 삭제할까요?'))) return;
        try {
            const data = await quizRequest('/api/wrong-answers/' + item.id + '/delete', {});
            renderWrongNotes(data.items, data.limit);
        } catch (error) { showMessage(error.message); }
    });
    actions.append(ask, remove);
    body.appendChild(actions);

    details.appendChild(body);
    return details;
}

function renderWrongNotes(items, limit) {
    const list = document.getElementById('wrong-notes-list');
    if (!list) return;
    list.innerHTML = '';
    items.forEach(function (item) { list.appendChild(buildWrongNote(item)); });
    document.getElementById('wrong-notes-empty').hidden = items.length > 0;
    document.getElementById('wrong-notes-count').textContent = items.length + ' / ' + (limit || 10);
}

async function loadWrongNotes() {
    if (!wrongNotes || !wrongNotes.dataset || wrongNotes.dataset.loggedIn !== 'true') return;
    try {
        const response = await fetch('/api/wrong-answers', {headers: {'Accept': 'application/json'}});
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || quizText('요청에 실패했습니다.'));
        renderWrongNotes(data.items, data.limit);
    } catch (error) { showMessage(error.message); }
}

loadWrongNotes();
