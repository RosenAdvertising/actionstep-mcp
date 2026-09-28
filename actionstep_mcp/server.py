#!/usr/bin/env python3
"""Actionstep MCP Server — full Actionstep API coverage via MCPServer."""

import json
from typing import Annotated

from mcp.server import MCPServer
from pydantic import Field

from .client import ActionstepClient

ListLimit = Annotated[int, Field(ge=1, le=200)]
PageNumber = Annotated[int, Field(ge=1)]

mcp = MCPServer(
    "actionstep-mcp",
    version="0.1.0",
    instructions=(
        "Full access to Actionstep practice management: actions (matters), participants "
        "(contacts), tasks, time records, time entries, disbursements, calendar, emails, "
        "SMS, file notes, documents, data collections, webhooks, and more."
    ),
)


# ── Users ─────────────────────────────────────────────────────────────────────


@mcp.tool()
def get_current_user() -> str:
    """Get the currently authenticated user's profile."""
    try:
        return json.dumps(ActionstepClient().get_current_user(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_users() -> str:
    """List all users in this Actionstep organisation."""
    try:
        return json.dumps(ActionstepClient().list_users(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_user(user_id: str) -> str:
    """Get a user by ID."""
    try:
        return json.dumps(ActionstepClient().get_user(user_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Actions (Matters) ─────────────────────────────────────────────────────────


@mcp.tool()
def list_actions(
    action_type: str = "",
    status: str = "",
    limit: ListLimit = 50,
    page: PageNumber = 1,
) -> str:
    """List actions (matters/cases). action_type: filter by action type ID. status: open|closed."""
    try:
        return json.dumps(
            ActionstepClient().list_actions(
                action_type=action_type or None,
                status=status or None,
                limit=limit,
                page=page,
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_action(action_id: str) -> str:
    """Get an action (matter) by ID."""
    try:
        return json.dumps(ActionstepClient().get_action(action_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_action(name: str, action_type_id: str, assigned_to_id: str = "") -> str:
    """Create an action (matter). action_type_id: from list_action_types."""
    try:
        fields = {}
        if assigned_to_id:
            fields["links"] = {"assignedTo": assigned_to_id}
        return json.dumps(
            ActionstepClient().create_action(name, action_type_id, **fields), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_action(
    action_id: str, name: str = "", status: str = "", assigned_to_id: str = ""
) -> str:
    """Update an action's name, status, or assignment."""
    try:
        fields = {}
        if name:
            fields["name"] = name
        if status:
            fields["status"] = status
        if assigned_to_id:
            fields["links"] = {"assignedTo": assigned_to_id}
        return json.dumps(
            ActionstepClient().update_action(action_id, **fields), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Action Types ──────────────────────────────────────────────────────────────


@mcp.tool()
def list_action_types(is_billable: str = "") -> str:
    """List action types (matter/case types). is_billable: 'true' or 'false' to filter."""
    try:
        billable_filter = None
        if is_billable.lower() == "true":
            billable_filter = True
        elif is_billable.lower() == "false":
            billable_filter = False
        return json.dumps(
            ActionstepClient().list_action_types(is_billable=billable_filter), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_action_type(action_type_id: str) -> str:
    """Get an action type by ID."""
    try:
        return json.dumps(ActionstepClient().get_action_type(action_type_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Action Bill Settings ──────────────────────────────────────────────────────


@mcp.tool()
def list_action_bill_settings(action_id: str = "") -> str:
    """List billing settings for actions. Filter by action_id for a specific matter."""
    try:
        return json.dumps(
            ActionstepClient().list_action_bill_settings(action_id=action_id or None),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_action_bill_settings(settings_id: str) -> str:
    """Get billing settings by ID."""
    try:
        return json.dumps(
            ActionstepClient().get_action_bill_settings(settings_id), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_action_bill_settings(
    settings_id: str, billing_type: str = "", rate: float = 0.0
) -> str:
    """Update billing settings for an action."""
    try:
        fields = {}
        if billing_type:
            fields["billingType"] = billing_type
        if rate:
            fields["rate"] = rate
        return json.dumps(
            ActionstepClient().update_action_bill_settings(settings_id, **fields),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Action Change Steps ───────────────────────────────────────────────────────


@mcp.tool()
def list_action_change_steps(action_id: str = "") -> str:
    """List available step transitions for an action."""
    try:
        return json.dumps(
            ActionstepClient().list_action_change_steps(action_id=action_id or None),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def transition_action_step(action_id: str, step_id: str, node_id: str = "") -> str:
    """Transition an action to a new workflow step. action_id: the matter ID. step_id: the target step ID."""
    try:
        return json.dumps(
            ActionstepClient().create_action_change_step(
                action_id, step_id, node_id=node_id or None
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Action Documents ──────────────────────────────────────────────────────────


@mcp.tool()
def list_action_documents(action_id: str = "") -> str:
    """List documents attached to actions. Filter by action_id."""
    try:
        return json.dumps(
            ActionstepClient().list_action_documents(action_id=action_id or None),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_action_document(document_id: str) -> str:
    """Get an action document by ID."""
    try:
        return json.dumps(ActionstepClient().get_action_document(document_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_action_document(action_id: str, file_name: str, folder_id: str = "") -> str:
    """Attach a document to an action."""
    try:
        fields: dict[str, str | dict[str, str]] = {"fileName": file_name}
        if folder_id:
            fields["links"] = {"actionFolder": folder_id}
        return json.dumps(
            ActionstepClient().create_action_document(action_id, **fields), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_action_document(document_id: str) -> str:
    """Delete an action document by ID."""
    try:
        return json.dumps(
            ActionstepClient().delete_action_document(document_id), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Action Folders ────────────────────────────────────────────────────────────


@mcp.tool()
def list_action_folders(action_id: str = "") -> str:
    """List document folders for actions."""
    try:
        return json.dumps(
            ActionstepClient().list_action_folders(action_id=action_id or None),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_action_folder(folder_id: str) -> str:
    """Get an action folder by ID."""
    try:
        return json.dumps(ActionstepClient().get_action_folder(folder_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_action_folder(action_id: str, name: str) -> str:
    """Create a document folder within an action."""
    try:
        return json.dumps(
            ActionstepClient().create_action_folder(action_id, name), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_action_folder(folder_id: str, name: str) -> str:
    """Rename an action folder."""
    try:
        return json.dumps(
            ActionstepClient().update_action_folder(folder_id, name=name), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_action_folder(folder_id: str) -> str:
    """Delete an action folder by ID."""
    try:
        return json.dumps(ActionstepClient().delete_action_folder(folder_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Action Participants ───────────────────────────────────────────────────────


@mcp.tool()
def list_action_participants(action_id: str = "") -> str:
    """List participants (clients/contacts) on actions."""
    try:
        return json.dumps(
            ActionstepClient().list_action_participants(action_id=action_id or None),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_action_participant(ap_id: str) -> str:
    """Get an action participant record by ID."""
    try:
        return json.dumps(ActionstepClient().get_action_participant(ap_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def add_participant_to_action(
    action_id: str, participant_id: str, participant_type_id: str
) -> str:
    """Add a participant (contact) to an action with a specific role/type."""
    try:
        return json.dumps(
            ActionstepClient().create_action_participant(
                action_id, participant_id, participant_type_id
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def remove_participant_from_action(ap_id: str) -> str:
    """Remove a participant from an action."""
    try:
        return json.dumps(ActionstepClient().delete_action_participant(ap_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Action Permissions ────────────────────────────────────────────────────────


@mcp.tool()
def list_action_permissions(action_id: str = "") -> str:
    """List access permissions on actions."""
    try:
        return json.dumps(
            ActionstepClient().list_action_permissions(action_id=action_id or None),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Action Rates ──────────────────────────────────────────────────────────────


@mcp.tool()
def list_action_rates(action_id: str = "") -> str:
    """List billing rates set on actions."""
    try:
        return json.dumps(
            ActionstepClient().list_action_rates(action_id=action_id or None), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_action_rate(rate_id: str) -> str:
    """Get an action billing rate by ID."""
    try:
        return json.dumps(ActionstepClient().get_action_rate(rate_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_action_rate(
    action_id: str, rate: float, participant_type_id: str = ""
) -> str:
    """Set a billing rate on an action."""
    try:
        fields: dict[str, float | dict[str, str]] = {"rate": rate}
        if participant_type_id:
            fields["links"] = {"participantType": participant_type_id}
        return json.dumps(
            ActionstepClient().create_action_rate(action_id, **fields), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_action_rate(rate_id: str, rate: float) -> str:
    """Update a billing rate on an action."""
    try:
        return json.dumps(
            ActionstepClient().update_action_rate(rate_id, rate=rate), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_action_rate(rate_id: str) -> str:
    """Delete an action billing rate."""
    try:
        return json.dumps(ActionstepClient().delete_action_rate(rate_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Action Type Folders ───────────────────────────────────────────────────────


@mcp.tool()
def list_action_type_folders(action_type_id: str = "") -> str:
    """List default document folders for an action type."""
    try:
        return json.dumps(
            ActionstepClient().list_action_type_folders(
                action_type_id=action_type_id or None
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_action_type_folder(folder_id: str) -> str:
    """Get an action type folder by ID."""
    try:
        return json.dumps(
            ActionstepClient().get_action_type_folder(folder_id), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_action_type_folder(action_type_id: str, name: str) -> str:
    """Create a default document folder template for an action type."""
    try:
        return json.dumps(
            ActionstepClient().create_action_type_folder(action_type_id, name), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_action_type_folder(folder_id: str) -> str:
    """Delete an action type folder template."""
    try:
        return json.dumps(
            ActionstepClient().delete_action_type_folder(folder_id), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Participants (Contacts) ───────────────────────────────────────────────────


@mcp.tool()
def list_participants(page: PageNumber = 1, limit: ListLimit = 50) -> str:
    """List participants (contacts/clients)."""
    try:
        return json.dumps(
            ActionstepClient().list_participants(page=page, limit=limit), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_participant(participant_id: str) -> str:
    """Get a participant (contact) by ID."""
    try:
        return json.dumps(ActionstepClient().get_participant(participant_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_participant(
    first_name: str = "",
    last_name: str = "",
    company_name: str = "",
    is_company: bool = False,
    email: str = "",
) -> str:
    """Create a participant (contact). Set is_company=true for organisations."""
    try:
        fields = {}
        if email:
            fields["email"] = email
        return json.dumps(
            ActionstepClient().create_participant(
                first_name=first_name,
                last_name=last_name,
                company_name=company_name,
                is_company=is_company,
                **fields,
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_participant(
    participant_id: str, first_name: str = "", last_name: str = "", email: str = ""
) -> str:
    """Update a participant's details."""
    try:
        fields = {}
        if first_name:
            fields["firstName"] = first_name
        if last_name:
            fields["lastName"] = last_name
        if email:
            fields["email"] = email
        return json.dumps(
            ActionstepClient().update_participant(participant_id, **fields), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_participant(participant_id: str) -> str:
    """Delete a participant by ID."""
    try:
        return json.dumps(
            ActionstepClient().delete_participant(participant_id), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Participant Types ─────────────────────────────────────────────────────────


@mcp.tool()
def list_participant_types() -> str:
    """List participant types (roles: client, opposing party, witness, etc.)."""
    try:
        return json.dumps(ActionstepClient().list_participant_types(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_participant_type(pt_id: str) -> str:
    """Get a participant type by ID."""
    try:
        return json.dumps(ActionstepClient().get_participant_type(pt_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Contact Relationships ─────────────────────────────────────────────────────


@mcp.tool()
def list_contact_relationships(participant_id: str = "") -> str:
    """List relationships between participants."""
    try:
        return json.dumps(
            ActionstepClient().list_contact_relationships(
                participant_id=participant_id or None
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_contact_relationship(cr_id: str) -> str:
    """Get a contact relationship by ID."""
    try:
        return json.dumps(ActionstepClient().get_contact_relationship(cr_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_contact_relationship(
    participant1_id: str, participant2_id: str, relationship_type_id: str
) -> str:
    """Create a relationship between two participants."""
    try:
        return json.dumps(
            ActionstepClient().create_contact_relationship(
                participant1_id, participant2_id, relationship_type_id
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Contact Documents ─────────────────────────────────────────────────────────


@mcp.tool()
def list_contact_documents(participant_id: str = "") -> str:
    """List documents attached to a contact."""
    try:
        return json.dumps(
            ActionstepClient().list_contact_documents(
                participant_id=participant_id or None
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_contact_document(doc_id: str) -> str:
    """Get a contact document by ID."""
    try:
        return json.dumps(ActionstepClient().get_contact_document(doc_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_contact_document(doc_id: str) -> str:
    """Delete a contact document."""
    try:
        return json.dumps(ActionstepClient().delete_contact_document(doc_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Contact Folders ───────────────────────────────────────────────────────────


@mcp.tool()
def list_contact_folders(participant_id: str = "") -> str:
    """List document folders for a contact."""
    try:
        return json.dumps(
            ActionstepClient().list_contact_folders(
                participant_id=participant_id or None
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_contact_folder(participant_id: str, name: str) -> str:
    """Create a document folder for a contact."""
    try:
        return json.dumps(
            ActionstepClient().create_contact_folder(participant_id, name), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_contact_folder(folder_id: str) -> str:
    """Delete a contact folder."""
    try:
        return json.dumps(ActionstepClient().delete_contact_folder(folder_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Contact Notes ─────────────────────────────────────────────────────────────


@mcp.tool()
def list_contact_notes(participant_id: str = "") -> str:
    """List notes on a contact."""
    try:
        return json.dumps(
            ActionstepClient().list_contact_notes(
                participant_id=participant_id or None
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_contact_note(note_id: str) -> str:
    """Get a contact note by ID."""
    try:
        return json.dumps(ActionstepClient().get_contact_note(note_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_contact_note(participant_id: str, note: str) -> str:
    """Create a note on a contact."""
    try:
        return json.dumps(
            ActionstepClient().create_contact_note(participant_id, note), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_contact_note(note_id: str, note: str) -> str:
    """Update a contact note."""
    try:
        return json.dumps(
            ActionstepClient().update_contact_note(note_id, note=note), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_contact_note(note_id: str) -> str:
    """Delete a contact note."""
    try:
        return json.dumps(ActionstepClient().delete_contact_note(note_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Phone Records ─────────────────────────────────────────────────────────────


@mcp.tool()
def list_phone_records(
    participant_id: str = "", limit: ListLimit = 50, page: PageNumber = 1
) -> str:
    """List phone numbers for participants."""
    try:
        return json.dumps(
            ActionstepClient().list_phone_records(
                participant_id=participant_id or None, page=page, limit=limit
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_phone_record(record_id: str) -> str:
    """Get a phone record by ID."""
    try:
        return json.dumps(ActionstepClient().get_phone_record(record_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_phone_record(
    participant_id: str, number: str, phone_type: str = "Mobile"
) -> str:
    """Add a phone number to a participant. phone_type: Mobile | Work | Home | Fax."""
    try:
        return json.dumps(
            ActionstepClient().create_phone_record(
                participant_id, number, phone_type=phone_type
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_phone_record(record_id: str, number: str = "", phone_type: str = "") -> str:
    """Update a phone record."""
    try:
        fields = {}
        if number:
            fields["number"] = number
        if phone_type:
            fields["phoneType"] = phone_type
        return json.dumps(
            ActionstepClient().update_phone_record(record_id, **fields), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_phone_record(record_id: str) -> str:
    """Delete a phone record."""
    try:
        return json.dumps(ActionstepClient().delete_phone_record(record_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Tasks ─────────────────────────────────────────────────────────────────────


@mcp.tool()
def list_tasks(
    action_id: str = "",
    assignee_id: str = "",
    page: PageNumber = 1,
    limit: ListLimit = 50,
) -> str:
    """List tasks. Filter by action_id (matter) or assignee_id (user)."""
    try:
        return json.dumps(
            ActionstepClient().list_tasks(
                action_id=action_id or None,
                assignee_id=assignee_id or None,
                page=page,
                limit=limit,
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_task(task_id: str) -> str:
    """Get a task by ID."""
    try:
        return json.dumps(ActionstepClient().get_task(task_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_task(
    name: str,
    action_id: str = "",
    assignee_id: str = "",
    due_date: str = "",
    priority: str = "",
) -> str:
    """Create a task. due_date: YYYY-MM-DD. priority: high | normal | low."""
    try:
        fields = {}
        if priority:
            fields["priority"] = priority
        return json.dumps(
            ActionstepClient().create_task(
                name,
                action_id=action_id or None,
                assignee_id=assignee_id or None,
                due_date=due_date or None,
                **fields,
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_task(
    task_id: str,
    name: str = "",
    due_date: str = "",
    completed: bool = False,
    priority: str = "",
) -> str:
    """Update a task. Set completed=true to mark done."""
    try:
        fields = {}
        if name:
            fields["name"] = name
        if due_date:
            fields["dueDate"] = due_date
        if completed:
            fields["completed"] = "T"
        if priority:
            fields["priority"] = priority
        return json.dumps(ActionstepClient().update_task(task_id, **fields), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_task(task_id: str) -> str:
    """Delete a task by ID."""
    try:
        return json.dumps(ActionstepClient().delete_task(task_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── File Notes ────────────────────────────────────────────────────────────────


@mcp.tool()
def list_file_notes(
    action_id: str = "", page: PageNumber = 1, limit: ListLimit = 50
) -> str:
    """List file notes (case notes/attendance notes) on actions."""
    try:
        return json.dumps(
            ActionstepClient().list_file_notes(
                action_id=action_id or None, page=page, limit=limit
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_file_note(note_id: str) -> str:
    """Get a file note by ID."""
    try:
        return json.dumps(ActionstepClient().get_file_note(note_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_file_note(action_id: str, note: str, note_type: str = "") -> str:
    """Create a file note on an action (matter note/attendance note)."""
    try:
        fields = {}
        if note_type:
            fields["noteType"] = note_type
        return json.dumps(
            ActionstepClient().create_file_note(action_id, note, **fields), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_file_note(note_id: str, note: str) -> str:
    """Update a file note."""
    try:
        return json.dumps(
            ActionstepClient().update_file_note(note_id, note=note), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_file_note(note_id: str) -> str:
    """Delete a file note."""
    try:
        return json.dumps(ActionstepClient().delete_file_note(note_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Scratch Notes ─────────────────────────────────────────────────────────────


@mcp.tool()
def list_scratch_notes(page: PageNumber = 1, limit: ListLimit = 50) -> str:
    """List scratch notes (quick personal notes)."""
    try:
        return json.dumps(
            ActionstepClient().list_scratch_notes(page=page, limit=limit), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_scratch_note(note_id: str) -> str:
    """Get a scratch note by ID."""
    try:
        return json.dumps(ActionstepClient().get_scratch_note(note_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_scratch_note(note: str) -> str:
    """Create a scratch note."""
    try:
        return json.dumps(ActionstepClient().create_scratch_note(note), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_scratch_note(note_id: str, note: str) -> str:
    """Update a scratch note."""
    try:
        return json.dumps(
            ActionstepClient().update_scratch_note(note_id, note=note), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_scratch_note(note_id: str) -> str:
    """Delete a scratch note."""
    try:
        return json.dumps(ActionstepClient().delete_scratch_note(note_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Time Records ──────────────────────────────────────────────────────────────


@mcp.tool()
def list_time_records(
    action_id: str = "", page: PageNumber = 1, limit: ListLimit = 50
) -> str:
    """List time records (timer sessions). Filter by action_id for a specific matter."""
    try:
        return json.dumps(
            ActionstepClient().list_time_records(
                action_id=action_id or None, page=page, limit=limit
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_time_record(record_id: str) -> str:
    """Get a time record by ID."""
    try:
        return json.dumps(ActionstepClient().get_time_record(record_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_time_record(
    action_id: str, start_timestamp: str, end_timestamp: str = "", notes: str = ""
) -> str:
    """Create a time record. start_timestamp: 'YYYY-MM-DD HH:MM'. Links to an action."""
    try:
        fields = {}
        if end_timestamp:
            fields["endTimestamp"] = end_timestamp
        if notes:
            fields["notes"] = notes
        return json.dumps(
            ActionstepClient().create_time_record(action_id, start_timestamp, **fields),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_time_record(record_id: str, end_timestamp: str = "", notes: str = "") -> str:
    """Update a time record."""
    try:
        fields = {}
        if end_timestamp:
            fields["endTimestamp"] = end_timestamp
        if notes:
            fields["notes"] = notes
        return json.dumps(
            ActionstepClient().update_time_record(record_id, **fields), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_time_record(record_id: str) -> str:
    """Delete a time record."""
    try:
        return json.dumps(ActionstepClient().delete_time_record(record_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Time Entries (Billable) ───────────────────────────────────────────────────


@mcp.tool()
def list_time_entries(
    action_id: str = "", page: PageNumber = 1, limit: ListLimit = 50
) -> str:
    """List time entries (billable time). Filter by action_id for a specific matter."""
    try:
        return json.dumps(
            ActionstepClient().list_time_entries(
                action_id=action_id or None, page=page, limit=limit
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_time_entry(entry_id: str) -> str:
    """Get a time entry by ID."""
    try:
        return json.dumps(ActionstepClient().get_time_entry(entry_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_time_entry(
    action_id: str,
    duration_minutes: int = 0,
    description: str = "",
    activity_id: str = "",
    date: str = "",
) -> str:
    """Create a billable time entry on an action."""
    try:
        fields = {}
        if duration_minutes:
            fields["durationMinutes"] = duration_minutes
        if description:
            fields["description"] = description
        if date:
            fields["date"] = date
        if activity_id:
            fields["links"] = {"timeRecordActivity": activity_id}
        return json.dumps(
            ActionstepClient().create_time_entry(action_id=action_id, **fields),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_time_entry(
    entry_id: str, duration_minutes: int = 0, description: str = ""
) -> str:
    """Update a time entry."""
    try:
        fields = {}
        if duration_minutes:
            fields["durationMinutes"] = duration_minutes
        if description:
            fields["description"] = description
        return json.dumps(
            ActionstepClient().update_time_entry(entry_id, **fields), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_time_entry(entry_id: str) -> str:
    """Delete a time entry."""
    try:
        return json.dumps(ActionstepClient().delete_time_entry(entry_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Time Record Activities ────────────────────────────────────────────────────


@mcp.tool()
def list_time_record_activities() -> str:
    """List time record activity codes (billing categories)."""
    try:
        return json.dumps(ActionstepClient().list_time_record_activities(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_time_record_activity(activity_id: str) -> str:
    """Get a time record activity by ID."""
    try:
        return json.dumps(
            ActionstepClient().get_time_record_activity(activity_id), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Disbursements ─────────────────────────────────────────────────────────────


@mcp.tool()
def list_disbursements(
    action_id: str = "", page: PageNumber = 1, limit: ListLimit = 50
) -> str:
    """List disbursements (expenses). Filter by action_id for matter-specific expenses."""
    try:
        return json.dumps(
            ActionstepClient().list_disbursements(
                action_id=action_id or None, page=page, limit=limit
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_disbursement(disbursement_id: str) -> str:
    """Get a disbursement by ID."""
    try:
        return json.dumps(
            ActionstepClient().get_disbursement(disbursement_id), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_disbursement(
    action_id: str, amount: float, description: str = "", date: str = ""
) -> str:
    """Create a disbursement (expense) on an action. amount: dollar value."""
    try:
        fields = {}
        if date:
            fields["date"] = date
        return json.dumps(
            ActionstepClient().create_disbursement(
                action_id, amount, description=description, **fields
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_disbursement(
    disbursement_id: str, amount: float = 0.0, description: str = ""
) -> str:
    """Update a disbursement."""
    try:
        fields = {}
        if amount:
            fields["unitPrice"] = amount
        if description:
            fields["description"] = description
        return json.dumps(
            ActionstepClient().update_disbursement(disbursement_id, **fields), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_disbursement(disbursement_id: str) -> str:
    """Delete a disbursement."""
    try:
        return json.dumps(
            ActionstepClient().delete_disbursement(disbursement_id), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Calendar Appointments ─────────────────────────────────────────────────────


@mcp.tool()
def list_calendar_appointments(
    action_id: str = "", page: PageNumber = 1, limit: ListLimit = 50
) -> str:
    """List calendar appointments. Filter by action_id for matter-specific events."""
    try:
        return json.dumps(
            ActionstepClient().list_calendar_appointments(
                action_id=action_id or None, page=page, limit=limit
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_calendar_appointment(appt_id: str) -> str:
    """Get a calendar appointment by ID."""
    try:
        return json.dumps(
            ActionstepClient().get_calendar_appointment(appt_id), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_calendar_appointment(
    subject: str, start: str, end: str, action_id: str = "", location: str = ""
) -> str:
    """Create a calendar appointment. start/end: ISO 8601 datetime."""
    try:
        fields = {}
        if location:
            fields["location"] = location
        return json.dumps(
            ActionstepClient().create_calendar_appointment(
                subject, start, end, action_id=action_id or None, **fields
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_calendar_appointment(
    appt_id: str, subject: str = "", start: str = "", end: str = ""
) -> str:
    """Update a calendar appointment."""
    try:
        fields = {}
        if subject:
            fields["subject"] = subject
        if start:
            fields["start"] = start
        if end:
            fields["end"] = end
        return json.dumps(
            ActionstepClient().update_calendar_appointment(appt_id, **fields), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_calendar_appointment(appt_id: str) -> str:
    """Delete a calendar appointment."""
    try:
        return json.dumps(
            ActionstepClient().delete_calendar_appointment(appt_id), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Emails ────────────────────────────────────────────────────────────────────


@mcp.tool()
def list_emails(
    action_id: str = "", page: PageNumber = 1, limit: ListLimit = 50
) -> str:
    """List emails. Filter by action_id to see emails on a matter."""
    try:
        return json.dumps(
            ActionstepClient().list_emails(
                action_id=action_id or None, page=page, limit=limit
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_email(email_id: str) -> str:
    """Get an email by ID."""
    try:
        return json.dumps(ActionstepClient().get_email(email_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_email(subject: str, body: str, to_address: str, action_id: str = "") -> str:
    """Create/log an email. Links it to an action if action_id provided."""
    try:
        return json.dumps(
            ActionstepClient().create_email(
                subject, body, to_address, action_id=action_id or None
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_email(email_id: str) -> str:
    """Delete an email record."""
    try:
        return json.dumps(ActionstepClient().delete_email(email_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Email Associations ────────────────────────────────────────────────────────


@mcp.tool()
def list_email_associations(email_id: str = "") -> str:
    """List action associations for emails."""
    try:
        return json.dumps(
            ActionstepClient().list_email_associations(email_id=email_id or None),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_email_association(email_id: str, action_id: str) -> str:
    """Associate an email with an action (matter)."""
    try:
        return json.dumps(
            ActionstepClient().create_email_association(email_id, action_id), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_email_association(assoc_id: str) -> str:
    """Remove an email-action association."""
    try:
        return json.dumps(
            ActionstepClient().delete_email_association(assoc_id), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── SMS ───────────────────────────────────────────────────────────────────────


@mcp.tool()
def list_sms(action_id: str = "", page: PageNumber = 1, limit: ListLimit = 50) -> str:
    """List SMS messages. Filter by action_id for matter-specific messages."""
    try:
        return json.dumps(
            ActionstepClient().list_sms(
                action_id=action_id or None, page=page, limit=limit
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_sms(sms_id: str) -> str:
    """Get an SMS record by ID."""
    try:
        return json.dumps(ActionstepClient().get_sms(sms_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_sms(message: str, to_number: str, action_id: str = "") -> str:
    """Send/log an SMS message. to_number: E.164 format (+1234567890)."""
    try:
        return json.dumps(
            ActionstepClient().create_sms(
                message, to_number, action_id=action_id or None
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Data Collections ──────────────────────────────────────────────────────────


@mcp.tool()
def list_data_collections() -> str:
    """List data collection schemas configured for this organisation."""
    try:
        return json.dumps(ActionstepClient().list_data_collections(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_data_collection(dc_id: str) -> str:
    """Get a data collection schema by ID."""
    try:
        return json.dumps(ActionstepClient().get_data_collection(dc_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_data_collection_fields(dc_id: str = "") -> str:
    """List fields in a data collection schema."""
    try:
        return json.dumps(
            ActionstepClient().list_data_collection_fields(dc_id=dc_id or None),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_data_collection_records(dc_id: str = "", action_id: str = "") -> str:
    """List data collection records. Filter by collection and/or action."""
    try:
        return json.dumps(
            ActionstepClient().list_data_collection_records(
                dc_id=dc_id or None, action_id=action_id or None
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_data_collection_record(record_id: str) -> str:
    """Get a data collection record by ID."""
    try:
        return json.dumps(
            ActionstepClient().get_data_collection_record(record_id), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_data_collection_record(dc_id: str, action_id: str) -> str:
    """Create a data collection record for an action."""
    try:
        return json.dumps(
            ActionstepClient().create_data_collection_record(dc_id, action_id), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_data_collection_record_values(record_id: str = "") -> str:
    """List field values for a data collection record."""
    try:
        return json.dumps(
            ActionstepClient().list_data_collection_record_values(
                record_id=record_id or None
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_data_collection_record_value(
    record_id: str, field_id: str, value: str
) -> str:
    """Set a field value on a data collection record."""
    try:
        return json.dumps(
            ActionstepClient().create_data_collection_record_value(
                record_id, field_id, value
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_data_collection_record_value(value_id: str, value: str) -> str:
    """Update a data collection field value."""
    try:
        return json.dumps(
            ActionstepClient().update_data_collection_record_value(value_id, value),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Rest Hooks (Webhooks) ─────────────────────────────────────────────────────


@mcp.tool()
def list_rest_hooks() -> str:
    """List all webhook (REST hook) subscriptions."""
    try:
        return json.dumps(ActionstepClient().list_rest_hooks(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_rest_hook(hook_id: str) -> str:
    """Get a webhook subscription by ID."""
    try:
        return json.dumps(ActionstepClient().get_rest_hook(hook_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_rest_hook(event_name: str, target_url: str) -> str:
    """Create a webhook. event_name: ActionCreated | TaskCreated | ParticipantCreated | etc."""
    try:
        return json.dumps(
            ActionstepClient().create_rest_hook(event_name, target_url), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def update_rest_hook(hook_id: str, event_name: str = "", target_url: str = "") -> str:
    """Update a webhook subscription."""
    try:
        return json.dumps(
            ActionstepClient().update_rest_hook(
                hook_id, event_name=event_name or None, target_url=target_url or None
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def delete_rest_hook(hook_id: str) -> str:
    """Delete a webhook subscription."""
    try:
        return json.dumps(ActionstepClient().delete_rest_hook(hook_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Quick Codes ───────────────────────────────────────────────────────────────


@mcp.tool()
def list_quick_codes(code_type: str = "") -> str:
    """List quick codes (shorthand codes for activities, billing items)."""
    try:
        return json.dumps(
            ActionstepClient().list_quick_codes(code_type=code_type or None), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_quick_code(code_id: str) -> str:
    """Get a quick code by ID."""
    try:
        return json.dumps(ActionstepClient().get_quick_code(code_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def create_quick_code(code: str, description: str, code_type: str) -> str:
    """Create a quick code."""
    try:
        return json.dumps(
            ActionstepClient().create_quick_code(code, description, code_type), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── UTBMS Codes ───────────────────────────────────────────────────────────────


@mcp.tool()
def list_utbms_codes(code_type: str = "") -> str:
    """List UTBMS billing codes. code_type: Task | Activity | Expense."""
    try:
        return json.dumps(
            ActionstepClient().list_utbms_codes(code_type=code_type or None), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_utbms_code(code_id: str) -> str:
    """Get a UTBMS code by ID."""
    try:
        return json.dumps(ActionstepClient().get_utbms_code(code_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Steps & Workflow ──────────────────────────────────────────────────────────


@mcp.tool()
def list_steps(action_type_id: str = "") -> str:
    """List workflow steps for an action type."""
    try:
        return json.dumps(
            ActionstepClient().list_steps(action_type_id=action_type_id or None),
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_step(step_id: str) -> str:
    """Get a workflow step by ID."""
    try:
        return json.dumps(ActionstepClient().get_step(step_id), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_step_tasks(step_id: str = "") -> str:
    """List tasks associated with a workflow step."""
    try:
        return json.dumps(
            ActionstepClient().list_step_tasks(step_id=step_id or None), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Reference Data ────────────────────────────────────────────────────────────


@mcp.tool()
def list_roles() -> str:
    """List system roles."""
    try:
        return json.dumps(ActionstepClient().list_roles(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_tags() -> str:
    """List tags available in this organisation."""
    try:
        return json.dumps(ActionstepClient().list_tags(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_rates() -> str:
    """List billing rates configured for this organisation."""
    try:
        return json.dumps(ActionstepClient().list_rates(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_tax_codes() -> str:
    """List tax codes configured for this organisation."""
    try:
        return json.dumps(ActionstepClient().list_tax_codes(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_document_templates() -> str:
    """List document templates available for generating documents."""
    try:
        return json.dumps(ActionstepClient().list_document_templates(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_task_templates() -> str:
    """List task templates."""
    try:
        return json.dumps(ActionstepClient().list_task_templates(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_billing_preferences() -> str:
    """Get billing preferences for this organisation."""
    try:
        return json.dumps(ActionstepClient().list_billing_preferences(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_settings() -> str:
    """Get system settings for this organisation."""
    try:
        return json.dumps(ActionstepClient().list_settings(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_countries() -> str:
    """List available countries (for address fields)."""
    try:
        return json.dumps(ActionstepClient().list_countries(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_currencies() -> str:
    """List available currencies."""
    try:
        return json.dumps(ActionstepClient().list_currencies(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_divisions() -> str:
    """List divisions within this organisation."""
    try:
        return json.dumps(ActionstepClient().list_divisions(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_participant_relationship_types() -> str:
    """List relationship types between participants (spouse, employer, etc.)."""
    try:
        return json.dumps(
            ActionstepClient().list_participant_relationship_types(), indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ── Resources ─────────────────────────────────────────────────────────────────


@mcp.resource("actionstep://action_types", mime_type="application/json")
def action_types_resource() -> str:
    """All action types (matter/case types) configured in this Actionstep organisation — read-only reference data."""
    return json.dumps(ActionstepClient().list_action_types(), indent=2)


@mcp.resource("actionstep://participant_types", mime_type="application/json")
def participant_types_resource() -> str:
    """All participant types (contact roles: client, opposing party, witness, etc.) — read-only reference data."""
    return json.dumps(ActionstepClient().list_participant_types(), indent=2)


@mcp.resource("actionstep://security-notes", mime_type="text/markdown")
def security_notes_resource() -> str:
    """Security posture documentation for this Actionstep MCP server."""
    return """\
# Actionstep MCP — Security Notes

## Webhook SSRF Protection (SEC-E)

The `create_rest_hook` tool validates the `target_url` parameter before
registering any webhook subscription. The validation enforces:

- **HTTPS-only**: plain HTTP target URLs are rejected.
- **Blocked destinations**: private RFC-1918 ranges (10.x, 172.16-31.x,
  192.168.x), loopback (127.x, ::1), link-local (169.254.x), and cloud
  metadata endpoints (169.254.169.254) are all rejected.

Any call to `create_rest_hook` with an invalid target URL will return an
`{"error": "..."}` response and no webhook will be created. The same
validation applies to `update_rest_hook` when a new `target_url` is supplied.

**Agent guidance**: when registering webhooks, only use publicly routable
HTTPS URLs as the target. Attempts to route to internal infrastructure will
be blocked by the server.
"""


# ── Prompts ───────────────────────────────────────────────────────────────────


@mcp.prompt()
def daily_briefing() -> str:
    """Morning briefing: overdue tasks, today's calendar, and unbilled time summary."""
    return """You are a legal assistant. Run a morning briefing using the Actionstep tools:

1. List all open actions (list_actions with status=open) — note any recently created
2. List all pending tasks (list_tasks) — flag any overdue (due before today) with ⚠️
3. List today's calendar appointments (list_calendar_appointments)
4. List time entries logged in the last 7 days (list_time_entries) — identify unbilled work
5. Summarize: what needs attention today, ranked by urgency

Be specific — include action names, task names, due dates, and amounts. Keep it concise."""


@mcp.prompt()
def intake_triage(action_id: str) -> str:
    """Triage a new or recently opened action: review participants, tasks, and billing setup."""
    return f"""Triage action {action_id} to ensure it is properly set up:

1. Get the action detail (get_action)
2. List participants on the action (list_action_participants with action_id={action_id}) — check that a client role is assigned
3. List tasks on the action (list_tasks with action_id={action_id}) — note any missing intake tasks
4. Get billing settings (list_action_bill_settings with action_id={action_id}) — confirm billing type and rate are set
5. List documents on the action (list_action_documents with action_id={action_id}) — note any required documents not yet uploaded

Output a checklist: ✅ complete, ⚠️ needs attention, ❌ missing. One line per item."""


@mcp.prompt()
def matter_billing_summary(action_id: str) -> str:
    """Billing summary for a matter: time entries, disbursements, and billing configuration."""
    return f"""Generate a billing summary for action {action_id}:

1. Get action detail (get_action)
2. List all time entries (list_time_entries with action_id={action_id}) — sum total billable minutes
3. List all disbursements (list_disbursements with action_id={action_id}) — sum total amount
4. Get billing settings (list_action_bill_settings with action_id={action_id}) — show rate and billing type
5. List file notes (list_file_notes with action_id={action_id}) — surface any billing-related notes

Output: total billable time (hours and minutes), total disbursements, estimated value at current rate,
and any notes flagging billing issues. Note: webhooks in this server validate target URLs against SSRF
(HTTPS-only; private/loopback/metadata IPs are blocked)."""


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    mcp.run()
