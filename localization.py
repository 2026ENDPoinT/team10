import json
import re
from pathlib import Path
from flask import request


def init_localization(app):
    translations = json.loads((Path(app.root_path) / 'static/translations.json').read_text(encoding='utf-8'))

    def language():
        return 'en' if request.cookies.get('ui_language') == 'en' else 'ko'

    def translate(value):
        if language() != 'en' or not isinstance(value, str):
            return value
        if value in translations:
            return translations[value]
        match = re.fullmatch(r'(\d)학년 (\d)학기', value)
        if match:
            return f'Year {match[1]} · Semester {match[2]}'
        if value == '오늘 마감':
            return 'Due today'
        if value == '오늘 마감 · 시간 지남':
            return 'Due today · Deadline passed'
        match = re.fullmatch(r'마감 (\d+)일 지남', value)
        if match:
            return f'{match[1]} day(s) overdue'
        match = re.fullmatch(r'(\d{4})년 (.+)', value)
        if match:
            return f'{match[1]} {translations.get(match[2], match[2])}'
        return value

    app.jinja_env.filters['ui_text'] = translate
    app.context_processor(lambda: {'t': translate, 'ui_language': language(), 'ui_translations': translations})

    @app.after_request
    def translate_errors(response):
        if language() == 'en' and response.is_json:
            data = response.get_json(silent=True)
            if isinstance(data, dict) and isinstance(data.get('error'), str):
                data['error'] = translate(data['error'])
                response.set_data(app.json.dumps(data))
        return response
