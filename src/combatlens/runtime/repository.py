"""Registered read-only evidence and atomic, revisioned analysis copies."""
from __future__ import annotations

import copy
import gzip
import hashlib
import json
import os
import tempfile
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .validation import ANALYSIS_ID, SOURCE_ID, WorkbenchError, canonical, revision, source_ids, validate_analysis


def read_json(path):
    try:
        data = path.read_bytes()
        value = json.loads(data.decode("utf-8-sig"), parse_constant=lambda name: (_ for _ in ()).throw(ValueError(name)))
        return value, data
    except FileNotFoundError as error:
        raise WorkbenchError(f"Local data is not available: {path.name}", status=503, code="data_unavailable") from error
    except (UnicodeError, ValueError, RecursionError) as error:
        raise WorkbenchError(f"Invalid JSON in {path.name}", status=503, code="invalid_local_data") from error


def digest(data):
    return hashlib.sha256(data).hexdigest()


def within(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class Config:
    repo_root: Path
    research_dir: Path | None = None
    analyses_dir: Path | None = None
    max_request_bytes: int = 16 * 1024 * 1024
    max_source_preview_bytes: int = 2 * 1024 * 1024

    def paths(self):
        root = self.repo_root.resolve()
        research = (self.research_dir or root / "local/research").resolve()
        pointer = root / "local/research/active-source.json"
        if self.research_dir is None and pointer.exists():
            selected = read_json(pointer)[0]
            relative = selected.get("relative_directory") if isinstance(selected, dict) else None
            if not isinstance(relative, str) or selected.get("schema_version") != "research-pointer/1":
                raise WorkbenchError("Invalid local research pointer.", status=503, code="invalid_research_pointer")
            research = (root / "local/research" / relative).resolve()
            if not within(research, (root / "local/research").resolve()):
                raise WorkbenchError("Active research must stay in this project.", status=403, code="unsafe_research_root")
        analyses = (self.analyses_dir or root / "local/analyses").resolve()
        if not within(analyses, root / "local"):
            raise WorkbenchError("Analysis writes must remain under this project's local directory.", code="unsafe_analysis_root")
        return root, research, analyses


class Repository:
    def __init__(self, config):
        self.config = config
        self.root, self.research_dir, self.analyses_dir = config.paths()
        self.lock = threading.RLock()
        self.hash_cache = {}

    def research(self):
        value, raw = read_json(self.research_dir / "research-package.json")
        if not isinstance(value, dict) or type(value.get("schema_version")) is not int or value.get("schema_version") != 1 or not isinstance(value.get("sources"), list):
            raise WorkbenchError("Unsupported research package schema.", status=503, code="schema_mismatch")
        ids = [source.get("id") for source in value["sources"] if isinstance(source, dict)]
        if len(ids) != len(value["sources"]) or any(not isinstance(sid, str) or not SOURCE_ID.fullmatch(sid) for sid in ids) or len(set(ids)) != len(ids):
            raise WorkbenchError("Research sources require unique registered IDs.", status=503, code="invalid_source_registry")
        return value, digest(raw)

    def timelines(self, fingerprint=None):
        value, _ = read_json(self.research_dir / "timelines.json")
        if not isinstance(value, dict) or value.get("schema_version") != "timeline-source/1" or not isinstance(value.get("objects"), list) or not isinstance(value.get("game_build"), str):
            raise WorkbenchError("Unsupported Timeline source schema.", status=503, code="schema_mismatch")
        if fingerprint is None:
            _, fingerprint = self.research()
        if value.get("package_fingerprint") != fingerprint:
            raise WorkbenchError("Timeline attachment does not match the current research package.", status=503, code="stale_timeline_attachment")
        return value

    def registry(self, package=None):
        if package is None:
            package, _ = self.research()
        registry_path = self.research_dir / "source-root.json"
        trusted = read_json(registry_path)[0] if registry_path.exists() else {}
        if not isinstance(trusted, dict):
            raise WorkbenchError("Invalid trusted source configuration.", status=503, code="invalid_source_registry")
        roots = trusted.get("allowed_roots", [trusted.get("root", str(self.research_dir))])
        if not isinstance(roots, list) or any(not isinstance(root, str) for root in roots):
            raise WorkbenchError("Invalid trusted source roots.", status=503, code="invalid_source_registry")
        approved = [Path(root).resolve() for root in roots]
        explicit = trusted.get("sources", {})
        if not isinstance(explicit, dict):
            raise WorkbenchError("Invalid trusted source mapping.", status=503, code="invalid_source_registry")
        records = {}
        for source in package["sources"]:
            sid = source["id"]
            mapped = explicit.get(sid, {})
            if isinstance(mapped, str):
                mapped = {"path": mapped}
            if not isinstance(mapped, dict):
                raise WorkbenchError("Invalid registered source entry.", status=503, code="invalid_source_registry")
            path_text = mapped.get("path") or source.get("snapshot_path") or source.get("local_path") or source.get("path")
            expected = source.get("sha256")
            if "sha256" in mapped and mapped["sha256"] != expected:
                raise WorkbenchError("Source registry hash conflicts with its research package.", status=503, code="invalid_source_registry")
            base_root = Path(trusted.get("root", str(self.research_dir))).resolve()
            records[sid] = {"source": source, "path_text": path_text, "expected_sha256": expected, "approved_roots": approved, "base_root": base_root}
        return records

    def source_path(self, record):
        text = record["path_text"]
        if not isinstance(text, str) or not text or "\x00" in text or "://" in text:
            raise WorkbenchError("This source has no registered local snapshot.", status=404, code="source_unavailable")
        path = Path(text)
        if not path.is_absolute():
            path = record["base_root"] / path
        path = path.resolve()
        if not any(within(path, root) for root in record["approved_roots"]):
            raise WorkbenchError("Registered source resolves outside approved roots.", status=403, code="source_path_rejected")
        if not path.is_file():
            raise WorkbenchError("Registered source snapshot is missing.", status=404, code="source_missing")
        return path

    def source_status(self, record):
        expected = record["expected_sha256"]
        try:
            path = self.source_path(record)
            stat = path.stat()
            key = (str(path), stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size)
            actual = self.hash_cache.get(key)
            if actual is None:
                sha = hashlib.sha256()
                with path.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        sha.update(chunk)
                actual = sha.hexdigest()
                self.hash_cache[key] = actual
            status = "current" if expected == actual else "changed" if expected else "unverified"
            return {"status": status, "sha256": actual, "expected_sha256": expected, "bytes": stat.st_size}
        except WorkbenchError as error:
            return {"status": "missing" if error.code == "source_missing" else "unavailable", "expected_sha256": expected, "message": str(error)}
        except OSError as error:
            return {"status": "unavailable", "expected_sha256": expected, "message": str(error)}

    def validity(self, objects=None, analysis=None):
        package, fingerprint = self.research()
        records = self.registry(package)
        statuses = {sid: self.source_status(record) for sid, record in records.items()}
        stale_ids = {sid for sid, state in statuses.items() if state["status"] != "current"}
        affected = []
        for obj in objects or []:
            for seq in obj.get("sequences", []):
                for event in seq.get("events", []) + seq.get("analysis_events", []):
                    dependencies = set(source_ids(event)) | set(source_ids(seq.get("origin", {}))) | set(seq.get("source_ids", [])) | set(obj.get("source_ids", []))
                    if dependencies & stale_ids:
                        affected.append(event["id"])
        result = {"sources": statuses, "stale_source_ids": sorted(stale_ids), "affected_event_ids": affected, "current_package_fingerprint": fingerprint}
        if analysis:
            result["stale_package"] = analysis.get("parent_package_fingerprint") != fingerprint
            try:
                result["stale_build"] = analysis.get("game_build") != self.timelines(fingerprint)["game_build"]
            except WorkbenchError:
                result["stale_build"] = None
        return result

    def research_response(self):
        value, _ = self.research()
        response = copy.deepcopy(value)
        response["validity"] = self.validity()
        return response

    def timelines_response(self):
        value = self.timelines()
        response = copy.deepcopy(value)
        response["validity"] = self.validity(value["objects"])
        return response

    def source(self, sid):
        if not SOURCE_ID.fullmatch(sid):
            raise WorkbenchError("Invalid source ID.")
        records = self.registry()
        if sid not in records:
            raise WorkbenchError("Unknown source ID.", status=404, code="unknown_source")
        record = records[sid]
        path = self.source_path(record)
        encoding = "gzip" if path.suffix.lower() == ".gz" else "identity"
        opener = gzip.open if encoding == "gzip" else lambda filename, mode: filename.open(mode)
        with opener(path, "rb") as handle:
            raw = handle.read(self.config.max_source_preview_bytes + 1)
        truncated = len(raw) > self.config.max_source_preview_bytes
        raw = raw[:self.config.max_source_preview_bytes]
        content = None
        kind = "binary"
        try:
            text = raw.decode("utf-8-sig")
            if "\x00" not in text:
                kind = "text"
                content = text
                if not truncated and (path.suffix.lower() == ".json" or path.name.lower().endswith(".json.gz")):
                    content = json.loads(text, parse_constant=lambda name: (_ for _ in ()).throw(ValueError(name)))
                    kind = "json"
        except (UnicodeError, ValueError):
            pass
        return {"source_id": sid, "source": record["source"], "path": str(path), "validity": self.source_status(record), "content_kind": kind, "content_encoding": encoding, "content": content, "preview_hex": raw[:64].hex() if kind == "binary" else None, "preview_truncated": truncated}

    def analysis_path(self, analysis_id):
        if not isinstance(analysis_id, str) or not ANALYSIS_ID.fullmatch(analysis_id):
            raise WorkbenchError("Invalid analysis ID.")
        path = self.analyses_dir / (analysis_id + ".json")
        if not within(path.resolve(), self.analyses_dir) or not within(self.analyses_dir.resolve(), self.root / "local"):
            raise WorkbenchError("Unsafe analysis path.", code="path_rejected")
        return path

    def analyses(self):
        results = []
        if self.analyses_dir.exists():
            for path in sorted(self.analyses_dir.glob("*.json")):
                if not ANALYSIS_ID.fullmatch(path.stem):
                    continue
                safe = self.analysis_path(path.stem)
                try:
                    value, _ = read_json(safe)
                    if value.get("schema_version") == "timeline-analysis/1" and value.get("analysis_id") == path.stem:
                        results.append({key: value.get(key) for key in ("analysis_id", "name", "revision", "saved_at")} | {"path": str(safe)})
                except (WorkbenchError, AttributeError):
                    continue
        return {"analyses": results}

    def analysis(self, analysis_id):
        path = self.analysis_path(analysis_id)
        if not path.exists():
            raise WorkbenchError("Analysis was not found.", status=404, code="analysis_missing")
        value, _ = read_json(path)
        if not isinstance(value, dict) or value.get("schema_version") != "timeline-analysis/1" or value.get("analysis_id") != analysis_id:
            raise WorkbenchError("Saved analysis has an unsupported schema or identity.", status=409, code="invalid_saved_analysis")
        response = copy.deepcopy(value)
        try:
            response["validity"] = self.validity(value.get("objects"), value)
        except WorkbenchError as error:
            response["validity"] = {"unavailable": True, "message": str(error), "stale_package": None, "stale_build": None}
        return response

    def _atomic_write(self, path, data):
        self.analyses_dir.mkdir(parents=True, exist_ok=True)
        temp_path = None
        backup_temp = None
        try:
            with tempfile.NamedTemporaryFile(prefix=".save-", suffix=".tmp", dir=self.analyses_dir, delete=False) as handle:
                temp_path = Path(handle.name)
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            if path.exists():
                with tempfile.NamedTemporaryFile(prefix=".backup-", suffix=".tmp", dir=self.analyses_dir, delete=False) as handle:
                    backup_temp = Path(handle.name)
                    handle.write(path.read_bytes())
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(backup_temp, path.with_suffix(".json.bak"))
                backup_temp = None
            os.replace(temp_path, path)
            temp_path = None
        finally:
            for temporary in (temp_path, backup_temp):
                if temporary is not None and temporary.exists():
                    temporary.unlink()

    def save(self, body):
        if not isinstance(body, dict) or set(body) != {"expected_revision", "analysis"}:
            raise WorkbenchError("Save needs expected_revision and analysis.")
        expected = revision(body["expected_revision"], "expected_revision")
        with self.lock:
            package, fingerprint = self.research()
            originals = self.timelines(fingerprint)
            accepted = validate_analysis(body["analysis"], originals, fingerprint, self.registry(package))
            if accepted["revision"] != expected:
                raise WorkbenchError("Payload revision differs from expected_revision.")
            path = self.analysis_path(accepted["analysis_id"])
            current = read_json(path)[0] if path.exists() else None
            latest = revision(current.get("revision")) if current else 0
            if latest != expected:
                raise WorkbenchError("Another window saved a newer revision.", status=409, code="revision_conflict", latest_revision=latest)
            if current and (current.get("schema_version") != "timeline-analysis/1" or current.get("analysis_id") != accepted["analysis_id"]):
                raise WorkbenchError("Existing analysis identity is invalid.", status=409, code="invalid_saved_analysis")
            accepted["revision"] = latest + 1
            accepted["saved_at"] = datetime.now(timezone.utc).isoformat()
            data = (json.dumps(accepted, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
            try:
                self._atomic_write(path, data)
            except OSError as error:
                raise WorkbenchError("Analysis save failed; the previous file remains intact.", status=500, code="save_failed", detail=str(error)) from error
            return {"analysis_id": accepted["analysis_id"], "revision": accepted["revision"], "sha256": digest(data), "path": str(path), "saved_at": accepted["saved_at"], "analysis": accepted}
