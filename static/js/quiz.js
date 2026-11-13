const quizText = value => typeof uiText === 'function' ? uiText(value) : value;
/*quiz 기능 구현*/

/* 학습 퀴즈 기능 */

// 보기 번호 표시용 기호 (4지선다)
const CHOICE_MARKS = ['①', '②', '③', '④'];

// 사용자가 고를 수 있는 문제 수 범위
const MIN_COUNT = 1;
const MAX_COUNT = 10;

// 과목별 문제 은행 (키: CURRICULUM의 과목명)
// answer: 정답 보기의 위치 (0~3)
// 문제가 없는 과목은 아직 준비 중으로 처리됨
const QUESTION_BANK = {
    '프로그래밍입문(1)': [
        { question: '화면에 값을 출력할 때 사용하는 파이썬 내장 함수는?',
          choices: ['input()', 'print()', 'echo()', 'show()'], answer: 1,
          explanation: 'print()는 값을 화면에 출력하는 함수입니다. input()은 입력을 받을 때 사용합니다.' },
        { question: '사용자로부터 키보드 입력을 문자열로 받는 함수는?',
          choices: ['input()', 'scan()', 'read()', 'get()'], answer: 0,
          explanation: 'input()은 사용자가 입력한 내용을 항상 문자열(str)로 반환합니다.' },
        { question: 'type(3.14)의 결과로 알맞은 것은?',
          choices: ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'double'>"], answer: 1,
          explanation: '3.14처럼 소수점이 있는 수는 float 자료형입니다. 파이썬에는 double 자료형이 없습니다.' },
        { question: '7 // 2 의 결과는?',
          choices: ['3.5', '4', '3', '2'], answer: 2,
          explanation: '// 는 몫만 구하는 정수 나눗셈 연산자입니다. 7을 2로 나눈 몫은 3입니다.' },
        { question: '7 % 3 의 결과는?',
          choices: ['2', '1', '0', '3'], answer: 1,
          explanation: '% 는 나머지를 구하는 연산자입니다. 7을 3으로 나눈 나머지는 1입니다.' },
        { question: '2 ** 3 의 결과는?',
          choices: ['6', '5', '8', '9'], answer: 2,
          explanation: '** 는 거듭제곱 연산자입니다. 2의 3제곱은 8입니다.' },
        { question: "'3' + '4' 의 결과는?",
          choices: ['7', '34', '12', '오류 발생'], answer: 1,
          explanation: "문자열끼리의 + 는 이어 붙이기입니다. '3'과 '4'를 이어 붙이면 '34'가 됩니다." },
        { question: '변수 이름으로 사용할 수 없는 것은?',
          choices: ['_count', 'total2', '2nd_score', 'myName'], answer: 2,
          explanation: '변수 이름은 숫자로 시작할 수 없습니다. 따라서 2nd_score는 사용할 수 없습니다.' },
        { question: 'len("python")의 결과는?',
          choices: ['5', '6', '7', '오류 발생'], answer: 1,
          explanation: 'len()은 문자열의 글자 수를 반환합니다. "python"은 6글자입니다.' },
        { question: 'a = [1, 2, 3] 일 때 a[1]의 값은?',
          choices: ['1', '2', '3', '오류 발생'], answer: 1,
          explanation: '리스트의 인덱스는 0부터 시작합니다. a[0]=1, a[1]=2, a[2]=3 입니다.' },
        { question: 'a = [1, 2, 3] 에서 a.append(4)를 실행한 후 a의 값은?',
          choices: ['[1, 2, 3]', '[4, 1, 2, 3]', '[1, 2, 3, 4]', '[4]'], answer: 2,
          explanation: 'append()는 리스트의 맨 뒤에 요소를 추가합니다.' },
        { question: 'list(range(3))의 결과는?',
          choices: ['[1, 2, 3]', '[0, 1, 2]', '[0, 1, 2, 3]', '[1, 2]'], answer: 1,
          explanation: 'range(3)은 0부터 시작해 3 미만의 정수를 만듭니다. 즉 0, 1, 2 입니다.' },
        { question: '파이썬에서 참(True)을 나타내는 올바른 표기는?',
          choices: ['true', 'True', 'TRUE', '"True"'], answer: 1,
          explanation: '파이썬의 불리언 값은 첫 글자만 대문자인 True, False 입니다.' },
        { question: '5 == 5.0 의 결과는?',
          choices: ['True', 'False', '오류 발생', 'None'], answer: 0,
          explanation: '== 는 값이 같은지 비교합니다. 정수 5와 실수 5.0은 값이 같으므로 True 입니다.' },
        { question: 'if 문에서 "그렇지 않고 다른 조건이라면"을 나타내는 키워드는?',
          choices: ['else if', 'elseif', 'elif', 'otherwise'], answer: 2,
          explanation: '파이썬에서는 elif 를 사용합니다.' },
        { question: '반복 횟수가 정해져 있을 때 주로 사용하는 반복문은?',
          choices: ['for', 'if', 'def', 'import'], answer: 0,
          explanation: 'for 문은 range() 등과 함께 정해진 횟수만큼 반복할 때 주로 사용합니다.' },
        { question: '반복문 실행 중 반복을 즉시 완전히 빠져나올 때 사용하는 키워드는?',
          choices: ['continue', 'break', 'pass', 'exit'], answer: 1,
          explanation: 'break는 반복문 전체를 종료합니다. continue는 현재 반복만 건너뜁니다.' },
        { question: '반복문 안에서 continue 의 역할은?',
          choices: ['반복문을 완전히 종료한다', '현재 반복의 나머지를 건너뛰고 다음 반복으로 넘어간다', '프로그램을 종료한다', '아무 동작도 하지 않는다'], answer: 1,
          explanation: 'continue는 이번 반복의 남은 코드를 건너뛰고 다음 반복을 진행합니다.' },
        { question: '파이썬에서 함수를 정의할 때 사용하는 키워드는?',
          choices: ['function', 'def', 'func', 'fn'], answer: 1,
          explanation: '함수는 def 키워드로 정의합니다. 예: def add(a, b):' },
        { question: '함수에서 결과 값을 호출한 곳으로 돌려줄 때 사용하는 키워드는?',
          choices: ['give', 'return', 'out', 'back'], answer: 1,
          explanation: 'return은 함수를 종료하며 값을 호출한 곳으로 반환합니다.' },
        { question: '파이썬에서 한 줄 주석을 나타내는 기호는?',
          choices: ['//', '#', '/* */', '--'], answer: 1,
          explanation: '파이썬의 한 줄 주석은 # 기호로 시작합니다.' },
        { question: '튜플(tuple)의 특징으로 알맞은 것은?',
          choices: ['생성 후 요소를 수정할 수 있다', '생성 후 요소를 수정할 수 없다', '키-값 쌍으로 저장한다', '중복된 값을 가질 수 없다'], answer: 1,
          explanation: '튜플은 한 번 만들면 요소를 바꿀 수 없는(immutable) 자료형입니다.' },
        { question: "d = {'a': 1} 일 때 d['a']의 값은?",
          choices: ["'a'", '1', "{'a': 1}", '오류 발생'], answer: 1,
          explanation: '딕셔너리에서 d[키]는 해당 키에 대응하는 값을 반환합니다. 여기서는 1 입니다.' },
        { question: '"Hello"[0]의 결과는?',
          choices: ['e', 'H', 'o', 'l'], answer: 1,
          explanation: '문자열도 인덱스가 0부터 시작합니다. 첫 번째 글자는 "H" 입니다.' },
        { question: 'int("10") + 5 의 결과는?',
          choices: ['15', '105', '"15"', '오류 발생'], answer: 0,
          explanation: 'int("10")은 문자열 "10"을 정수 10으로 바꿉니다. 10 + 5 = 15 입니다.' },
        { question: '3 > 2 and 2 > 5 의 결과는?',
          choices: ['True', 'False', '오류 발생', 'None'], answer: 1,
          explanation: 'and 는 양쪽이 모두 참일 때만 참입니다. 2 > 5 는 거짓이므로 결과는 False 입니다.' },
        { question: 'not True 의 결과는?',
          choices: ['True', 'False', '1', 'None'], answer: 1,
          explanation: 'not 은 참/거짓을 반대로 뒤집습니다. not True 는 False 입니다.' },
        { question: '"a,b,c".split(",")의 결과는?',
          choices: ["['a,b,c']", "['a', 'b', 'c']", "'abc'", "('a', 'b', 'c')"], answer: 1,
          explanation: 'split(",")은 쉼표를 기준으로 문자열을 나눠 리스트로 반환합니다.' },
        { question: '10 / 0 을 실행했을 때 발생하는 오류는?',
          choices: ['ValueError', 'ZeroDivisionError', 'NameError', 'IndexError'], answer: 1,
          explanation: '0으로 나누면 ZeroDivisionError 가 발생합니다.' },
        { question: '정의하지 않은 변수를 사용했을 때 발생하는 오류는?',
          choices: ['NameError', 'KeyError', 'IndexError', 'TypeError'], answer: 0,
          explanation: '정의되지 않은 이름을 사용하면 NameError 가 발생합니다.' }
    ]
};

// 영문 과목명은 한글 과목명과 같은 문제 은행을 사용
QUESTION_BANK['Introduction to Programming 1'] = QUESTION_BANK['프로그래밍입문(1)'];

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

// 화면 전환: 'setup' | 'play' | 'result'
function showSection(sectionName) {
    quizSetup.hidden = sectionName !== 'setup';
    quizPlay.hidden = sectionName !== 'play';
    quizResult.hidden = sectionName !== 'result';
}

// 배열을 무작위로 섞은 새 배열 반환 (Fisher-Yates)
function shuffle(array) {
    const result = array.slice();
    for (let i = result.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        const temp = result[i];
        result[i] = result[j];
        result[j] = temp;
    }
    return result;
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


    if (document.getElementById('quiz-source')?.value === 'ai') {
        if (count > 5) { showMessage(quizText('AI 퀴즈는 1~5문제를 선택해 주세요.')); return; }
        quizBusy = true;
        quizStartBtn.disabled = true;
        const status = document.getElementById('quiz-generation-status');
        status.textContent = quizText('문제와 해설을 생성하고 있습니다. 잠시 기다려 주세요…');
        try {
            const data = await quizRequest('/ai/api/quiz/generate', {
                subject, count, topic: document.getElementById('quiz-topic').value.trim()
            });
            generatedQuizId = data.quiz_id;
            quizQuestions = data.questions;
            userAnswers = new Array(quizQuestions.length).fill(null);
            currentIndex = 0;
            quizSubjectLabel.textContent = '- ' + subject + quizText(' · AI 생성');
            status.textContent = data.usage?.total_tokens ? quizText('이번 생성 사용량: ') + data.usage.total_tokens + quizText('토큰') : quizText('생성 완료');
            renderQuestion();
            showSection('play');
        } catch (error) { showMessage(error.message); status.textContent = quizText('생성하지 못했습니다. 설정을 확인하고 다시 시도하세요.'); }
        finally { quizBusy = false; quizStartBtn.disabled = false; }
        return;
    }
    generatedQuizId = null;

    const bank = QUESTION_BANK[subject];
    if (!bank || bank.length === 0) {
        showMessage("'" + subject + "' 과목의 문제는 아직 준비 중입니다.");
        return;
    }

    // 문제 은행에서 무작위로 선택한 문제 수만큼 출제
    quizQuestions = shuffle(bank).slice(0, Math.min(count, bank.length));
    userAnswers = new Array(quizQuestions.length).fill(null);
    currentIndex = 0;

    quizSubjectLabel.textContent = '- ' + subject;
    renderQuestion();
    showSection('play');
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
function updateQuizSource() {
    const ai = document.getElementById('quiz-source').value === 'ai';
    for (const option of quizCountSelect.options) option.disabled = ai && Number(option.value) > 5;
    if (ai && Number(quizCountSelect.value) > 5) quizCountSelect.value = '5';
    document.getElementById('quiz-topic').disabled = !ai;
}
document.getElementById('quiz-source').addEventListener('change', updateQuizSource);
if (quizCountSelect.options) updateQuizSource();