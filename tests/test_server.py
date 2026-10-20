"""Behavior tests use synthetic evidence, never game assets."""
import copy
import hashlib
import gzip
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from combatlens.runtime.repository import Config, Repository
from combatlens.runtime.server import Handler, create_server
from combatlens.runtime.validation import WorkbenchError


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix=".test-", dir=Path(__file__).resolve().parent)
        self.root = Path(self.temporary.name)
        self.research = self.root / "local/research"
        self.research.mkdir(parents=True)
        self.snapshot = self.research / "original.json"
        self.snapshot.write_text('{"synthetic_original":3}', encoding="utf-8")
        self.source_hash = hashlib.sha256(self.snapshot.read_bytes()).hexdigest()
        self.package = {"schema_version": 1, "game_build": "synthetic-build", "sources": [{"id": "source-one", "snapshot_path": str(self.snapshot), "sha256": self.source_hash}], "objects": [], "relations": [], "claims": []}
        self.package_path = self.research / "research-package.json"
        self.package_path.write_text(json.dumps(self.package), encoding="utf-8")
        self.fingerprint = hashlib.sha256(self.package_path.read_bytes()).hexdigest()
        self.originals = {"schema_version": "timeline-source/1", "game_build": "synthetic-build", "package_fingerprint": self.fingerprint, "objects": [{"id": "character-one", "role": "character", "name": "Synthetic character", "mapping_status": "synthetic", "sequences": [{"id": "sequence-one", "name": "Synthetic action", "action_id": "synthetic", "unit": None, "duration": None, "origin": {"kind": "unknown", "source_ids": ["source-one"]}, "source_ids": ["source-one"], "events": [{"id": "event-one", "label": "Unknown event", "kind": "unknown", "track": "unplaced", "start": None, "end": None, "timing_status": "unknown", "raw_value": {"original": 3}, "raw_unit": None, "source_ids": ["source-one"], "locator": {"field": "synthetic_original"}, "analysis_override": None}]}], "graph": {"nodes": [], "edges": []}}]}
        (self.research / "timelines.json").write_text(json.dumps(self.originals), encoding="utf-8")
        (self.research / "source-root.json").write_text(json.dumps({"root": str(self.research)}), encoding="utf-8")
        self.repository = Repository(Config(self.root))
        (self.root / "web").mkdir()
        (self.root / "web/index.html").write_text("<!doctype html><title>Synthetic</title>", encoding="utf-8")
        self.server = create_server(Config(self.root), port=0)
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=2)
        self.temporary.cleanup()

    def analysis(self, analysis_id="copy-one"):
        return {"schema_version": "timeline-analysis/1", "analysis_id": analysis_id, "name": "Synthetic analysis", "revision": 0, "game_build": "synthetic-build", "parent_package_fingerprint": self.fingerprint, "objects": copy.deepcopy(self.originals["objects"])}

    @staticmethod
    def event(analysis):
        return analysis["objects"][0]["sequences"][0]["events"][0]

    @staticmethod
    def override():
        return {"start": 1.5, "end": 2.0, "unit": "seconds", "note": "Synthetic hypothesis", "reason": "Synthetic test", "timing_status": "analyst_hypothesis", "parameters": {"proposed": 7}, "deleted": False}

    def request(self, path, body=None, headers=None):
        request_headers = {"Origin": self.base}
        request_headers.update(headers or {})
        raw = None if body is None else json.dumps(body).encode("utf-8")
        if body is not None:
            request_headers["Content-Type"] = "application/json"
        request = Request(self.base + path, data=raw, headers=request_headers)
        try:
            with urlopen(request, timeout=3) as response:
                data = response.read()
                return response.status, json.loads(data) if path.startswith("/api/") else data
        except HTTPError as error:
            return error.code, json.loads(error.read())

    def test_analysis_catalog_scopes_build_and_package_without_deleting_other_cases(self):
        self.repository.analyses_dir.mkdir(parents=True,exist_ok=True)
        for identity,build,fp in [('current','synthetic-build',self.fingerprint),('other-build','different',self.fingerprint),('other-package','synthetic-build','0'*64)]:
            value={'schema_version':'timeline-analysis/1','analysis_id':identity,'game_build':build,'parent_package_fingerprint':fp,'revision':1}
            (self.repository.analyses_dir/(identity+'.json')).write_text(json.dumps(value),encoding='utf-8')
        self.assertEqual([v['analysis_id'] for v in self.repository.analyses()['analyses']],['current'])
        self.assertEqual(len(list(self.repository.analyses_dir.glob('*.json'))),3)

    def test_save_reopen_revision_backup_and_source_unchanged(self):
        analysis = self.analysis()
        self.event(analysis)["analysis_override"] = self.override()
        status, saved = self.request("/api/analyses", {"expected_revision": 0, "analysis": analysis})
        self.assertEqual(status, 200)
        self.assertEqual(saved["revision"], 1)
        self.assertEqual(hashlib.sha256(Path(saved["path"]).read_bytes()).hexdigest(), saved["sha256"])
        status, reopened = self.request("/api/analyses/copy-one")
        self.assertEqual(status, 200)
        self.assertEqual(self.event(reopened)["raw_value"], {"original": 3})
        self.assertEqual(self.event(reopened)["analysis_override"]["start"], 1.5)
        self.assertFalse(reopened["validity"]["stale_package"])
        reopened["name"] = "Second revision"
        status, second = self.request("/api/analyses", {"expected_revision": 1, "analysis": reopened})
        self.assertEqual((status, second["revision"]), (200, 2))
        backup = json.loads(Path(second["path"]).with_suffix(".json.bak").read_text(encoding="utf-8"))
        self.assertEqual(backup["revision"], 1)
        self.assertEqual(hashlib.sha256(self.snapshot.read_bytes()).hexdigest(), self.source_hash)

    def test_concurrent_windows_cannot_overwrite_a_new_revision(self):
        payload = {"expected_revision": 0, "analysis": self.analysis()}
        with ThreadPoolExecutor(max_workers=2) as pool:
            replies = list(pool.map(lambda _: self.request("/api/analyses", payload), range(2)))
        self.assertEqual(sorted(status for status, _ in replies), [200, 409])
        conflict = next(body for status, body in replies if status == 409)
        self.assertEqual(conflict["latest_revision"], 1)
        self.assertEqual(self.repository.analysis("copy-one")["revision"], 1)

    def test_source_registry_cannot_replace_fingerprinted_package_hash(self):
        self.snapshot.write_text('{"synthetic_original":999}',encoding='utf-8')
        changed_sha=hashlib.sha256(self.snapshot.read_bytes()).hexdigest()
        registry={"root":str(self.research),"sources":{"source-one":{"path":str(self.snapshot),"sha256":changed_sha}}}
        (self.research/"source-root.json").write_text(json.dumps(registry),encoding='utf-8')
        with self.assertRaises(WorkbenchError) as caught:self.repository.registry()
        self.assertEqual((caught.exception.status,caught.exception.code),(503,"invalid_source_registry"))
        status,body=self.request("/api/research")
        self.assertEqual((status,body["error"]),(503,"invalid_source_registry"))
        status,body=self.request("/api/analyses",{"expected_revision":0,"analysis":self.analysis()})
        self.assertEqual((status,body["error"]),(503,"invalid_source_registry"))
        self.assertFalse(self.repository.analyses_dir.exists())
        # A path-only mapping preserves the package's original expected hash;
        # changing the bytes then reports stale instead of declaring current.
        registry["sources"]["source-one"].pop("sha256")
        (self.research/"source-root.json").write_text(json.dumps(registry),encoding='utf-8')
        self.assertEqual(self.repository.validity()["sources"]["source-one"]["status"],"changed")

    def test_reject_original_parameter_graph_source_and_event_deletion_changes(self):
        mutations = [lambda doc: self.event(doc)["raw_value"].update(original=999), lambda doc: doc["objects"][0]["graph"]["nodes"].append({"id": "fake"}), lambda doc: self.event(doc).update(source_ids=["fake-source"]), lambda doc: doc["objects"][0]["sequences"][0]["events"].clear()]
        for mutate in mutations:
            analysis = self.analysis()
            mutate(analysis)
            with self.assertRaises(WorkbenchError):
                self.repository.save({"expected_revision": 0, "analysis": analysis})
        self.assertFalse(self.repository.analysis_path("copy-one").exists())

    def test_parameters_soft_delete_and_new_event_roundtrip(self):
        analysis = self.analysis()
        override = self.override()
        override["deleted"] = True
        self.event(analysis)["analysis_override"] = override
        new = {"id": "analysis-12345678-1234-1234-1234-123456789abc", "label": "Hypothesis", "kind": "analysis_event", "track": "analysis", "start": None, "end": None, "unit": None, "note": "Untimed", "reason": "Synthetic test", "parameters": [1, {"value": 2}], "source_ids": ["source-one"], "timing_status": "analyst_hypothesis"}
        analysis["objects"][0]["sequences"][0]["analysis_events"] = [new]
        saved = self.repository.save({"expected_revision": 0, "analysis": analysis})["analysis"]
        self.assertEqual(len(saved["objects"][0]["sequences"][0]["events"]), 1)
        self.assertTrue(self.event(saved)["analysis_override"]["deleted"])
        self.assertEqual(saved["objects"][0]["sequences"][0]["analysis_events"], [new])

    def numeric_originals(self):
        event = self.originals["objects"][0]["sequences"][0]["events"][0]
        event["raw_value"] = {"scalar": 1.0, "flag": True}
        (self.research / "timelines.json").write_text(json.dumps(self.originals), encoding="utf-8")

    def test_integral_number_roundtrip_preserves_server_original_float(self):
        self.numeric_originals()
        analysis = self.analysis()
        self.event(analysis)["raw_value"]["scalar"] = 1
        self.event(analysis)["analysis_override"] = self.override()
        saved = self.repository.save({"expected_revision": 0, "analysis": analysis})["analysis"]
        self.assertIs(type(self.event(saved)["raw_value"]["scalar"]), float)
        self.assertEqual(self.event(saved)["raw_value"]["scalar"], 1.0)

    def test_numeric_equivalence_never_accepts_bool_alias_or_changed_value(self):
        self.numeric_originals()
        for key, changed in [("scalar", True), ("flag", 1), ("scalar", 1.0000000000000002)]:
            analysis = self.analysis()
            self.event(analysis)["raw_value"][key] = changed
            with self.assertRaises(WorkbenchError) as context:
                self.repository.save({"expected_revision": 0, "analysis": analysis})
            self.assertEqual(context.exception.code, "original_modified")

    def test_real_javascript_json_roundtrip_can_save_unchanged_evidence(self):
        node = os.environ.get("WORKBENCH_NODE") or shutil.which("node")
        if not node:
            self.skipTest("Node is unavailable; numeric semantics are separately tested")
        self.numeric_originals()
        result = subprocess.run([node, "-e", "let s='';process.stdin.setEncoding('utf8');process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>process.stdout.write(JSON.stringify(JSON.parse(s))));"], input=json.dumps(self.analysis()), text=True, capture_output=True, check=True)
        analysis = json.loads(result.stdout)
        self.assertIs(type(self.event(analysis)["raw_value"]["scalar"]), int)
        self.event(analysis)["analysis_override"] = self.override()
        status, saved = self.request("/api/analyses", {"expected_revision": 0, "analysis": analysis})
        self.assertEqual(status, 200)
        self.assertEqual(saved["revision"], 1)
        self.assertIs(type(self.event(saved["analysis"])["raw_value"]["scalar"]), float)

    def test_reject_bad_intervals_nonfinite_parameters_and_unknown_new_sources(self):
        for key, value in [("start", float("nan")), ("end", float("inf")), ("end", 1.0), ("start", True), ("parameters", {"bad": float("inf")})]:
            analysis = self.analysis()
            override = self.override()
            override[key] = value
            self.event(analysis)["analysis_override"] = override
            with self.assertRaises(WorkbenchError):
                self.repository.save({"expected_revision": 0, "analysis": analysis})
        analysis = self.analysis()
        self.event(analysis)["analysis_override"] = self.override()
        analysis["objects"][0]["sequences"][0]["analysis_events"] = [{"id": "analysis-12345678-1234-1234-1234-123456789abc", "label": "Invalid", "kind": "analysis_event", "track": "analysis", "start": None, "end": None, "unit": None, "note": "", "reason": "Synthetic", "parameters": None, "source_ids": ["unregistered"], "timing_status": "analyst_hypothesis"}]
        with self.assertRaises(WorkbenchError):
            self.repository.save({"expected_revision": 0, "analysis": analysis})

    def test_schema_build_fingerprint_and_ids_are_checked(self):
        for key, value in [("schema_version", "timeline-analysis/2"), ("game_build", "old-build"), ("parent_package_fingerprint", "old-package"), ("analysis_id", "../../escape"), ("revision", True)]:
            analysis = self.analysis()
            analysis[key] = value
            with self.assertRaises(WorkbenchError):
                self.repository.save({"expected_revision": 0, "analysis": analysis})
        self.assertFalse((self.root / "escape.json").exists())

    def test_source_change_is_stale_without_mutating_saved_values(self):
        self.repository.save({"expected_revision": 0, "analysis": self.analysis()})
        self.snapshot.write_text('{"synthetic_original":999}', encoding="utf-8")
        reopened = self.repository.analysis("copy-one")
        self.assertEqual(reopened["validity"]["sources"]["source-one"]["status"], "changed")
        self.assertIn("event-one", reopened["validity"]["affected_event_ids"])
        self.assertEqual(self.event(reopened)["raw_value"], {"original": 3})
        self.package["title"] = "Updated package"
        self.package_path.write_text(json.dumps(self.package), encoding="utf-8")
        self.assertTrue(self.repository.analysis("copy-one")["validity"]["stale_package"])

    def test_failed_atomic_replace_preserves_old_file_and_cleans_temporary_files(self):
        saved = self.repository.save({"expected_revision": 0, "analysis": self.analysis()})
        path = Path(saved["path"])
        old = path.read_bytes()
        changed = copy.deepcopy(saved["analysis"])
        changed["name"] = "Failed edit"
        real_replace = os.replace
        def fail_final(source, destination):
            if Path(destination) == path:
                raise OSError("Synthetic interrupted write")
            return real_replace(source, destination)
        with patch("combatlens.runtime.repository.os.replace", side_effect=fail_final):
            with self.assertRaises(WorkbenchError) as context:
                self.repository.save({"expected_revision": 1, "analysis": changed})
        self.assertEqual(context.exception.code, "save_failed")
        self.assertEqual(path.read_bytes(), old)
        self.assertFalse(list(path.parent.glob("*.tmp")))

    def test_http_host_origin_registered_source_and_static_traversal(self):
        self.assertEqual(self.request("/")[0], 200)
        self.assertEqual(self.request("/api/research", headers={"Host": "external.invalid"})[0], 403)
        self.assertEqual(self.request("/api/research", headers={"Origin": "https://external.invalid"})[0], 403)
        self.assertEqual(self.request("/api/analyses", {"expected_revision": 0, "analysis": self.analysis()}, {"Origin": "null"})[0], 403)
        self.assertEqual(self.request("/%2e%2e/local/research/original.json")[0], 403)
        self.assertEqual(self.request("/api/source/source-one")[1]["content"], {"synthetic_original": 3})
        self.assertEqual(self.request("/api/source/not-registered")[0], 404)
        self.package["sources"][0]["snapshot_path"] = str(self.root / "outside.json")
        (self.root / "outside.json").write_text('{"private":true}', encoding="utf-8")
        self.package_path.write_text(json.dumps(self.package), encoding="utf-8")
        self.assertEqual(self.repository.source_status(self.repository.registry()["source-one"])["status"], "unavailable")
        with self.assertRaises(WorkbenchError) as context:
            self.repository.source("source-one")
        self.assertEqual(context.exception.status, 403)

    def test_symlink_source_cannot_escape_approved_root(self):
        outside = self.root / "outside.json"
        outside.write_text("{}", encoding="utf-8")
        link = self.research / "link.json"
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest("Symlink creation is unavailable on this host")
        self.package["sources"][0]["snapshot_path"] = str(link)
        self.package_path.write_text(json.dumps(self.package), encoding="utf-8")
        with self.assertRaises(WorkbenchError):
            self.repository.source("source-one")

    def test_relative_snapshot_uses_trusted_external_root_and_gzip_hash_scope(self):
        evidence = self.root / "evidence"
        evidence.mkdir()
        compressed = evidence / "synthetic.json.gz"
        with gzip.open(compressed, "wb") as handle:
            handle.write(b'{"external_synthetic":7}')
        compressed_hash = hashlib.sha256(compressed.read_bytes()).hexdigest()
        self.package["sources"][0].update(snapshot_path="synthetic.json.gz", sha256=compressed_hash)
        self.package_path.write_text(json.dumps(self.package), encoding="utf-8")
        (self.research / "source-root.json").write_text(json.dumps({"root": str(evidence)}), encoding="utf-8")
        response = self.repository.source("source-one")
        self.assertEqual(response["path"], str(compressed.resolve()))
        self.assertEqual(response["content"], {"external_synthetic": 7})
        self.assertEqual(response["content_kind"], "json")
        self.assertEqual(response["content_encoding"], "gzip")
        self.assertEqual(response["validity"]["sha256"], compressed_hash)
        self.assertEqual(response["validity"]["status"], "current")
        self.package["sources"][0]["snapshot_path"] = "../local/research/original.json"
        self.package_path.write_text(json.dumps(self.package), encoding="utf-8")
        with self.assertRaises(WorkbenchError):
            self.repository.source("source-one")

    def test_health_identifies_workspace_without_reading_evidence_and_authorizes_first(self):
        expected = {"service": "combatlens", "api_version": 1,
                    "pid": os.getpid(), "port": self.server.server_port,
                    "workspace_fingerprint": hashlib.sha256(self.root.resolve().as_posix().lower().encode("utf-8")).hexdigest()}
        with ExitStack() as stack:
            for target in ("combatlens.runtime.repository.read_json", "combatlens.runtime.preview.read_json"):
                stack.enter_context(patch(target, side_effect=AssertionError("Health read evidence")))
            stack.enter_context(patch.object(Path, "read_bytes", side_effect=AssertionError("Health read a file")))
            for name in ("response", "binary", "open_asset"):
                stack.enter_context(patch.object(self.server.preview, name, side_effect=AssertionError("Health touched preview")))
            self.assertEqual(self.request("/api/health"), (200, expected))
            with patch("combatlens.runtime.server.os.getpid", side_effect=AssertionError("Unauthorized request entered health")):
                for headers, code in [({"Host": "external.invalid"}, "host_rejected"),
                                      ({"Origin": "https://external.invalid"}, "origin_rejected"),
                                      ({"Sec-Fetch-Site": "cross-site"}, "origin_rejected")]:
                    with self.subTest(headers=headers):
                        status, body = self.request("/api/health", headers=headers)
                        self.assertEqual((status, body["error"]), (403, code))
        self.assertFalse(self.repository.analyses_dir.exists())
        self.assertEqual(hashlib.sha256(self.snapshot.read_bytes()).hexdigest(), self.source_hash)

    def test_service_rejects_non_loopback_bind(self):
        with self.assertRaises(ValueError):
            create_server(Config(self.root), host="0.0.0.0", port=0)


class PreviewStreamTests(unittest.TestCase):
    @staticmethod
    def handler(binary):
        handler = Handler.__new__(Handler)
        handler.server = SimpleNamespace(server_port=8766, repository=SimpleNamespace(),
                                         preview=SimpleNamespace(binary=binary))
        handler.path = "/api/preview/assets/synthetic-asset"
        handler.headers = {"Host": "127.0.0.1:8766"}
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = io.BytesIO()
        handler.close_connection = False
        return handler

    def test_client_abort_never_replies_twice_and_always_closes_asset(self):
        for error_type in (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            for phase in ("headers", "body"):
                with self.subTest(error=error_type.__name__, phase=phase):
                    handle = io.BytesIO(b"synthetic-glb")
                    handle.read = Mock(side_effect=[b"first", b"second", b""])
                    handler = self.handler(Mock(return_value=(handle, 12, "synthetic-sha")))
                    handler.reply = Mock()
                    if phase == "headers":
                        handler.end_headers.side_effect = error_type("Synthetic client abort")
                    else:
                        handler.wfile = Mock()
                        handler.wfile.write.side_effect = [5, error_type("Synthetic client abort")]
                    handler.do_GET()
                    handler.send_response.assert_called_once_with(200)
                    handler.reply.assert_not_called()
                    self.assertTrue(handler.close_connection)
                    self.assertTrue(handle.closed)
                    if phase == "body":
                        self.assertEqual(handler.wfile.write.call_count, 2)

    def test_read_failure_after_headers_closes_stream_without_json_error(self):
        handle = io.BytesIO(b"synthetic-glb")
        handle.read = Mock(side_effect=[b"first", OSError("Synthetic source read failure")])
        handler = self.handler(Mock(return_value=(handle, 12, "synthetic-sha")))
        handler.reply = Mock()
        handler.do_GET()
        handler.send_response.assert_called_once_with(200)
        handler.reply.assert_not_called()
        self.assertEqual(handler.wfile.getvalue(), b"first")
        self.assertTrue(handler.close_connection)
        self.assertTrue(handle.closed)

    def test_asset_failure_before_headers_preserves_json_error(self):
        for error, status, code in [
            (WorkbenchError("Synthetic invalid asset", status=503, code="invalid_preview_asset"), 503, "invalid_preview_asset"),
            (OSError("Synthetic unavailable asset"), 500, "read_failed"),
        ]:
            with self.subTest(code=code):
                binary = Mock(side_effect=error)
                handler = self.handler(binary)
                handler.do_GET()
                binary.assert_called_once_with("synthetic-asset")
                handler.send_response.assert_called_once_with(status)
                body = json.loads(handler.wfile.getvalue())
                self.assertEqual(body["error"], code)
                self.assertFalse(handler.close_connection)


if __name__ == "__main__":
    unittest.main()
