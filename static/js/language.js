let languageFormChanged = false;
document.addEventListener('input', () => { languageFormChanged = true; });
document.addEventListener('change', () => { languageFormChanged = true; });
window.uiText = function (text) {
    return window.UI_LANGUAGE === 'en' ? (window.UI_TRANSLATIONS[text] ?? text) : text;
};
window.switchSiteLanguage = function () {
    const warning = window.UI_LANGUAGE === 'en'
        ? 'Switch language and reload? Unsaved entries and this chat will be cleared.'
        : '언어를 바꾸면 페이지가 새로고침됩니다. 저장하지 않은 입력과 현재 대화가 지워집니다. 변경할까요?';
    const hasChat = document.querySelectorAll('#messages .message').length > 1;
    if ((languageFormChanged || hasChat) && !window.confirm(warning)) return;
    const next = window.UI_LANGUAGE === 'en' ? 'ko' : 'en';
    document.cookie = 'ui_language=' + next + '; Path=/; Max-Age=31536000; SameSite=Lax';
    window.location.reload();
};
