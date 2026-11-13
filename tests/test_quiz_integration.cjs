// Exercises the quiz review button handlers and the AI-only quiz flow (the built-in question bank was removed).
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.join(__dirname, '..');
class Element {
  constructor() { this.children = []; this.listeners = {}; this.style = {}; this.value = ''; }
  appendChild(child) { this.children.push(child); return child; }
  addEventListener(name, handler) { this.listeners[name] = handler; }
}
const elements = new Map();
const get = id => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); };
const stored = new Map();
let destination = '';
const sandbox = {
  document: {getElementById: get, createElement: () => new Element(), createTextNode: text => ({textContent: text})},
  window: {location: {href: 'http://localhost:5002/quiz', origin: 'http://localhost:5002', assign: url => {destination = url;}}},
  sessionStorage: {setItem: (key, value) => stored.set(key, value)}, URL
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(root, 'study_ai/static/quiz-bridge.js'), 'utf8'), sandbox);
sandbox.StudyQuizBridge = sandbox.window.StudyQuizBridge;
vm.runInContext(fs.readFileSync(path.join(root, 'static/js/quiz.js'), 'utf8'), sandbox);
get('quiz-subject').value = '프로그래밍입문(1)';
const sampleQuestions = [
  {question: '화면에 값을 출력할 때 사용하는 파이썬 내장 함수는?', choices: ['input()', 'print()', 'echo()', 'show()'], answer: 1, explanation: 'print()는 값을 화면에 출력하는 함수입니다.'},
  {question: '사용자로부터 키보드 입력을 문자열로 받는 함수는?', choices: ['input()', 'scan()', 'read()', 'get()'], answer: 0, explanation: 'input()은 입력을 문자열로 반환합니다.'},
  {question: '7 // 2 의 결과는?', choices: ['3.5', '4', '3', '2'], answer: 2, explanation: '// 는 몫만 구하는 정수 나눗셈입니다.'}
];
sandbox.sampleQuestions = sampleQuestions;
vm.runInContext(`quizQuestions = sampleQuestions.slice(0, 3); userAnswers = [0, 0, null];`, sandbox);
const wrongItem = vm.runInContext('buildReviewItem(0)', sandbox);
wrongItem.children.at(-1).listeners.click();
assert.equal(destination, 'http://localhost:5002/ai/');
const single = JSON.parse(stored.get('team10.studyQuizContext'));
assert.equal(single.questions.length, 1);
assert.equal(single.questions[0].selected_answer, 0);
assert.equal(single.questions[0].answer, 1);
assert.equal(single.questions[0].choices[1], 'print()');
fs.writeFileSync(path.join(__dirname, 'quiz_context.json'), JSON.stringify(single, null, 2));
get('quiz-ai-review-btn').listeners.click();
const missed = JSON.parse(stored.get('team10.studyQuizContext'));
assert.equal(missed.questions.length, 2);
assert.equal(missed.questions[1].selected_answer, null);
const correctItem = vm.runInContext('buildReviewItem(1)', sandbox);
correctItem.children.at(-1).listeners.click();
assert.equal(JSON.parse(stored.get('team10.studyQuizContext')).questions.length, 1);
vm.runInContext('userAnswers = quizQuestions.map(q => q.answer);', sandbox);
destination = '';
get('quiz-ai-review-btn').listeners.click();
assert.equal(destination, '');
assert.equal(get('quiz-message').hidden, false);
console.log('Actual team quiz checks passed: individual help, missed review, correct answer help, unanswered, perfect score.');

get('quiz-ai-analysis-btn').listeners.click();
assert.equal(JSON.parse(stored.get('team10.studyQuizContext')).questions.length, 3);
console.log('Full-result strength/review handoff passed.');

(async () => {
  get('quiz-count').value = '1';

  // 학습 주제가 비어 있거나 공백뿐이면 서버를 호출하지 않음
  let blockedCalls = 0;
  sandbox.fetch = async () => { blockedCalls++; return {ok: true, json: async () => ({})}; };
  for (const empty of ['', '   ']) {
    get('quiz-topic').value = empty;
    await vm.runInContext('startQuiz()', sandbox);
    assert.equal(get('quiz-message').hidden, false);
  }
  assert.equal(blockedCalls, 0);

  // 문제 수는 1~5만 허용
  get('quiz-topic').value = '입출력';
  get('quiz-count').value = '6';
  await vm.runInContext('startQuiz()', sandbox);
  assert.equal(blockedCalls, 0);
  get('quiz-count').value = '1';
  console.log('Required topic and 1~5 question limit passed.');

  get('quiz-choices').querySelectorAll = () => [];
  let calls = 0;
  const question = {question: '입력 함수는?', choices: ['input()', 'print()', 'len()', 'int()'], answer: 0, explanation: 'input()은 입력을 받습니다.'};
  sandbox.fetch = async (url, options) => {
    calls++;
    if (url.endsWith('generate')) return {ok: true, json: async () => ({quiz_id: 'test', questions: [{question: question.question, choices: question.choices}]})};
    assert.equal(JSON.parse(options.body).answers[0], 1);
    return {ok: true, json: async () => ({questions: [question], correct: 0})};
  };
  await vm.runInContext('startQuiz()', sandbox);
  assert.equal(get('quiz-play').hidden, false);
  assert.equal(vm.runInContext('quizQuestions[0].answer', sandbox), undefined);
  vm.runInContext('userAnswers = [1]', sandbox);
  await vm.runInContext('goNext()', sandbox);
  assert.equal(get('quiz-result-score').textContent, '0 / 1');
  get('quiz-ai-review-btn').listeners.click();
  assert.equal(JSON.parse(stored.get('team10.studyQuizContext')).questions[0].explanation, question.explanation);
  vm.runInContext('retryQuiz()', sandbox);
  assert.equal(calls, 2);
  assert.equal(get('quiz-play').hidden, false);
  sandbox.fetch = async () => ({ok:false, json:async()=>({error:'사용 한도'})});
  await vm.runInContext('startQuiz()', sandbox);
  assert.equal(get('quiz-start-btn').disabled, false);
  console.log('AI generation → server grading → tutor handoff and no-call retry passed.');
})().catch(error => { console.error(error); process.exitCode = 1; });
