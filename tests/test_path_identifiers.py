"""Regression coverage for every ID-bearing client path call site.

The transport boundary is replaced, so rejected identifiers must fail before
any HTTP call, including a preliminary read in a merge/update operation.
"""

import inspect
from unittest.mock import Mock

import pytest
import requests

from actionstep_mcp.client import ActionstepClient

CASES = [
    ("get_user", "user_id"),
    ("get_action", "action_id"),
    ("create_action", "action_type_id"),
    ("update_action", "action_id"),
    ("get_action_type", "action_type_id"),
    ("get_action_bill_settings", "settings_id"),
    ("update_action_bill_settings", "settings_id"),
    ("get_action_document", "document_id"),
    ("update_action_document", "document_id"),
    ("delete_action_document", "document_id"),
    ("get_action_folder", "folder_id"),
    ("update_action_folder", "folder_id"),
    ("delete_action_folder", "folder_id"),
    ("get_action_participant", "ap_id"),
    ("update_action_participant", "ap_id"),
    ("delete_action_participant", "ap_id"),
    ("update_action_permissions", "perm_id"),
    ("get_action_rate", "rate_id"),
    ("update_action_rate", "rate_id"),
    ("delete_action_rate", "rate_id"),
    ("get_action_type_folder", "folder_id"),
    ("update_action_type_folder", "folder_id"),
    ("delete_action_type_folder", "folder_id"),
    ("get_participant", "participant_id"),
    ("update_participant", "participant_id"),
    ("delete_participant", "participant_id"),
    ("get_participant_type", "pt_id"),
    ("update_participant_type", "pt_id"),
    ("get_participant_relationship_type", "rt_id"),
    ("update_participant_relationship_type", "rt_id"),
    ("get_contact_relationship", "cr_id"),
    ("update_contact_relationship", "cr_id"),
    ("get_contact_document", "doc_id"),
    ("update_contact_document", "doc_id"),
    ("delete_contact_document", "doc_id"),
    ("get_contact_folder", "folder_id"),
    ("update_contact_folder", "folder_id"),
    ("delete_contact_folder", "folder_id"),
    ("get_contact_note", "note_id"),
    ("update_contact_note", "note_id"),
    ("delete_contact_note", "note_id"),
    ("get_task", "task_id"),
    ("update_task", "task_id"),
    ("delete_task", "task_id"),
    ("get_file_note", "note_id"),
    ("update_file_note", "note_id"),
    ("delete_file_note", "note_id"),
    ("get_scratch_note", "note_id"),
    ("update_scratch_note", "note_id"),
    ("delete_scratch_note", "note_id"),
    ("get_time_record", "record_id"),
    ("update_time_record", "record_id"),
    ("delete_time_record", "record_id"),
    ("get_time_entry", "entry_id"),
    ("update_time_entry", "entry_id"),
    ("delete_time_entry", "entry_id"),
    ("get_time_record_activity", "activity_id"),
    ("get_disbursement", "disbursement_id"),
    ("update_disbursement", "disbursement_id"),
    ("delete_disbursement", "disbursement_id"),
    ("get_calendar_appointment", "appt_id"),
    ("update_calendar_appointment", "appt_id"),
    ("delete_calendar_appointment", "appt_id"),
    ("get_email", "email_id"),
    ("update_email", "email_id"),
    ("delete_email", "email_id"),
    ("get_email_association", "assoc_id"),
    ("delete_email_association", "assoc_id"),
    ("get_email_attachment", "attach_id"),
    ("delete_email_attachment", "attach_id"),
    ("get_sms", "sms_id"),
    ("update_sms", "sms_id"),
    ("get_phone_record", "record_id"),
    ("update_phone_record", "record_id"),
    ("delete_phone_record", "record_id"),
    ("get_quick_code", "code_id"),
    ("update_quick_code", "code_id"),
    ("get_data_collection", "dc_id"),
    ("update_data_collection", "dc_id"),
    ("delete_data_collection", "dc_id"),
    ("get_data_collection_field", "field_id"),
    ("update_data_collection_field", "field_id"),
    ("delete_data_collection_field", "field_id"),
    ("get_data_collection_record", "record_id"),
    ("update_data_collection_record", "record_id"),
    ("delete_data_collection_record", "record_id"),
    ("get_data_collection_record_value", "value_id"),
    ("update_data_collection_record_value", "value_id"),
    ("delete_data_collection_record_value", "value_id"),
    ("get_rest_hook", "hook_id"),
    ("update_rest_hook", "hook_id"),
    ("delete_rest_hook", "hook_id"),
    ("get_step", "step_id"),
    ("get_role", "role_id"),
    ("get_tag", "tag_id"),
    ("get_rate", "rate_id"),
    ("get_tax_code", "code_id"),
    ("get_utbms_code", "code_id"),
    ("update_utbms_code", "code_id"),
    ("delete_utbms_code", "code_id"),
    ("get_document_template", "template_id"),
    ("get_task_template", "template_id"),
    ("update_billing_preferences", "pref_id"),
    ("update_settings", "setting_id"),
    ("get_country", "country_id"),
    ("get_currency", "currency_id"),
    ("get_division", "division_id"),
    ("get_unit", "unit_id"),
    ("get_node", "node_id"),
]


def client_and_arguments(method):
    client = object.__new__(ActionstepClient)
    response = requests.Response()
    response.status_code = 200
    response._content = b'{"id": "normal-id", "success": true}'
    request = Mock(return_value={"id": "normal-id", "success": True})
    send = Mock(return_value=response)
    client._request = request
    client._send = send
    kwargs = {}
    for key, param in inspect.signature(getattr(client, method)).parameters.items():
        if param.default is not inspect.Parameter.empty or param.kind in (
            inspect.Parameter.VAR_KEYWORD,
            inspect.Parameter.VAR_POSITIONAL,
        ):
            continue
        annotation = str(param.annotation)
        if "dict" in annotation or key in {"body", "fields", "overlay"}:
            kwargs[key] = {"name": "probe"}
        elif "int" in annotation:
            kwargs[key] = 1
        else:
            kwargs[key] = "normal-id"
    if "resource" in kwargs:
        kwargs["resource"] = "matters"
    if "path" in kwargs:
        kwargs["path"] = "/tasks"
    if method == "tag_call":
        kwargs["tag_ids"] = [1]
    if method == "update_contact" and ActionstepClient.__name__ == "CloudTalkClient":
        kwargs["name"] = "probe"
    return client, kwargs, request, send


@pytest.mark.parametrize(("method", "parameter"), CASES)
@pytest.mark.parametrize(
    "value",
    ["", ".", "..", "a/../b", "%2e%2e", "a?b", "a#b", "a\\b", " ", "a\n", None, True],
)
def test_invalid_path_id_never_reaches_transport(method, parameter, value):
    client, kwargs, request, send = client_and_arguments(method)
    kwargs[parameter] = value
    with pytest.raises(Exception) as caught:
        getattr(client, method)(**kwargs)
    error = caught.value
    assert parameter in str(error) or getattr(error, "field", None) == parameter
    assert "identifier" in str(error) or "identifier" in getattr(error, "expected", "")
    request.assert_not_called()
    send.assert_not_called()


@pytest.mark.parametrize(("method", "parameter"), CASES)
@pytest.mark.parametrize(
    "value", ["normal-id", "550e8400-e29b-41d4-a716-446655440000", "123", 123]
)
def test_normal_path_id_reaches_transport(method, parameter, value):
    client, kwargs, request, send = client_and_arguments(method)
    kwargs[parameter] = value
    getattr(client, method)(**kwargs)
    calls = request.call_args_list + send.call_args_list
    assert calls
    assert any(str(value) in str(call) for call in calls)
