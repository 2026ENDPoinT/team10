// Exercises the actual team's question bank and patched review button handlers.
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
vm.runInContext(`quizQuestions = QUESTION_BANK['프로그래밍입문(1)'].slice(0, 3); userAnswers = [0, 0, null];`, sandbox);
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
