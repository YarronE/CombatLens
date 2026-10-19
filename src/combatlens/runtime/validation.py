"""Validate the editable surface without accepting changes to evidence."""
from __future__ import annotations

import copy
import json
import math
import re

ANALYSIS_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
SOURCE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
UNITS = {None, "seconds", "frames", "game_seconds", "source_units"}


class WorkbenchError(Exception):
    def __init__(self, message, status=400, code="invalid_request", **details):
        super().__init__(message)
        self.status = status
        self.code = code
        self.details = details

    def payload(self):
        return {"error": self.code, "message": str(self), **self.details}


def canonical(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (ValueError, TypeError, RecursionError) as error:
        raise WorkbenchError("JSON contains an invalid or non-finite value.") from error


def json_equivalent(left, right):
    """Compare JSON values; browsers serialize integral numbers without '.0'."""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is bool and type(right) is bool and left == right
    if isinstance(left, (int, float)) or isinstance(right, (int, float)):
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            return False
        try:
            return math.isfinite(left) and math.isfinite(right) and left == right
        except OverflowError:
            return False
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(json_equivalent(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(json_equivalent(a, b) for a, b in zip(left, right))
    return left == right


def revision(value, label="revision"):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise WorkbenchError(f"{label} must be a non-negative integer.")
    return value


def finite(value, label):
    if value is None:
        return
    try:
        valid = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise WorkbenchError(f"{label} must be null or a finite number.")


def finite_json(value, label="parameters", depth=0):
    if depth > 100:
        raise WorkbenchError(f"{label} exceeds the supported nesting depth.")
    if isinstance(value, float) or isinstance(value, int) and not isinstance(value, bool):
        finite(value, label)
    elif isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise WorkbenchError(f"{label} keys must be strings.")
        for item in value.values():
            finite_json(item, label, depth + 1)
    elif isinstance(value, list):
        for item in value:
            finite_json(item, label, depth + 1)
    elif value is not None and not isinstance(value, (str, bool)):
        raise WorkbenchError(f"{label} must be JSON.")


def validate_override(override, event_id):
    if override is None:
        return
    if not isinstance(override, dict):
        raise WorkbenchError(f"Override for {event_id} must be an object or null.")
    required = {"start", "end", "unit", "note", "reason", "timing_status"}
    if not required <= set(override) or set(override) - required - {"parameters", "deleted"}:
        raise WorkbenchError(f"Override for {event_id} has missing or unsupported fields.")
    for key in ("start", "end"):
        finite(override[key], f"{event_id}.{key}")
    if override["unit"] not in UNITS:
        raise WorkbenchError(f"Unsupported time unit for {event_id}.")
    start, end = override["start"], override["end"]
    if end is not None and start is None:
        raise WorkbenchError(f"An interval end requires a start for {event_id}.")
    if start is not None and end is not None and end < start:
        raise WorkbenchError(f"Interval end precedes start for {event_id}.")
    if start is not None and override["unit"] is None:
        raise WorkbenchError(f"A proposed time requires an explicit unit for {event_id}.")
    if override["timing_status"] != "analyst_hypothesis":
        raise WorkbenchError(f"An override must remain an analyst hypothesis for {event_id}.")
    for key in ("note", "reason"):
        if not isinstance(override[key], str) or len(override[key]) > 10_000:
            raise WorkbenchError(f"{event_id}.{key} must be text of at most 10000 characters.")
    if not override["reason"].strip():
        raise WorkbenchError(f"An override needs a reason for {event_id}.")
    if "parameters" in override:
        finite_json(override["parameters"])
    if "deleted" in override and not isinstance(override["deleted"], bool):
        raise WorkbenchError(f"deleted must be a boolean for {event_id}.")


def validate_analysis_event(event):
    if not isinstance(event, dict):
        raise WorkbenchError("Analysis events must be objects.")
    required = {"id", "label", "kind", "track", "start", "end", "unit", "note", "reason", "parameters", "timing_status"}
    if not required <= set(event) or set(event) - required - {"source_ids"}:
        raise WorkbenchError("Analysis event has missing or unsupported fields.")
    if not isinstance(event["id"], str) or not re.fullmatch(r"analysis-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", event["id"]):
        raise WorkbenchError("New analysis events require an analysis-UUID ID.")
    if event["kind"] != "analysis_event":
        raise WorkbenchError("New events must remain analysis_event records.")
    for key in ("label", "track"):
        if not isinstance(event[key], str) or not event[key].strip() or len(event[key]) > 200:
            raise WorkbenchError(f"Analysis event {key} must be non-empty text.")
    validate_override({key: event[key] for key in ("start", "end", "unit", "note", "reason", "timing_status", "parameters")}, event["id"])


def original_objects(objects, validate=False):
    if not isinstance(objects, list):
        raise WorkbenchError("objects must be an array.")
    result = copy.deepcopy(objects)
    event_ids = set()
    try:
        for obj in result:
            for sequence in obj["sequences"]:
                additions = sequence.pop("analysis_events", [])
                if not isinstance(additions, list):
                    raise WorkbenchError("analysis_events must be an array.")
                if validate:
                    for addition in additions:
                        validate_analysis_event(addition)
                        if addition["id"] in event_ids:
                            raise WorkbenchError("Analysis event IDs must be unique.")
                        event_ids.add(addition["id"])
                for event in sequence["events"]:
                    event_id = event["id"]
                    if not isinstance(event_id, str) or event_id in event_ids:
                        raise WorkbenchError("Event IDs must be unique strings.")
                    event_ids.add(event_id)
                    if validate:
                        validate_override(event.get("analysis_override"), event_id)
                    event["analysis_override"] = None
    except (KeyError, TypeError) as error:
        raise WorkbenchError("Malformed object, sequence or event structure.") from error
    return result


def source_ids(value):
    """Read references only; never interpret locators or paths as write targets."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "source_ids":
                if not isinstance(item, list) or any(not isinstance(sid, str) for sid in item):
                    raise WorkbenchError("source_ids must be an array of strings.")
                yield from item
            elif key not in {"parameters", "raw_value", "locator", "analysis_override"}:
                yield from source_ids(item)
    elif isinstance(value, list):
        for item in value:
            yield from source_ids(item)


def validate_analysis(analysis, timelines, fingerprint, registered_ids):
    if not isinstance(analysis, dict):
        raise WorkbenchError("analysis must be an object.")
    allowed = {"schema_version", "analysis_id", "name", "revision", "game_build", "parent_package_fingerprint", "objects", "saved_at", "validity"}
    if set(analysis) - allowed:
        raise WorkbenchError("Analysis contains unsupported top-level fields.")
    if analysis.get("schema_version") != "timeline-analysis/1":
        raise WorkbenchError("Unsupported analysis schema.", code="schema_mismatch")
    analysis_id = analysis.get("analysis_id")
    if not isinstance(analysis_id, str) or not ANALYSIS_ID.fullmatch(analysis_id):
        raise WorkbenchError("Invalid analysis ID.")
    name = analysis.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 200:
        raise WorkbenchError("Analysis name must be non-empty text of at most 200 characters.")
    rev = revision(analysis.get("revision"))
    if analysis.get("game_build") != timelines["game_build"]:
        raise WorkbenchError("Analysis Build differs from the current source.", code="build_mismatch")
    if analysis.get("parent_package_fingerprint") != fingerprint:
        raise WorkbenchError("The parent research package changed; reopen sources before saving.", status=409, code="stale_package", current_package_fingerprint=fingerprint)
    stripped = original_objects(analysis.get("objects"), validate=True)
    if not json_equivalent(stripped, original_objects(timelines["objects"])):
        raise WorkbenchError("Original objects, graph, events and source values are read-only.", code="original_modified")
    unknown = sorted(set(source_ids(analysis["objects"])) - set(registered_ids))
    if unknown:
        raise WorkbenchError("Analysis references unregistered sources.", code="unknown_source", source_ids=unknown)
    # Construct the saved document from server-owned originals and accepted overrides.
    objects = copy.deepcopy(timelines["objects"])
    for original_obj, proposed_obj in zip(objects, analysis["objects"]):
        for original_seq, proposed_seq in zip(original_obj["sequences"], proposed_obj["sequences"]):
            original_seq["analysis_events"] = copy.deepcopy(proposed_seq.get("analysis_events", []))
            for original_event, proposed_event in zip(original_seq["events"], proposed_seq["events"]):
                original_event["analysis_override"] = copy.deepcopy(proposed_event.get("analysis_override"))
    return {"schema_version": "timeline-analysis/1", "analysis_id": analysis_id, "name": name.strip(), "revision": rev, "game_build": timelines["game_build"], "parent_package_fingerprint": fingerprint, "objects": objects}
