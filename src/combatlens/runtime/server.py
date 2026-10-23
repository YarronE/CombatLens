"""Loopback-only HTTP server for the standalone workbench."""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .repository import Config, Repository, within
from .validation import WorkbenchError
from .preview import PreviewRepository
from .presentation import resolve as resolve_presentation
from .event_guide import resolve as resolve_event_guide
from .collection import Collection
from .design_study import resolve as resolve_design_study


class WorkbenchServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, repository):
        if address[0] != "127.0.0.1":
            raise ValueError("The workbench only binds 127.0.0.1.")
        self.repository = repository
        self.preview = PreviewRepository(repository)
        self.collection = Collection(repository)
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "CombatLens/0.1"

    def log_message(self, fmt, *args):
        # Avoid logging evidence locators, annotations or payloads.
        return

    def allowed_hosts(self):
        return {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

    def authorize(self, writing=False):
        host = self.headers.get("Host", "").lower()
        if host not in self.allowed_hosts():
            raise WorkbenchError("Request Host is not this loopback service.", status=403, code="host_rejected")
        origin = self.headers.get("Origin")
        allowed = {"http://" + host for host in self.allowed_hosts()}
        if origin is not None and origin not in allowed:
            raise WorkbenchError("Cross-origin requests are rejected.", status=403, code="origin_rejected")
        if writing and origin is None:
            raise WorkbenchError("Saving requires the local workbench Origin.", status=403, code="origin_required")
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            raise WorkbenchError("Cross-site requests are rejected.", status=403, code="origin_rejected")

    def reply(self, status, value):
        data = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def route_path(self):
        path = unquote(urlsplit(self.path).path)
        if path.startswith("/workspaces/"):
            parts=path.split("/",3)
            if len(parts)<4:raise WorkbenchError("Workspace route requires a path.",status=404,code="not_found")
            return "/"+parts[3]
        return path

    def context(self):
        path=unquote(urlsplit(self.path).path)
        if path.startswith("/workspaces/"):
            return self.server.collection.resolve(path.split("/",3)[2])
        return self.server.repository,self.server.preview

    def do_GET(self):
        try:
            self.authorize()
            path = self.route_path()
            repository, preview = self.context()
            if path == "/api/workspaces":
                self.reply(200, self.server.collection.response())
            elif path == "/api/run":
                from .repository import read_json
                self.reply(200, read_json(repository.research_dir / "run-report.json")[0])
            elif path == "/api/health":
                workspace = repository.root.resolve().as_posix().lower().encode("utf-8")
                self.reply(200, {"service": "combatlens", "api_version": 1,
                                 "pid": os.getpid(), "port": self.server.server_port,
                                 "workspace_fingerprint": hashlib.sha256(workspace).hexdigest()})
            elif path == "/api/design-study":
                self.reply(200, resolve_design_study(repository))
            elif path == "/api/event-guide":
                self.reply(200, resolve_event_guide(repository))
            elif path in {"/api/presentation", "/api/presentation/hero"}:
                theme, asset = resolve_presentation(repository)
                if path == "/api/presentation":
                    self.reply(200, theme)
                elif asset is None:
                    raise WorkbenchError("Registered presentation image unavailable.", status=404, code="not_found")
                else:
                    raw = asset.read_bytes()
                    if hashlib.sha256(raw).hexdigest() != theme['hero']['sha256']:
                        raise WorkbenchError("Presentation image changed.", status=409, code="stale_source")
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png" if asset.suffix.lower()==".png" else "image/jpeg")
                    self.send_header("Content-Length", str(len(raw)))
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    self.wfile.write(raw)
            elif path == "/api/research":
                self.reply(200, repository.research_response())
            elif path == "/api/timelines":
                self.reply(200, repository.timelines_response())
            elif path == "/api/preview":
                self.reply(200, preview.response())
            elif path.startswith("/api/preview/assets/"):
                self.preview_asset(path[len("/api/preview/assets/"):], preview)
            elif path == "/api/analyses":
                self.reply(200, repository.analyses())
            elif path.startswith("/api/analyses/"):
                self.reply(200, repository.analysis(path[len("/api/analyses/"):]))
            elif path.startswith("/api/source/"):
                self.reply(200, repository.source(path[len("/api/source/"):]))
            elif path.startswith("/api/"):
                raise WorkbenchError("Unknown API route.", status=404, code="not_found")
            else:
                self.static(path)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # A cancelled fetch is complete; a second response cannot reach it.
            self.close_connection = True
        except WorkbenchError as error:
            self.reply(error.status, error.payload())
        except (ValueError, OSError, RecursionError) as error:
            self.reply(500, {"error": "read_failed", "message": str(error)})

    def preview_asset(self, asset_id, preview=None):
        handle, size, sha = (preview or self.server.preview).binary(asset_id)
        with handle:
            self.send_response(200)
            self.send_header("Content-Type", "model/gltf-binary")
            self.send_header("Content-Length", str(size))
            self.send_header("Cache-Control", "no-store")
            self.send_header("ETag", '"' + sha + '"')
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            try:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    self.wfile.write(chunk)
            except OSError:
                # Headers are committed. End this stream instead of appending JSON.
                self.close_connection = True

    def static(self, request_path):
        web_root = (self.server.repository.root / "web").resolve()
        if "\x00" in request_path or "\\" in request_path or ".." in Path(request_path).parts:
            raise WorkbenchError("Static path rejected.", status=403, code="path_rejected")
        relative = "index.html" if request_path == "/" else request_path.lstrip("/")
        path = (web_root / relative).resolve()
        if not within(path, web_root) or not path.is_file():
            raise WorkbenchError("Static file was not found.", status=404, code="not_found")
        if path.suffix.lower() not in {".html", ".js", ".css", ".svg", ".png", ".jpg", ".ico", ".woff2", ".ttf", ".json"}:
            raise WorkbenchError("Static file type rejected.", status=403, code="path_rejected")
        raw = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        try:
            self.authorize(writing=True)
            repository, _ = self.context()
            if self.route_path() != "/api/analyses":
                raise WorkbenchError("Unknown save route.", status=404, code="not_found")
            if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                raise WorkbenchError("Save requests require application/json.", status=415, code="content_type_rejected")
            if self.headers.get("Transfer-Encoding"):
                raise WorkbenchError("Chunked save requests are not supported.")
            try:
                length = int(self.headers.get("Content-Length", "-1"))
            except ValueError as error:
                raise WorkbenchError("Invalid Content-Length.") from error
            if length < 0 or length > repository.config.max_request_bytes:
                raise WorkbenchError("Save payload exceeds the allowed size.", status=413, code="payload_too_large")
            raw = self.rfile.read(length)
            try:
                body = json.loads(raw.decode("utf-8"), parse_constant=lambda name: (_ for _ in ()).throw(ValueError(name)))
            except (UnicodeError, ValueError, RecursionError) as error:
                raise WorkbenchError("Invalid JSON payload.") from error
            self.reply(200, repository.save(body))
        except WorkbenchError as error:
            self.reply(error.status, error.payload())
        except (OSError, ValueError, RecursionError) as error:
            self.reply(500, {"error": "save_failed", "message": str(error)})


def create_server(config, host="127.0.0.1", port=8766):
    return WorkbenchServer((host, port), Repository(config))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only local game evidence and editable analysis copies.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--research-dir", type=Path, default=None)
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args(argv)
    server = create_server(Config(args.repo_root,research_dir=args.research_dir), port=args.port)
    print(f"Workbench: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
