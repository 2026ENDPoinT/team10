"""Temporary real HTTP smoke check. Does not call AI or leave a server running."""
from pathlib import Path
import sys
import threading
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import app
from werkzeug.serving import make_server

server = make_server('127.0.0.1', 0, app, threaded=True)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f'http://127.0.0.1:{server.server_port}'
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
    for path in ('/', '/quiz?student_id=12345678&name=Test&year=1', '/ai/', '/ai/api/health'):
        with opener.open(base + path, timeout=5) as response:
            assert response.status == 200
            print(f'HTTP 200: {path}', flush=True)
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)
