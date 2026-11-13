// Each create/edit form owns its date fields. Impossible dates require reselection.
document.querySelectorAll('.deadline-picker').forEach(picker => {
    const year = picker.querySelector('[name="deadline_year"]');
    const month = picker.querySelector('[name="deadline_month"]');
    const day = picker.querySelector('[name="deadline_day"]');
    function updateDays() {
        const selected = day.value;
        const count = year.value && month.value
            ? new Date(Number(year.value), Number(month.value), 0).getDate() : 31;
        day.replaceChildren(new Option('DD', ''));
        for (let value = 1; value <= count; value++) {
            day.add(new Option(value + (window.UI_LANGUAGE === 'en' ? '' : '일'), String(value)));
        }
        day.value = selected && Number(selected) <= count ? selected : '';
    }
    year.addEventListener('change', updateDays);
    month.addEventListener('change', updateDays);
    updateDays();
});
