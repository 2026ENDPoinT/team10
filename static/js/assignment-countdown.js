// Deadlines and calendar-day labels use Korea time regardless of browser timezone.
function assignmentCountdown(deadlineText, now = Date.now()) {
    const deadline = Date.parse(deadlineText);
    if (!Number.isFinite(deadline)) return '마감 일시 확인 필요';
    const koreaDay = time => new Date(time + 9 * 3600000).toISOString().slice(0, 10);
    const days = Math.round((Date.parse(koreaDay(deadline)) - Date.parse(koreaDay(now))) / 86400000);
    if (days > 0) return 'D-' + days;
    if (days < 0) return '마감 ' + Math.abs(days) + '일 지남';

    const remaining = deadline - now;
    if (remaining <= 0) return '오늘 마감 · 마감 시간이 지났어요';
    if (remaining < 60000) return '오늘 마감 · 1분 이내 마감';
    const minutes = Math.ceil(remaining / 60000);
    const hours = Math.floor(minutes / 60);
    const rest = minutes % 60;
    const duration = hours
        ? hours + '시간' + (rest ? ' ' + rest + '분' : '')
        : minutes + '분';
    return '오늘 마감 · ' + duration + ' 후 마감';
}

if (typeof document !== 'undefined') {
    function refreshAssignmentCountdowns() {
        const now = Date.now();
        document.querySelectorAll('[data-task-deadline]').forEach(badge => {
            badge.textContent = assignmentCountdown(badge.dataset.taskDeadline, now);
        });
    }
    refreshAssignmentCountdowns();
    setInterval(refreshAssignmentCountdowns, 1000);
    document.addEventListener('visibilitychange', refreshAssignmentCountdowns);
}

if (typeof module !== 'undefined') module.exports = {assignmentCountdown};
