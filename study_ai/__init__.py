import os

from flask import Blueprint, current_app, jsonify, render_template, request, session, url_for
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge

from .service import TutorError, answer_question
from .resources import find_video_lessons
from .validation import validate_payload

bp = Blueprint('study_ai', __name__, template_folder='templates',
               static_folder='static', url_prefix='/ai')


def init_study_ai(app):
    """Register this module without modifying existing quiz, score or DB routes."""
    app.config.setdefault('AI_MODE', os.getenv('AI_MODE', 'gemini'))
    app.config.setdefault('OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
    app.config.setdefault('OPENAI_MODEL', os.getenv('OPENAI_MODEL', 'gpt-5.4-mini'))
    app.config.setdefault('YOUTUBE_API_KEY', os.getenv('YOUTUBE_API_KEY', ''))
    app.config.setdefault('GEMINI_API_KEY', os.getenv('GEMINI_API_KEY', ''))
    app.config.setdefault('GEMINI_MODEL', os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite'))
    app.register_blueprint(bp)


@bp.get('/')
def index():
    back_url = None
    endpoint = current_app.config.get('STUDY_BACK_ENDPOINT')
    navigation = session.get('study_navigation')
    if endpoint and navigation:
        back_url = url_for(endpoint, **navigation)
    elif 'index' in current_app.view_functions:
        back_url = url_for('index')
    return render_template('study_ai/chat.html', mode=current_app.config['AI_MODE'],
                           configured=bool(current_app.config.get('GEMINI_API_KEY' if current_app.config['AI_MODE'] == 'gemini' else 'OPENAI_API_KEY')), back_url=back_url)


@bp.get('/api/health')
def health():
    mode = current_app.config['AI_MODE']
    ready = mode == 'demo' or (mode in ('openai', 'gemini') and bool(current_app.config.get('GEMINI_API_KEY' if mode == 'gemini' else 'OPENAI_API_KEY')))
    return jsonify(mode=mode, configured=ready)


@bp.post('/api/chat')
def chat():
    # JSON + same-origin requests keep unrelated websites from using the local API.
    origin = request.headers.get('Origin')
    if origin and origin != request.host_url.rstrip('/'):
        return jsonify(error='Cross-origin requests are not enabled.'), 403
    if not request.is_json:
        return jsonify(error='Send application/json.'), 415
    request.max_content_length = 128 * 1024
    try:
        payload = validate_payload(request.get_json())
        answer = answer_question(payload, current_app.config)
        videos = find_video_lessons(answer['video_query'], payload['preferences'], current_app.config)
        return jsonify(reply=answer['reply'], study_topic=answer['study_topic'],
                       videos=videos, mode=current_app.config['AI_MODE'])
    except RequestEntityTooLarge:
        return jsonify(error='The request is too large.'), 413
    except BadRequest:
        return jsonify(error='The request contains invalid JSON.'), 400
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except TutorError as exc:
        return jsonify(error=str(exc)), exc.status
