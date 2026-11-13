// Each create/edit form owns its date fields. Impossible dates require reselection.
document.querySelectorAll('.deadline-picker').forEach(picker => {
    const year = picker.querySelector('[name="deadline_year"]');
    const month = picker.querySelector('[name="deadline_month"]');
    const day = picker.querySelector('[name="deadline_day"]');
    const time = picker.querySelector('[name="deadline_time"]');
    const error = picker.querySelector('.deadline-error');
    function validateDeadline() {
        const completeDate = year.value && month.value && day.value;
        const deadline = completeDate ? Date.parse(
            year.value + '-' + month.value.padStart(2, '0') + '-' + day.value.padStart(2, '0')
            + 'T' + (time.value || '23:59') + ':00+09:00') : NaN;
        const expired = Number.isFinite(deadline) && deadline < Date.now();
        const message = expired ? (window.UI_LANGUAGE === 'en'
            ? 'You cannot enter a date or time in the past.'
            : '이미 지난 시간을 입력할 수 없습니다.') : '';
        time.setCustomValidity(message);
        error.textContent = message;
        error.hidden = !expired;
        time.setAttribute('aria-invalid', String(expired));
        return !expired;
    }
    function updateDays() {
        const selected = day.value;
        const count = year.value && month.value
            ? new Date(Number(year.value), Number(month.value), 0).getDate() : 31;
        day.replaceChildren(new Option('DD', ''));
        for (let value = 1; value <= count; value++) {
            day.add(new Option(value + (window.UI_LANGUAGE === 'en' ? '' : '일'), String(value)));
        }
        day.value = selected && Number(selected) <= count ? selected : '';
        validateDeadline();
    }
    year.addEventListener('change', updateDays);
    month.addEventListener('change', updateDays);
    day.addEventListener('change', validateDeadline);
    time.addEventListener('input', validateDeadline);
    time.addEventListener('change', validateDeadline);
    picker.closest('form').addEventListener('submit', event => {
        if (!validateDeadline()) {
            event.preventDefault();
            time.reportValidity();
        }
    });
    updateDays();
});
