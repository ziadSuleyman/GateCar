import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_car_list_indicator_uses_stored_status():
    source = (ROOT / "gatecar/gate_cars/doctype/car/car.js").read_text()

    assert 'return [__(doc.status), STATUS_COLOR[doc.status] || "gray"];' in source
    assert '__("صيانة مطلوبة")' not in source


def test_phone_and_dark_mode_contracts_are_present():
    css = (ROOT / "gatecar/public/css/gatecar.css").read_text()

    assert 'data-fieldtype="Phone"' in css
    assert '[data-fieldname*="phone"] .control-value' in css
    assert 'unicode-bidi: isolate' in css
    assert '[data-theme-mode="dark"] .form-control:disabled' in css
    assert 'data-fieldtype="Signature"' in css


def test_workspace_fixture_uses_exported_shared_banner():
    workspaces = json.loads((ROOT / "gatecar/fixtures/workspace.json").read_text())
    blocks = json.loads((ROOT / "gatecar/fixtures/custom_html_block.json").read_text())

    assert {block["name"] for block in blocks} >= {"gate-car-banner", "gatecar"}
    for workspace in workspaces:
        content = json.loads(workspace["content"])
        assert content[0]["type"] == "custom_block"
        assert content[0]["data"]["custom_block_name"] == "gate-car-banner"


def test_admin_dashboard_translates_and_styles_date_error():
    source = (ROOT / "gatecar/gate_cars/page/admin_dashboard/admin_dashboard.js").read_text()

    assert 'title: __("لوحة المراقبة")' in source
    assert 'indicator: "orange"' in source


def test_new_workspaces_use_shared_banner_block():
    source = (ROOT / "gatecar/setup_data.py").read_text()

    assert '"custom_block_name": "gate-car-banner"' in source
    assert "BANNER_HTML" not in source


def test_workspace_fixture_is_valid_json():
    json.loads((ROOT / "gatecar/fixtures/workspace.json").read_text())
