/*quiz 기능 구현*/

/* 학습 퀴즈 기능 */

// 보기 번호 표시용 기호 (4지선다)
const CHOICE_MARKS = ['①', '②', '③', '④'];

// 샘플 문제 (과목별·학년별 문제 구성은 추후 구현 예정)
// answer: 정답 보기의 위치 (0~3)
const QUIZ_QUESTIONS = [
    {
        question: 'HTTP 상태 코드 중 "요청한 페이지를 찾을 수 없음"을 뜻하는 것은?',
        choices: ['200', '301', '404', '500'],
        answer: 2,
        explanation: '404는 서버에서 요청한 자원을 찾을 수 없다는 뜻입니다. 200은 성공, 301은 영구 이동, 500은 서버 내부 오류입니다.'
    },
    {
        question: '파이썬에서 리스트의 길이(요소 개수)를 구하는 내장 함수는?',
        choices: ['size()', 'len()', 'count()', 'length()'],
        answer: 1,
        explanation: 'len()은 리스트, 문자열 등의 길이를 반환하는 파이썬 내장 함수입니다.'
    },
    {
        question: '다음 중 관계형 데이터베이스(RDBMS)가 아닌 것은?',
        choices: ['MySQL', 'PostgreSQL', 'SQLite', 'Redis'],
        answer: 3,
        explanation: 'Redis는 키-값 형태의 NoSQL 데이터베이스입니다. 나머지는 관계형 데이터베이스입니다.'
    },
    {
        question: 'SQL에서 테이블의 데이터를 조회할 때 사용하는 명령어는?',
        choices: ['SELECT', 'INSERT', 'UPDATE', 'DELETE'],
        answer: 0,
        explanation: 'SELECT는 조회, INSERT는 추가, UPDATE는 수정, DELETE는 삭제에 사용합니다.'
    },
    {
        question: '이진수 1010을 십진수로 바꾸면?',
        choices: ['8', '9', '10', '12'],
        answer: 2,
        explanation: '1×8 + 0×4 + 1×2 + 0×1 = 10 입니다.'
    },
    {
        question: '4.5 만점 기준에서 성적 등급 A+의 평점은?',
        choices: ['4.0', '4.5', '5.0', '3.5'],
        answer: 1,
        explanation: '이 프로그램은 4.5 만점 기준이며 A+는 4.5, A0는 4.0입니다.'
    },
    {
        question: '3학점 과목 A0(4.0)와 2학점 과목 B0(3.0)을 들었을 때 평점평균은?',
        choices: ['3.2', '3.4', '3.5', '3.6'],
        answer: 3,
        explanation: '(3×4.0 + 2×3.0) ÷ 5 = 18 ÷ 5 = 3.6 입니다.'
    },
    {
        question: 'HTML에서 하이퍼링크를 만들 때 사용하는 태그는?',
        choices: ['<a>', '<link>', '<href>', '<url>'],
        answer: 0,
        explanation: '<a> 태그에 href 속성으로 이동할 주소를 지정합니다.'
    },
    {
        question: '먼저 들어온 데이터가 먼저 나오는(FIFO) 자료구조는?',
        choices: ['스택', '큐', '트리', '그래프'],
        answer: 1,
        explanation: '큐(Queue)는 먼저 들어온 데이터가 먼저 나옵니다. 스택은 나중에 들어온 데이터가 먼저 나옵니다(LIFO).'
    },
    {
        question: '파이썬에서 딕셔너리를 만드는 올바른 문법은?',
        choices: ['[1: 2]', '(1: 2)', '{1: 2}', '<1: 2>'],
        answer: 2,
        explanation: '딕셔너리는 중괄호 {} 안에 "키: 값" 형태로 만듭니다.'
    }
];

// 퀴즈 진행 상태
let quizQuestions = [];   // 이번 퀴즈에 출제된 문제 목록
let userAnswers = [];     // 문제별 선택한 보기 (선택 안 함: null, 선택: 0~3)
let currentIndex = 0;     // 현재 풀고 있는 문제 위치

// 화면 요소
const quizMessage = document.getElementById('quiz-message');
const quizSetup = document.getElementById('quiz-setup');
const quizPlay = document.getElementById('quiz-play');
const quizResult = document.getElementById('quiz-result');

const quizCountSelect = document.getElementById('quiz-count');
const quizStartBtn = document.getElementById('quiz-start-btn');

const quizProgressText = document.getElementById('quiz-progress-text');
const quizProgressFill = document.getElementById('quiz-progress-fill');
const quizQuestion = document.getElementById('quiz-question');
const quizChoices = document.getElementById('quiz-choices');
const quizPrevBtn = document.getElementById('quiz-prev-btn');
const quizNextBtn = document.getElementById('quiz-next-btn');

const quizResultScore = document.getElementById('quiz-result-score');
const quizResultDetail = document.getElementById('quiz-result-detail');
const quizWrongTable = document.getElementById('quiz-wrong-table');
const quizWrongBody = document.getElementById('quiz-wrong-body');
const quizWrongEmpty = document.getElementById('quiz-wrong-empty');
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

// 화면 전환: 'setup' | 'play' | 'result'
function showSection(sectionName) {
    quizSetup.hidden = sectionName !== 'setup';
    quizPlay.hidden = sectionName !== 'play';
    quizResult.hidden = sectionName !== 'result';
}

// 퀴즈 시작
function startQuiz() {
    clearMessage();

    const count = Number(quizCountSelect.value);
    if (count !== 5 && count !== 10) {
        showMessage('문제 수를 선택해주세요.');
        return;
    }

    // 과목 선택은 아직 사용하지 않으므로, 샘플 문제 앞에서부터 선택한 문제 수만큼 출제
    quizQuestions = QUIZ_QUESTIONS.slice(0, count);
    userAnswers = new Array(quizQuestions.length).fill(null);
    currentIndex = 0;

    renderQuestion();
    showSection('play');
}

// 현재 문제 화면 그리기
function renderQuestion() {
    const q = quizQuestions[currentIndex];
    const total = quizQuestions.length;

    quizProgressText.textContent = '문제 ' + (currentIndex + 1) + ' / ' + total;
    quizProgressFill.style.width = ((currentIndex + 1) / total * 100) + '%';
    quizQuestion.textContent = 'Q' + (currentIndex + 1) + '. ' + q.question;

    const labels = quizChoices.querySelectorAll('label');
    labels.forEach(function (label, i) {
        label.querySelector('span').textContent = CHOICE_MARKS[i] + ' ' + q.choices[i];
        label.querySelector('input').checked = (userAnswers[currentIndex] === i);
    });

    // 첫 문제에서는 '이전' 숨김, 마지막 문제에서는 '다음' → '결과 보기'
    quizPrevBtn.style.visibility = (currentIndex === 0) ? 'hidden' : 'visible';
    quizNextBtn.textContent = (currentIndex === total - 1) ? '결과 보기' : '다음';
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

function goNext() {
    if (currentIndex < quizQuestions.length - 1) {
        currentIndex++;
        renderQuestion();
    } else {
        showResult();
    }
}

// 표의 셀 추가 (textContent 사용)
function addCell(row, text) {
    const td = document.createElement('td');
    td.textContent = text;
    row.appendChild(td);
}

// 틀린 문제 한 개를 표에 추가 (문제 행 + 해설 행)
function addWrongRow(index) {
    const q = quizQuestions[index];
    const mine = userAnswers[index];

    const row = document.createElement('tr');
    addCell(row, (index + 1) + '번');
    addCell(row, q.question);
    addCell(row, mine === null ? '선택 안 함' : CHOICE_MARKS[mine] + ' ' + q.choices[mine]);
    addCell(row, CHOICE_MARKS[q.answer] + ' ' + q.choices[q.answer]);

    const toggleCell = document.createElement('td');
    const toggleBtn = document.createElement('button');
    toggleBtn.type = 'button';
    toggleBtn.className = 'btn-edit';
    toggleBtn.textContent = '해설 보기';
    toggleCell.appendChild(toggleBtn);
    row.appendChild(toggleCell);

    const explainRow = document.createElement('tr');
    explainRow.hidden = true;
    const explainCell = document.createElement('td');
    explainCell.colSpan = 5;
    explainCell.style.textAlign = 'left';
    explainCell.style.backgroundColor = '#f1f3f5';
    explainCell.textContent = '💡 해설: ' + q.explanation;
    explainRow.appendChild(explainCell);

    toggleBtn.addEventListener('click', function () {
        explainRow.hidden = !explainRow.hidden;
        toggleBtn.textContent = explainRow.hidden ? '해설 보기' : '해설 닫기';
    });

    quizWrongBody.appendChild(row);
    quizWrongBody.appendChild(explainRow);
}

// 결과 화면 그리기
function showResult() {
    const total = quizQuestions.length;
    let correctCount = 0;

    quizWrongBody.innerHTML = '';

    quizQuestions.forEach(function (q, i) {
        if (userAnswers[i] === q.answer) {
            correctCount++;
        } else {
            addWrongRow(i);   // 틀린 문제 (선택 안 한 문제 포함)
        }
    });

    quizResultScore.textContent = correctCount + ' / ' + total;
    quizResultDetail.textContent = Math.round(correctCount / total * 100);

    const hasWrong = correctCount < total;
    quizWrongTable.hidden = !hasWrong;
    quizWrongEmpty.hidden = hasWrong;

    showSection('result');
}

// 다시 풀기: 설정 화면으로 돌아감
function retryQuiz() {
    clearMessage();
    showSection('setup');
}

// 이벤트 연결
quizStartBtn.addEventListener('click', startQuiz);
quizChoices.addEventListener('click', handleChoiceClick);
quizPrevBtn.addEventListener('click', goPrev);
quizNextBtn.addEventListener('click', goNext);
quizRetryBtn.addEventListener('click', retryQuiz);
