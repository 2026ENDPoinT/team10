/* Adapter for team10/static/js/quiz.js. Does not change grading or the question bank. */
(() => {
  'use strict';
  function buildContext(subject, questions, answers, onlyMissed = true) {
    if (!Array.isArray(questions) || !Array.isArray(answers) || questions.length !== answers.length)
      throw new Error('Quiz questions and answers must have matching lengths.');
    return {
      subject,
      questions: questions.map((q, index) => ({
        question: q.question, choices: [...q.choices], answer: q.answer,
        selected_answer: answers[index] ?? null, explanation: q.explanation || ''
      })).filter(q => !onlyMissed || q.selected_answer !== q.answer)
    };
  }
  function openTutor(context, tutorUrl = '/ai/') {
    if (!context.questions.length) return false;
    if (context.questions.length > 10) throw new Error('Send at most ten quiz questions.');
    const target = new URL(tutorUrl, window.location.href);
    if (target.origin !== window.location.origin)
      throw new Error('The quiz bridge requires the tutor on the same origin after merging.');
    sessionStorage.setItem('team10.studyQuizContext', JSON.stringify(context));
    window.location.assign(target.href);
    return true;
  }
  window.StudyQuizBridge = Object.freeze({buildContext, openTutor});
})();
