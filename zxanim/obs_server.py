import json
import mimetypes
import threading
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


OBS_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
html,body{width:100%;height:100%;margin:0;overflow:hidden;background:transparent}
body{display:flex;align-items:center;justify-content:center}
img{width:100%;height:100%;object-fit:contain}
</style>
</head>
<body>
<img id="character" alt="">
<script>
const image=document.getElementById("character");
let current="";
async function update(){
  try{
    const response=await fetch("/state",{cache:"no-store"});
    const state=await response.json();
    if(state.asset!==current){
      current=state.asset;
      image.src=current;
    }
  }catch(error){}
}
setInterval(update,16);
update();
</script>
</body>
</html>
"""


class ObsState:
    def __init__(self):
        self._lock = threading.Lock()
        self._state = {"asset": ""}

    def update(self, asset):
        with self._lock:
            self._state = {"asset": asset}

    def snapshot(self):
        with self._lock:
            return deepcopy(self._state)


class ObsServer:
    def __init__(self, repository, state, port):
        self.repository = repository
        self.state = state
        self.requested_port = int(port)
        self.httpd = None
        self.thread = None

    @property
    def port(self):
        if not self.httpd:
            return self.requested_port
        return self.httpd.server_address[1]

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}/"

    def start(self):
        handler = self._handler_class()
        try:
            self.httpd = ThreadingHTTPServer(("127.0.0.1", self.requested_port), handler)
        except OSError:
            self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
        if self.thread:
            self.thread.join(timeout=2)
            self.thread = None

    def _handler_class(self):
        repository = self.repository
        state = self.state

        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                path = urlparse(self.path).path
                if path == "/":
                    self._send(200, OBS_PAGE.encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/state":
                    payload = json.dumps(state.snapshot()).encode("utf-8")
                    self._send(200, payload, "application/json")
                    return
                if path.startswith("/asset/"):
                    self._serve_asset(path)
                    return
                self._send(404, b"Not found", "text/plain; charset=utf-8")

            def _serve_asset(self, path):
                parts = unquote(path).split("/", 3)
                if len(parts) != 4:
                    self._send(404, b"Not found", "text/plain; charset=utf-8")
                    return
                pack = repository.get(parts[2])
                if not pack:
                    self._send(404, b"Not found", "text/plain; charset=utf-8")
                    return
                asset = (pack.root / Path(parts[3])).resolve()
                if pack.root not in asset.parents or not asset.is_file():
                    self._send(404, b"Not found", "text/plain; charset=utf-8")
                    return
                content_type = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
                self._send(200, asset.read_bytes(), content_type, cache=True)

            def _send(self, status, payload, content_type, cache=False):
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(payload)))
                self.send_header(
                    "Cache-Control",
                    "public, max-age=3600" if cache else "no-store",
                )
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, format_string, *args):
                return

        return RequestHandler
