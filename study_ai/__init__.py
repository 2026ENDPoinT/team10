import os

from flask import Blueprint, current_app, jsonify, render_template, request
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge

from .service import TutorError, answer_question
from .resources import find_video_lessons
from .validation import validate_payload

bp = Blueprint('study_ai', __name__, template_folder='templates',
               static_folder='static', url_prefix='/ai')


def init_study_ai(app):
    """Register this module without modifying existing quiz, score or DB routes."""
    app.config.setdefault('AI_MODE', os.getenv('AI_MODE', 'groq'))
    app.config.setdefault('GROQ_API_KEY', os.getenv('GROQ_API_KEY', ''))
    app.config.setdefault('GROQ_MODEL', os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b'))
    app.config.setdefault('OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
    app.config.setdefault('OPENAI_MODEL', os.getenv('OPENAI_MODEL', 'gpt-5.4-mini'))
    app.config.setdefault('YOUTUBE_API_KEY', os.getenv('YOUTUBE_API_KEY', ''))
    app.config.setdefault('GEMINI_API_KEY', os.getenv('GEMINI_API_KEY', ''))
    app.config.setdefault('GEMINI_MODEL', os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite'))
    app.register_blueprint(bp)


@bp.get('/')
def index():
    assignment_plan = None
    if request.args.get('assignment_id') is not None:
        from assignments import planning_context
        assignment_id = request.args.get('assignment_id', type=int)
        if assignment_id is None:
            from flask import abort
            abort(400)
        assignment_plan = planning_context(assignment_id)
    mode = current_app.config['AI_MODE']
    key_name = {'groq': 'GROQ_API_KEY', 'gemini': 'GEMINI_API_KEY', 'openai': 'OPENAI_API_KEY'}.get(mode, '')
    return render_template('study_ai/chat.html', mode=mode, key_name=key_name, assignment_plan=assignment_plan,
                           provider_name={'groq': 'Groq', 'gemini': 'Google Gemini', 'openai': 'OpenAI'}.get(mode, mode),
                           configured=bool(current_app.config.get(key_name)))


@bp.get('/api/health')
def health():
    mode = current_app.config['AI_MODE']
    key_name = {'groq': 'GROQ_API_KEY', 'gemini': 'GEMINI_API_KEY', 'openai': 'OPENAI_API_KEY'}.get(mode, '')
    ready = mode == 'demo' or bool(current_app.config.get(key_name))
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
