#!/usr/bin/env python3
"""Actionstep API client. OAuth 2.0 auth code flow, dynamic api_endpoint, wrapped body format."""

import ipaddress
import json
import os
import sys
import time
import urllib.parse
import requests
from pathlib import Path
from datetime import datetime, timezone

AUTH_BASE = "https://go.actionstep.com"
REDIRECT_URI = "http://127.0.0.1:8769/callback"
TOKEN_URL = f"{AUTH_BASE}/oauth/token"
AUTH_URL = f"{AUTH_BASE}/oauth/authorize"

CONFIG_DIR = Path.home() / ".actionstep-mcp"
API_PREFIX = "/api/rest"

# Private/reserved address ranges that must not receive webhook payloads (SSRF hygiene).
_PRIVATE_NETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _validate_webhook_url(url: str) -> None:
    """Raise ValueError if url is not a safe https endpoint for webhook delivery.

    Enforces:
    - scheme must be https (prevents cleartext delivery)
    - hostname must not resolve to a private, loopback, or link-local address
      (prevents SSRF — Actionstep posting matter data to an internal service)

    Note: this is a best-effort syntactic check on the literal hostname.  DNS
    resolution at call time is not performed; a split-horizon DNS attack or a
    hostname that resolves differently at Actionstep's side is out of scope.
    """
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(
            f"Webhook target_url must use https (got '{parsed.scheme}'). "
            "Plain-http endpoints would receive Actionstep matter data unencrypted."
        )
    hostname = parsed.hostname or ""
    if not hostname:
        raise ValueError("Webhook target_url must include a hostname.")
    # Reject bare IP addresses in private ranges
    try:
        addr = ipaddress.ip_address(hostname)
        for net in _PRIVATE_NETS:
            if addr in net:
                raise ValueError(
                    f"Webhook target_url hostname '{hostname}' is a private/loopback/"
                    "link-local address. Webhooks must target a firm-controlled public endpoint."
                )
    except ValueError as exc:
        # Re-raise our own ValueError; non-IP hostnames (domain names) pass through
        if "private" in str(exc) or "loopback" in str(exc) or "link-local" in str(exc):
            raise
    # Reject well-known loopback/internal hostnames
    _BLOCKED_HOSTS = {"localhost", "local", "internal", "metadata.google.internal"}
    if hostname.lower() in _BLOCKED_HOSTS or hostname.lower().endswith(".local"):
        raise ValueError(
            f"Webhook target_url hostname '{hostname}' is a reserved/internal hostname. "
            "Webhooks must target a firm-controlled public endpoint."
        )


def _load_env():
    env_file = CONFIG_DIR / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())


_load_env()

CLIENT_ID = os.environ.get("ACTIONSTEP_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ACTIONSTEP_CLIENT_SECRET", "")
API_ENDPOINT = os.environ.get("ACTIONSTEP_API_ENDPOINT", "")


def _retry_after_seconds(resp, default=10):
    try:
        return int(resp.headers.get("Retry-After", default))
    except (TypeError, ValueError):
        return default


def _json_response(resp):
    try:
        return resp.json()
    except ValueError:
        raise RuntimeError(
            f"Actionstep API returned non-JSON response ({resp.status_code}): "
            f"{resp.text[:200]}"
        )


class TokenManager:
    def __init__(self):
        self.token_file = CONFIG_DIR / "tokens.json"
        self.tokens = self._load()

    def _load(self):
        if self.token_file.exists():
            with open(self.token_file) as f:
                return json.load(f)
        return {}

    def save(self, tokens):
        self.tokens = tokens
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.token_file, "w") as f:
            json.dump(tokens, f, indent=2)
        os.chmod(self.token_file, 0o600)

    @property
    def access_token(self):
        return self.tokens.get("access_token", "")

    @property
    def refresh_token(self):
        return self.tokens.get("refresh_token", "")

    def refresh(self):
        if not self.refresh_token:
            raise RuntimeError("No refresh token. Run: actionstep-mcp-setup")
        if not CLIENT_ID or not CLIENT_SECRET:
            raise RuntimeError(
                "ACTIONSTEP_CLIENT_ID and ACTIONSTEP_CLIENT_SECRET are required. Run: actionstep-mcp-setup"
            )
        resp = requests.post(
            TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
        )
        if resp.status_code == 200:
            new_tokens = _json_response(resp)
            if "refresh_token" not in new_tokens:
                new_tokens["refresh_token"] = self.refresh_token
            new_tokens["refreshed_at"] = datetime.now(timezone.utc).isoformat()
            # Preserve api_endpoint if not returned again
            if "api_endpoint" not in new_tokens and "api_endpoint" in self.tokens:
                new_tokens["api_endpoint"] = self.tokens["api_endpoint"]
            self.save(new_tokens)
            return new_tokens
        raise RuntimeError(f"Token refresh failed ({resp.status_code}): {resp.text}")


class ActionstepClient:
    def __init__(self):
        self.tm = TokenManager()
        # api_endpoint: env var takes priority, then token, then error
        self.api_endpoint = (
            API_ENDPOINT or self.tm.tokens.get("api_endpoint", "")
        ).rstrip("/")
        if not self.api_endpoint:
            raise RuntimeError(
                "ACTIONSTEP_API_ENDPOINT not set. Run: actionstep-mcp-setup"
            )
        if not self.tm.access_token and not self.tm.refresh_token:
            raise RuntimeError(
                "No Actionstep OAuth tokens found. Run: actionstep-mcp-setup"
            )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.tm.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _url(self, path):
        return f"{self.api_endpoint}{API_PREFIX}/{path.lstrip('/')}"

    def _request(
        self, method, path, params=None, json_body=None, retry=True, _rate_retries=0
    ):
        url = self._url(path)
        resp = self.session.request(method, url, params=params, json=json_body)

        if resp.status_code == 401 and retry:
            self.tm.refresh()
            self.session.headers["Authorization"] = f"Bearer {self.tm.access_token}"
            return self._request(
                method, path, params=params, json_body=json_body, retry=False
            )

        if resp.status_code == 429 and _rate_retries < 3:
            retry_after = _retry_after_seconds(resp)
            print(f"Rate limited. Waiting {retry_after}s...", file=sys.stderr)
            time.sleep(retry_after)
            return self._request(
                method,
                path,
                params=params,
                json_body=json_body,
                retry=retry,
                _rate_retries=_rate_retries + 1,
            )

        if resp.status_code in (204, 200) and not resp.content:
            return {"success": True}

        if not resp.ok:
            raise RuntimeError(
                f"Actionstep API error {resp.status_code}: {resp.text[:400]}"
            )

        return _json_response(resp)

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def post(self, path, resource_key, data):
        return self._request("POST", path, json_body={resource_key: data})

    def put(self, path, resource_key, data):
        return self._request("PUT", path, json_body={resource_key: data})

    def delete(self, path):
        return self._request("DELETE", path)

    # ── Users ─────────────────────────────────────────────────────────────────

    def get_current_user(self):
        return self.get("users/current")

    def list_users(self):
        return self.get("users")

    def get_user(self, user_id):
        return self.get(f"users/{user_id}")

    # ── Actions (Matters) ─────────────────────────────────────────────────────

    def list_actions(self, action_type=None, status=None, limit=50, page=1):
        params = {"page": page, "pageSize": limit}
        if action_type:
            params["actiontype"] = action_type
        if status:
            params["status"] = status
        return self.get("actions", params)

    def get_action(self, action_id):
        return self.get(f"actions/{action_id}")

    def create_action(self, name, action_type_id, **fields):
        # Actionstep uses /actioncreate/{action_type_id} for creation,
        # with key "actioncreate" and field "actionName".
        data = {"actionName": name, "links": {"actionType": str(action_type_id)}}
        if "links" in fields:
            data["links"].update(fields.pop("links"))
        data.update(fields)
        return self.post(f"actioncreate/{action_type_id}", "actioncreate", data)

    def update_action(self, action_id, **fields):
        return self.put(f"actions/{action_id}", "actions", fields)

    # ── Action Types ──────────────────────────────────────────────────────────

    def list_action_types(self, is_billable=None):
        params = {}
        if is_billable is not None:
            params["isBillable"] = "T" if is_billable else "F"
        return self.get("actiontypes", params)

    def get_action_type(self, action_type_id):
        return self.get(f"actiontypes/{action_type_id}")

    # ── Action Bill Settings ──────────────────────────────────────────────────

    def list_action_bill_settings(self, action_id=None):
        params = {}
        if action_id:
            params["action"] = action_id
        return self.get("actionbillsettings", params)

    def get_action_bill_settings(self, settings_id):
        return self.get(f"actionbillsettings/{settings_id}")

    def update_action_bill_settings(self, settings_id, **fields):
        return self.put(
            f"actionbillsettings/{settings_id}", "actionbillsettings", fields
        )

    # ── Action Change Steps ───────────────────────────────────────────────────

    def list_action_change_steps(self, action_id=None):
        params = {}
        if action_id:
            params["action"] = action_id
        return self.get("actionchangestep", params)

    def create_action_change_step(self, action_id, step_id, node_id=None):
        """Transition an action to a new workflow step (POST to actionchangestep)."""
        links = {"action": str(action_id), "step": str(step_id)}
        if node_id:
            links["node"] = str(node_id)
        return self.post("actionchangestep", "actionchangestep", {"links": links})

    # ── Action Documents ──────────────────────────────────────────────────────

    def list_action_documents(self, action_id=None):
        params = {}
        if action_id:
            params["action"] = action_id
        return self.get("actiondocuments", params)

    def get_action_document(self, document_id):
        return self.get(f"actiondocuments/{document_id}")

    def create_action_document(self, action_id, **fields):
        # Note: API uses "name" for the document name (not "fileName")
        data = {"links": {"action": str(action_id)}}
        if "links" in fields:
            data["links"].update(fields.pop("links"))
        # Remap fileName -> name if passed
        if "fileName" in fields:
            fields["name"] = fields.pop("fileName")
        data.update(fields)
        return self.post("actiondocuments", "actiondocuments", data)

    def update_action_document(self, document_id, **fields):
        return self.put(f"actiondocuments/{document_id}", "actiondocuments", fields)

    def delete_action_document(self, document_id):
        return self.delete(f"actiondocuments/{document_id}")

    # ── Action Folders ────────────────────────────────────────────────────────

    def list_action_folders(self, action_id=None):
        params = {}
        if action_id:
            params["action"] = action_id
        return self.get("actionfolders", params)

    def get_action_folder(self, folder_id):
        return self.get(f"actionfolders/{folder_id}")

    def create_action_folder(self, action_id, name):
        return self.post(
            "actionfolders",
            "actionfolders",
            {"name": name, "links": {"action": str(action_id)}},
        )

    def update_action_folder(self, folder_id, **fields):
        return self.put(f"actionfolders/{folder_id}", "actionfolders", fields)

    def delete_action_folder(self, folder_id):
        return self.delete(f"actionfolders/{folder_id}")

    # ── Action Participants ───────────────────────────────────────────────────

    def list_action_participants(self, action_id=None):
        params = {}
        if action_id:
            params["action"] = action_id
        return self.get("actionparticipants", params)

    def get_action_participant(self, ap_id):
        return self.get(f"actionparticipants/{ap_id}")

    def create_action_participant(self, action_id, participant_id, participant_type_id):
        data = {
            "links": {
                "action": str(action_id),
                "participant": str(participant_id),
                "participantType": str(participant_type_id),
            }
        }
        return self.post("actionparticipants", "actionparticipants", data)

    def update_action_participant(self, ap_id, **fields):
        return self.put(f"actionparticipants/{ap_id}", "actionparticipants", fields)

    def delete_action_participant(self, ap_id):
        return self.delete(f"actionparticipants/{ap_id}")

    # ── Action Permissions ────────────────────────────────────────────────────

    def list_action_permissions(self, action_id=None):
        params = {}
        if action_id:
            params["action"] = action_id
        return self.get("actionpermissions", params)

    def update_action_permissions(self, perm_id, **fields):
        return self.put(f"actionpermissions/{perm_id}", "actionpermissions", fields)

    # ── Action Rates ──────────────────────────────────────────────────────────

    def list_action_rates(self, action_id=None):
        params = {}
        if action_id:
            params["action"] = action_id
        return self.get("actionrates", params)

    def get_action_rate(self, rate_id):
        return self.get(f"actionrates/{rate_id}")

    def create_action_rate(self, action_id, **fields):
        data = {"links": {"action": str(action_id)}}
        if "links" in fields:
            data["links"].update(fields.pop("links"))
        data.update(fields)
        return self.post("actionrates", "actionrates", data)

    def update_action_rate(self, rate_id, **fields):
        return self.put(f"actionrates/{rate_id}", "actionrates", fields)

    def delete_action_rate(self, rate_id):
        return self.delete(f"actionrates/{rate_id}")

    # ── Action Type Folders ───────────────────────────────────────────────────

    def list_action_type_folders(self, action_type_id=None):
        params = {}
        if action_type_id:
            params["actionType"] = action_type_id
        return self.get("actiontypefolders", params)

    def get_action_type_folder(self, folder_id):
        return self.get(f"actiontypefolders/{folder_id}")

    def create_action_type_folder(self, action_type_id, name):
        return self.post(
            "actiontypefolders",
            "actiontypefolders",
            {"name": name, "links": {"actionType": str(action_type_id)}},
        )

    def update_action_type_folder(self, folder_id, **fields):
        return self.put(f"actiontypefolders/{folder_id}", "actiontypefolders", fields)

    def delete_action_type_folder(self, folder_id):
        return self.delete(f"actiontypefolders/{folder_id}")

    # ── Participants (Contacts) ───────────────────────────────────────────────

    def list_participants(self, page=1, limit=50):
        return self.get("participants", {"page": page, "pageSize": limit})

    def get_participant(self, participant_id):
        return self.get(f"participants/{participant_id}")

    def create_participant(
        self, first_name="", last_name="", company_name="", is_company=False, **fields
    ):
        data = {"isCompany": "T" if is_company else "F", **fields}
        if first_name:
            data["firstName"] = first_name
        if last_name:
            data["lastName"] = last_name
        if company_name:
            data["companyName"] = company_name
        return self.post("participants", "participants", data)

    def update_participant(self, participant_id, **fields):
        return self.put(f"participants/{participant_id}", "participants", fields)

    def delete_participant(self, participant_id):
        return self.delete(f"participants/{participant_id}")

    # ── Participant Types ─────────────────────────────────────────────────────

    def list_participant_types(self):
        return self.get("participanttypes")

    def get_participant_type(self, pt_id):
        return self.get(f"participanttypes/{pt_id}")

    def create_participant_type(self, name, **fields):
        return self.post(
            "participanttypes", "participanttypes", {"name": name, **fields}
        )

    def update_participant_type(self, pt_id, **fields):
        return self.put(f"participanttypes/{pt_id}", "participanttypes", fields)

    # ── Participant Relationship Types ────────────────────────────────────────

    def list_participant_relationship_types(self):
        return self.get("participantrelationshiptypes")

    def get_participant_relationship_type(self, rt_id):
        return self.get(f"participantrelationshiptypes/{rt_id}")

    def create_participant_relationship_type(self, name, **fields):
        return self.post(
            "participantrelationshiptypes",
            "participantrelationshiptypes",
            {"name": name, **fields},
        )

    def update_participant_relationship_type(self, rt_id, **fields):
        return self.put(
            f"participantrelationshiptypes/{rt_id}",
            "participantrelationshiptypes",
            fields,
        )

    # ── Contact Relationships ─────────────────────────────────────────────────

    def list_contact_relationships(self, participant_id=None):
        params = {}
        if participant_id:
            params["participant"] = participant_id
        return self.get("contactrelationships", params)

    def get_contact_relationship(self, cr_id):
        return self.get(f"contactrelationships/{cr_id}")

    def create_contact_relationship(
        self, participant1_id, participant2_id, relationship_type_id
    ):
        data = {
            "links": {
                "participant1": str(participant1_id),
                "participant2": str(participant2_id),
                "participantRelationshipType": str(relationship_type_id),
            }
        }
        return self.post("contactrelationships", "contactrelationships", data)

    def update_contact_relationship(self, cr_id, **fields):
        return self.put(f"contactrelationships/{cr_id}", "contactrelationships", fields)

    # ── Contact Documents ─────────────────────────────────────────────────────

    def list_contact_documents(self, participant_id=None):
        params = {}
        if participant_id:
            params["participant"] = participant_id
        return self.get("contactdocuments", params)

    def get_contact_document(self, doc_id):
        return self.get(f"contactdocuments/{doc_id}")

    def create_contact_document(self, participant_id, **fields):
        data = {"links": {"participant": str(participant_id)}, **fields}
        return self.post("contactdocuments", "contactdocuments", data)

    def update_contact_document(self, doc_id, **fields):
        return self.put(f"contactdocuments/{doc_id}", "contactdocuments", fields)

    def delete_contact_document(self, doc_id):
        return self.delete(f"contactdocuments/{doc_id}")

    # ── Contact Folders ───────────────────────────────────────────────────────

    def list_contact_folders(self, participant_id=None):
        params = {}
        if participant_id:
            params["participant"] = participant_id
        return self.get("contactfolders", params)

    def get_contact_folder(self, folder_id):
        return self.get(f"contactfolders/{folder_id}")

    def create_contact_folder(self, participant_id, name):
        return self.post(
            "contactfolders",
            "contactfolders",
            {"name": name, "links": {"participant": str(participant_id)}},
        )

    def update_contact_folder(self, folder_id, **fields):
        return self.put(f"contactfolders/{folder_id}", "contactfolders", fields)

    def delete_contact_folder(self, folder_id):
        return self.delete(f"contactfolders/{folder_id}")

    # ── Contact Notes ─────────────────────────────────────────────────────────

    def list_contact_notes(self, participant_id=None):
        params = {}
        if participant_id:
            params["participant"] = participant_id
        return self.get("contactnotes", params)

    def get_contact_note(self, note_id):
        return self.get(f"contactnotes/{note_id}")

    def create_contact_note(self, participant_id, note, **fields):
        # API field is "text", not "note"
        data = {"text": note, "links": {"participant": str(participant_id)}, **fields}
        return self.post("contactnotes", "contactnotes", data)

    def update_contact_note(self, note_id, **fields):
        if "note" in fields:
            fields["text"] = fields.pop("note")
        return self.put(f"contactnotes/{note_id}", "contactnotes", fields)

    def delete_contact_note(self, note_id):
        return self.delete(f"contactnotes/{note_id}")

    # ── Tasks ─────────────────────────────────────────────────────────────────

    def list_tasks(self, action_id=None, assignee_id=None, page=1, limit=50):
        params = {"page": page, "pageSize": limit}
        if action_id:
            params["action"] = action_id
        if assignee_id:
            params["assignee"] = assignee_id
        return self.get("tasks", params)

    def get_task(self, task_id):
        return self.get(f"tasks/{task_id}")

    def create_task(
        self, name, action_id=None, assignee_id=None, due_date=None, **fields
    ):
        data = {"name": name, **fields}
        links = {}
        if action_id:
            links["action"] = str(action_id)
        if assignee_id:
            links["assignee"] = str(assignee_id)
        if links:
            data["links"] = links
        if due_date:
            data["dueDate"] = due_date
        return self.post("tasks", "tasks", data)

    def update_task(self, task_id, **fields):
        return self.put(f"tasks/{task_id}", "tasks", fields)

    def delete_task(self, task_id):
        return self.delete(f"tasks/{task_id}")

    # ── File Notes ────────────────────────────────────────────────────────────

    def list_file_notes(self, action_id=None, page=1, limit=50):
        params = {"page": page, "pageSize": limit}
        if action_id:
            params["action"] = action_id
        return self.get("filenotes", params)

    def get_file_note(self, note_id):
        return self.get(f"filenotes/{note_id}")

    def create_file_note(self, action_id, note, **fields):
        # API field is "text", not "note"
        data = {"text": note, "links": {"action": str(action_id)}, **fields}
        return self.post("filenotes", "filenotes", data)

    def update_file_note(self, note_id, **fields):
        # Remap "note" kwarg to "text" if passed
        if "note" in fields:
            fields["text"] = fields.pop("note")
        return self.put(f"filenotes/{note_id}", "filenotes", fields)

    def delete_file_note(self, note_id):
        return self.delete(f"filenotes/{note_id}")

    # ── Scratch Notes ─────────────────────────────────────────────────────────

    def list_scratch_notes(self, page=1, limit=50):
        return self.get("scratchnotes", {"page": page, "pageSize": limit})

    def get_scratch_note(self, note_id):
        return self.get(f"scratchnotes/{note_id}")

    def create_scratch_note(self, note, **fields):
        # API field is "text", not "note"
        return self.post("scratchnotes", "scratchnotes", {"text": note, **fields})

    def update_scratch_note(self, note_id, **fields):
        if "note" in fields:
            fields["text"] = fields.pop("note")
        return self.put(f"scratchnotes/{note_id}", "scratchnotes", fields)

    def delete_scratch_note(self, note_id):
        return self.delete(f"scratchnotes/{note_id}")

    # ── Time Records ──────────────────────────────────────────────────────────

    def list_time_records(self, action_id=None, page=1, limit=50):
        params = {"page": page, "pageSize": limit}
        if action_id:
            params["action"] = action_id
        return self.get("timerecords", params)

    def get_time_record(self, record_id):
        return self.get(f"timerecords/{record_id}")

    def create_time_record(self, action_id, start_timestamp, **fields):
        data = {
            "startTimestamp": start_timestamp,
            "links": {"action": str(action_id)},
            **fields,
        }
        return self.post("timerecords", "timerecords", data)

    def update_time_record(self, record_id, **fields):
        return self.put(f"timerecords/{record_id}", "timerecords", fields)

    def delete_time_record(self, record_id):
        return self.delete(f"timerecords/{record_id}")

    # ── Time Entries ──────────────────────────────────────────────────────────

    def list_time_entries(self, action_id=None, page=1, limit=50):
        params = {"page": page, "pageSize": limit}
        if action_id:
            params["action"] = action_id
        return self.get("timeentries", params)

    def get_time_entry(self, entry_id):
        return self.get(f"timeentries/{entry_id}")

    def create_time_entry(self, action_id=None, **fields):
        data = {**fields}
        if action_id:
            data.setdefault("links", {})["action"] = str(action_id)
        return self.post("timeentries", "timeentries", data)

    def update_time_entry(self, entry_id, **fields):
        return self.put(f"timeentries/{entry_id}", "timeentries", fields)

    def delete_time_entry(self, entry_id):
        return self.delete(f"timeentries/{entry_id}")

    # ── Time Record Activities ────────────────────────────────────────────────

    def list_time_record_activities(self):
        return self.get("timerecordactivities")

    def get_time_record_activity(self, activity_id):
        return self.get(f"timerecordactivities/{activity_id}")

    def create_time_record_activity(self, name, **fields):
        return self.post(
            "timerecordactivities", "timerecordactivities", {"name": name, **fields}
        )

    # ── Disbursements ─────────────────────────────────────────────────────────

    def list_disbursements(self, action_id=None, page=1, limit=50):
        params = {"page": page, "pageSize": limit}
        if action_id:
            params["action"] = action_id
        return self.get("disbursements", params)

    def get_disbursement(self, disbursement_id):
        return self.get(f"disbursements/{disbursement_id}")

    def create_disbursement(self, action_id, amount, description="", **fields):
        # API field is "unitPrice" (not "amount")
        data = {
            "unitPrice": amount,
            "links": {"action": str(action_id)},
            **fields,
        }
        if description:
            data["description"] = description
        return self.post("disbursements", "disbursements", data)

    def update_disbursement(self, disbursement_id, **fields):
        return self.put(f"disbursements/{disbursement_id}", "disbursements", fields)

    def delete_disbursement(self, disbursement_id):
        return self.delete(f"disbursements/{disbursement_id}")

    # ── Calendar Appointments ─────────────────────────────────────────────────

    def list_calendar_appointments(self, action_id=None, page=1, limit=50):
        params = {"page": page, "pageSize": limit}
        if action_id:
            params["action"] = action_id
        return self.get("calendarappointments", params)

    def get_calendar_appointment(self, appt_id):
        return self.get(f"calendarappointments/{appt_id}")

    def create_calendar_appointment(
        self, subject, start, end, action_id=None, calendar_id=None, **fields
    ):
        # API fields: "title", "startTimestamp", "endTimestamp" (not subject/start/end)
        data = {
            "title": subject,
            "startTimestamp": start,
            "endTimestamp": end,
            **fields,
        }
        links = {}
        if action_id:
            links["action"] = str(action_id)
        if calendar_id:
            links["calendar"] = str(calendar_id)
        if links:
            data["links"] = links
        return self.post("calendarappointments", "calendarappointments", data)

    def update_calendar_appointment(self, appt_id, **fields):
        # Remap field names if callers use old names
        if "subject" in fields:
            fields["title"] = fields.pop("subject")
        if "start" in fields:
            fields["startTimestamp"] = fields.pop("start")
        if "end" in fields:
            fields["endTimestamp"] = fields.pop("end")
        return self.put(
            f"calendarappointments/{appt_id}", "calendarappointments", fields
        )

    def delete_calendar_appointment(self, appt_id):
        return self.delete(f"calendarappointments/{appt_id}")

    # ── Emails ────────────────────────────────────────────────────────────────

    def list_emails(self, action_id=None, page=1, limit=50):
        params = {"page": page, "pageSize": limit}
        if action_id:
            params["action"] = action_id
        return self.get("emails", params)

    def get_email(self, email_id):
        return self.get(f"emails/{email_id}")

    def create_email(self, subject, body, to_address, action_id=None, **fields):
        # API fields: "subject", "bodyText", "to" (not body/toAddress)
        data = {"subject": subject, "bodyText": body, "to": to_address, **fields}
        if action_id:
            data["links"] = {"action": str(action_id)}
        return self.post("emails", "emails", data)

    def update_email(self, email_id, **fields):
        return self.put(f"emails/{email_id}", "emails", fields)

    def delete_email(self, email_id):
        return self.delete(f"emails/{email_id}")

    # ── Email Associations ────────────────────────────────────────────────────

    def list_email_associations(self, email_id=None):
        params = {}
        if email_id:
            params["email"] = email_id
        return self.get("emailassociations", params)

    def get_email_association(self, assoc_id):
        return self.get(f"emailassociations/{assoc_id}")

    def create_email_association(self, email_id, action_id):
        data = {"links": {"email": str(email_id), "action": str(action_id)}}
        return self.post("emailassociations", "emailassociations", data)

    def delete_email_association(self, assoc_id):
        return self.delete(f"emailassociations/{assoc_id}")

    # ── Email Attachments ─────────────────────────────────────────────────────

    def list_email_attachments(self, email_id=None):
        params = {}
        if email_id:
            params["email"] = email_id
        return self.get("emailattachments", params)

    def get_email_attachment(self, attach_id):
        return self.get(f"emailattachments/{attach_id}")

    def create_email_attachment(self, email_id, file_name, **fields):
        data = {"fileName": file_name, "links": {"email": str(email_id)}, **fields}
        return self.post("emailattachments", "emailattachments", data)

    def delete_email_attachment(self, attach_id):
        return self.delete(f"emailattachments/{attach_id}")

    # ── SMS ───────────────────────────────────────────────────────────────────

    def list_sms(self, action_id=None, page=1, limit=50):
        params = {"page": page, "pageSize": limit}
        if action_id:
            params["action"] = action_id
        return self.get("sms", params)

    def get_sms(self, sms_id):
        return self.get(f"sms/{sms_id}")

    def create_sms(self, message, to_number, action_id=None, **fields):
        # API fields: "text" (not message), "number" (not toNumber)
        data = {"text": message, "number": to_number, **fields}
        if action_id:
            data.setdefault("links", {})["action"] = str(action_id)
        return self.post("sms", "sms", data)

    def update_sms(self, sms_id, **fields):
        return self.put(f"sms/{sms_id}", "sms", fields)

    # ── Phone Records ─────────────────────────────────────────────────────────

    def list_phone_records(self, participant_id=None, page=1, limit=50):
        params = {"page": page, "pageSize": limit}
        if participant_id:
            params["participant"] = participant_id
        return self.get("phonerecords", params)

    def get_phone_record(self, record_id):
        return self.get(f"phonerecords/{record_id}")

    def create_phone_record(self, participant_id, number, phone_type="", **fields):
        data = {
            "number": number,
            "links": {"participant": str(participant_id)},
            **fields,
        }
        if phone_type:
            data["phoneType"] = phone_type
        return self.post("phonerecords", "phonerecords", data)

    def update_phone_record(self, record_id, **fields):
        return self.put(f"phonerecords/{record_id}", "phonerecords", fields)

    def delete_phone_record(self, record_id):
        return self.delete(f"phonerecords/{record_id}")

    # ── Quick Codes ───────────────────────────────────────────────────────────

    def list_quick_codes(self, code_type=None):
        params = {}
        if code_type:
            params["codeType"] = code_type
        return self.get("quickcodes", params)

    def get_quick_code(self, code_id):
        return self.get(f"quickcodes/{code_id}")

    def create_quick_code(self, code, description, code_type, **fields):
        return self.post(
            "quickcodes",
            "quickcodes",
            {"code": code, "description": description, "codeType": code_type, **fields},
        )

    def update_quick_code(self, code_id, **fields):
        return self.put(f"quickcodes/{code_id}", "quickcodes", fields)

    # ── Data Collections ──────────────────────────────────────────────────────

    def list_data_collections(self):
        return self.get("datacollections")

    def get_data_collection(self, dc_id):
        return self.get(f"datacollections/{dc_id}")

    def create_data_collection(self, name, **fields):
        return self.post("datacollections", "datacollections", {"name": name, **fields})

    def update_data_collection(self, dc_id, **fields):
        return self.put(f"datacollections/{dc_id}", "datacollections", fields)

    def delete_data_collection(self, dc_id):
        return self.delete(f"datacollections/{dc_id}")

    # ── Data Collection Fields ────────────────────────────────────────────────

    def list_data_collection_fields(self, dc_id=None):
        params = {}
        if dc_id:
            params["dataCollection"] = dc_id
        return self.get("datacollectionfields", params)

    def get_data_collection_field(self, field_id):
        return self.get(f"datacollectionfields/{field_id}")

    def create_data_collection_field(self, dc_id, name, field_type, **fields):
        data = {
            "name": name,
            "fieldType": field_type,
            "links": {"dataCollection": str(dc_id)},
            **fields,
        }
        return self.post("datacollectionfields", "datacollectionfields", data)

    def update_data_collection_field(self, field_id, **fields):
        return self.put(
            f"datacollectionfields/{field_id}", "datacollectionfields", fields
        )

    def delete_data_collection_field(self, field_id):
        return self.delete(f"datacollectionfields/{field_id}")

    # ── Data Collection Records ───────────────────────────────────────────────

    def list_data_collection_records(self, dc_id=None, action_id=None):
        params = {}
        if dc_id:
            params["dataCollection"] = dc_id
        if action_id:
            params["action"] = action_id
        return self.get("datacollectionrecords", params)

    def get_data_collection_record(self, record_id):
        return self.get(f"datacollectionrecords/{record_id}")

    def create_data_collection_record(self, dc_id, action_id, **fields):
        data = {
            "links": {
                "dataCollection": str(dc_id),
                "action": str(action_id),
            },
            **fields,
        }
        return self.post("datacollectionrecords", "datacollectionrecords", data)

    def update_data_collection_record(self, record_id, **fields):
        return self.put(
            f"datacollectionrecords/{record_id}", "datacollectionrecords", fields
        )

    def delete_data_collection_record(self, record_id):
        return self.delete(f"datacollectionrecords/{record_id}")

    # ── Data Collection Record Values ─────────────────────────────────────────

    def list_data_collection_record_values(self, record_id=None):
        params = {}
        if record_id:
            params["dataCollectionRecord"] = record_id
        return self.get("datacollectionrecordvalues", params)

    def get_data_collection_record_value(self, value_id):
        return self.get(f"datacollectionrecordvalues/{value_id}")

    def create_data_collection_record_value(self, record_id, field_id, value):
        data = {
            "value": value,
            "links": {
                "dataCollectionRecord": str(record_id),
                "dataCollectionField": str(field_id),
            },
        }
        return self.post(
            "datacollectionrecordvalues", "datacollectionrecordvalues", data
        )

    def update_data_collection_record_value(self, value_id, value):
        return self.put(
            f"datacollectionrecordvalues/{value_id}",
            "datacollectionrecordvalues",
            {"value": value},
        )

    def delete_data_collection_record_value(self, value_id):
        return self.delete(f"datacollectionrecordvalues/{value_id}")

    # ── Rest Hooks (Webhooks) ─────────────────────────────────────────────────

    def list_rest_hooks(self):
        return self.get("resthooks")

    def get_rest_hook(self, hook_id):
        return self.get(f"resthooks/{hook_id}")

    def create_rest_hook(self, event_name, target_url):
        _validate_webhook_url(target_url)
        return self.post(
            "resthooks", "resthooks", {"eventName": event_name, "targetUrl": target_url}
        )

    def update_rest_hook(self, hook_id, event_name=None, target_url=None):
        data = {}
        if event_name:
            data["eventName"] = event_name
        if target_url:
            _validate_webhook_url(target_url)
            data["targetUrl"] = target_url
        return self.put(f"resthooks/{hook_id}", "resthooks", data)

    def delete_rest_hook(self, hook_id):
        return self.delete(f"resthooks/{hook_id}")

    # ── Steps ─────────────────────────────────────────────────────────────────

    def list_steps(self, action_type_id=None):
        params = {}
        if action_type_id:
            params["actionType"] = action_type_id
        return self.get("steps", params)

    def get_step(self, step_id):
        return self.get(f"steps/{step_id}")

    def list_step_tasks(self, step_id=None):
        params = {}
        if step_id:
            params["step"] = step_id
        return self.get("steptasks", params)

    def list_step_messages(self, step_id=None):
        params = {}
        if step_id:
            params["step"] = step_id
        return self.get("stepmessages", params)

    # ── Roles ─────────────────────────────────────────────────────────────────

    def list_roles(self):
        return self.get("roles")

    def get_role(self, role_id):
        return self.get(f"roles/{role_id}")

    # ── Tags ──────────────────────────────────────────────────────────────────

    def list_tags(self):
        return self.get("tags")

    def get_tag(self, tag_id):
        return self.get(f"tags/{tag_id}")

    # ── Rates ─────────────────────────────────────────────────────────────────

    def list_rates(self):
        return self.get("rates")

    def get_rate(self, rate_id):
        return self.get(f"rates/{rate_id}")

    # ── Tax Codes ─────────────────────────────────────────────────────────────

    def list_tax_codes(self):
        return self.get("taxcodes")

    def get_tax_code(self, code_id):
        return self.get(f"taxcodes/{code_id}")

    # ── UTBMS Codes ───────────────────────────────────────────────────────────

    def list_utbms_codes(self, code_type=None):
        params = {}
        if code_type:
            params["codeType"] = code_type
        return self.get("utbmscodes", params)

    def get_utbms_code(self, code_id):
        return self.get(f"utbmscodes/{code_id}")

    def create_utbms_code(self, code, description, code_type, **fields):
        return self.post(
            "utbmscodes",
            "utbmscodes",
            {"code": code, "description": description, "codeType": code_type, **fields},
        )

    def update_utbms_code(self, code_id, **fields):
        return self.put(f"utbmscodes/{code_id}", "utbmscodes", fields)

    def delete_utbms_code(self, code_id):
        return self.delete(f"utbmscodes/{code_id}")

    # ── Document Templates ────────────────────────────────────────────────────

    def list_document_templates(self):
        return self.get("documenttemplates")

    def get_document_template(self, template_id):
        return self.get(f"documenttemplates/{template_id}")

    # ── Task Templates ────────────────────────────────────────────────────────

    def list_task_templates(self):
        return self.get("tasktemplates")

    def get_task_template(self, template_id):
        return self.get(f"tasktemplates/{template_id}")

    # ── Billing Preferences ───────────────────────────────────────────────────

    def list_billing_preferences(self):
        return self.get("billingpreferences")

    def update_billing_preferences(self, pref_id, **fields):
        return self.put(f"billingpreferences/{pref_id}", "billingpreferences", fields)

    # ── Settings ──────────────────────────────────────────────────────────────

    def list_settings(self):
        return self.get("settings")

    def update_settings(self, setting_id, **fields):
        return self.put(f"settings/{setting_id}", "settings", fields)

    # ── Reference Data ────────────────────────────────────────────────────────

    def list_countries(self):
        return self.get("countries")

    def get_country(self, country_id):
        return self.get(f"countries/{country_id}")

    def list_currencies(self):
        return self.get("currencies")

    def get_currency(self, currency_id):
        return self.get(f"currencies/{currency_id}")

    def list_divisions(self):
        return self.get("divisions")

    def get_division(self, division_id):
        return self.get(f"divisions/{division_id}")

    def list_units(self):
        return self.get("units")

    def get_unit(self, unit_id):
        return self.get(f"units/{unit_id}")

    def list_nodes(self):
        return self.get("nodes")

    def get_node(self, node_id):
        return self.get(f"nodes/{node_id}")

    def list_gender_types(self):
        return self.get("gendertypes")

    def list_sale_purchase_types(self):
        return self.get("salepurchasetypes")
