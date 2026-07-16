#!/usr/bin/env python3
"""
Generator for the "نموذج تسليم مركبة" (Vehicle Handover) print format.

Builds a fully table-based HTML layout (wkhtmltopdf-safe: NO flexbox / grid),
with all icons embedded as inline, theme-colored SVG (from
public/images/SVG/Gc icons-NN.svg) and a CSS-drawn checkbox system that is
filled from the document data.

Run from the bench root with the bench python:

    env/bin/python3 apps/gatecar/gatecar/gate_cars/doctype/car_inspection/print_format/build_vehicle_handover.py

It writes the HTML to `vehicle_handover.html` next to this file and, if
`--save` is passed, upserts the print format record directly into the DB.
"""

import base64
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "public", "images", "Car Inspection"))
SVG_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "public", "images", "SVG"))

DOCTYPE = "Car Inspection"

# Two themed variants of the same layout:
#   - Handover (تسليم): green accent
#   - Receipt  (استلام): navy accent
THEMES = [
	{
		"name": "نموذج تسليم مركبة",
		"title": "نموذج تسليم مركبة",
		"file": "vehicle_handover.html",
		"accent": "#2e7d32",  # green
		"accent_lt": "#cfe0cf",  # light green (borders)
		"accent_bg": "#eef2ee",  # very light green (header tint)
	},
	{
		"name": "نموذج استلام مركبة",
		"title": "نموذج استلام مركبة",
		"file": "vehicle_receipt.html",
		"accent": "#1e3a5f",  # navy
		"accent_lt": "#c5d0e0",  # light navy (borders)
		"accent_bg": "#eef1f6",  # very light navy (header tint)
	},
]


def b64(path: str) -> str:
	with open(path, "rb") as f:
		return base64.b64encode(f.read()).decode()


LOGO_HD = b64(os.path.join(IMG_DIR, "logo_hd.png"))

FONT_DIR = os.path.join(HERE, "fonts")
FONT_REG = b64(os.path.join(FONT_DIR, "Almarai-Regular.ttf"))
FONT_BOLD = b64(os.path.join(FONT_DIR, "Almarai-Bold.ttf"))

FONT_FACE = (
	"@font-face { font-family: 'Almarai'; font-weight: 400; font-style: normal; "
	"src: url(data:font/truetype;charset=utf-8;base64," + FONT_REG + ") format('truetype'); }\n"
	"@font-face { font-family: 'Almarai'; font-weight: 700; font-style: normal; "
	"src: url(data:font/truetype;charset=utf-8;base64," + FONT_BOLD + ") format('truetype'); }\n"
	"@font-face { font-family: 'Almarai'; font-weight: 800; font-style: normal; "
	"src: url(data:font/truetype;charset=utf-8;base64," + FONT_BOLD + ") format('truetype'); }\n"
)


# ── GateCar brand icon set (public/images/SVG/Gc icons-NN.svg) ──────────────
# Pre-rasterized to PNG (via cairosvg) and embedded as base64 <img>, exactly
# like the print format's other illustrations always were. Inline <svg> was
# tried first, but wkhtmltopdf's bundled WebKit renders it unreliably below
# ~25px — paths become near-invisible in a small checklist-row cell — so
# rasterizing avoids that failure mode entirely regardless of display size.
# The reference design already uses plain black line art for these
# illustrations (not theme-tinted), so no per-theme colour variant is needed.
def load_icon(num: int, px: int = 256) -> str:
	import cairosvg

	path = os.path.join(SVG_DIR, f"Gc icons-{num:02d}.svg")
	png_bytes = cairosvg.svg2png(url=path, output_width=px, output_height=px)
	return f'<img src="data:image/png;base64,{base64.b64encode(png_bytes).decode()}" class="ic-img">'


ICON_FLEET = load_icon(1)  # multi-car illustration → exterior section
ICON_DASHBOARD = load_icon(2)  # dashboard illustration → interior section + dashboard row
ICON_FUEL = load_icon(3)  # fuel gauge → fuel box
ICON_PEN = load_icon(4)  # pen signing → signature labels
ICON_CAR_BODY = load_icon(5)  # car silhouette → generic body-panel rows
ICON_PHONE = load_icon(6)  # phone handset → meta "رقم الهاتف"
ICON_EV_PLUG = load_icon(7)  # EV charging plug → "وصلة شحن السيارة"
ICON_JACK = load_icon(8)  # car jack/lift → "رافعة السيارة"
ICON_TRIANGLE = load_icon(9)  # warning triangle → "مثلث الأمان"
ICON_HEADLIGHT = load_icon(10)  # headlight beam → lights/signals rows
ICON_ENGINE = load_icon(11)  # engine → engine warning/oil rows
ICON_WHEEL = load_icon(12)  # wheel/tire → tire rows
ICON_WIPER = load_icon(13)  # windshield wipers → glass/window rows
ICON_FIRSTAID = load_icon(14)  # first aid kit → "حقيبة الإسعافات الأولية"
ICON_PLATE = load_icon(15)  # license plate → plate rows/meta
ICON_CAL_CLOCK = load_icon(16)  # calendar + clock → meta "التاريخ والوقت"
ICON_CAL = load_icon(17)  # plain calendar → meta "رقم الحجز"
ICON_PERSON = load_icon(18)  # person → meta "اسم العميل"

# Kept from the previous hand-drawn Lucide set: no brand icon fits a plain
# speed/odometer gauge (icon 03 above is specifically a *fuel* gauge).
_SVG = (
	'<svg viewBox="0 0 24 24" fill="none" stroke="__ACCENT__" stroke-width="2" '
	'stroke-linecap="round" stroke-linejoin="round">'
)
ICON_GAUGE = _SVG + '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/></svg>'


# ── Checkbox helpers ──
def box(field: str, val: str) -> str:
	"""CSS checkbox filled when doc.<field> == val."""
	return (
		"{% if doc." + field + ' == "' + val + '" %}'
		'<span class="bx on">&#10003;</span>'
		'{% else %}<span class="bx"></span>{% endif %}'
	)


def chkbox(cond: str) -> str:
	return (
		"{% if " + cond + ' %}<span class="bx on">&#10003;</span>'
		'{% else %}<span class="bx"></span>{% endif %}'
	)


def row(field: str, label: str, icon: str = "") -> str:
	icon_cell = f'<span class="ric">{icon}</span>' if icon else ""
	return (
		"<tr>"
		f'<td class="ic">{icon_cell}</td>'
		f'<td class="nm">{label}</td>'
		f'<td class="cb">{box(field, "سليم")}</td>'
		f'<td class="cb">{box(field, "متضرر")}</td>'
		f'<td class="cb">{box(field, "غير متاح")}</td>'
		"</tr>"
	)


def field(icon: str, label: str, value_expr: str) -> str:
	return (
		'<table class="fld"><tr>'
		f'<td class="f-ico">{icon}</td>'
		f'<td class="f-lbl">{label}</td>'
		f'<td class="f-val">{value_expr}</td>'
		"</tr></table>"
	)


THEAD = (
	"<tr>"
	'<th class="th-ic"></th>'
	'<th class="th-nm">البند</th>'
	'<th class="th-ok">سليم</th>'
	'<th class="th-dmg">متضرر</th>'
	'<th class="th-na">غير&nbsp;متاح</th>'
	"</tr>"
)

# ── Exact labels from the reference design, each paired with the brand icon
# that best matches it. Rows with no clear match get no icon rather than a
# forced/confusing one. ──
EXT_ROWS = "".join(
	[
		row("front_bumper", "الصدام الأمامي", ICON_CAR_BODY),
		row("rear_bumper", "الصدام الخلفي", ICON_CAR_BODY),
		row("left_side", "الجانب الأيسر", ICON_CAR_BODY),
		row("right_side", "الجانب الأيمن", ICON_CAR_BODY),
		row("roof", "السقف", ICON_CAR_BODY),
		row("front_glass", "الزجاج الأمامي", ICON_WIPER),
		row("windows_mirrors", "النوافذ والمرايا", ICON_WIPER),
		row("lights", "الأضواء (الأمامية والخلفية)", ICON_HEADLIGHT),
		row("signals", "المصابيح والإشارات", ICON_HEADLIGHT),
		row("license_plate_check", "لوحة المركبة", ICON_PLATE),
	]
)

INT_ROWS = "".join(
	[
		row("seats", "المقاعد (نظيفة وخالية من التمزقات)"),
		row("dashboard_check", "لوحة القيادة"),
		row("doors_locks", "الأبواب والأقفال الداخلية"),
		row("floor_carpet", "الأرضية والسجاد"),
		row("front_glass", "الزجاج الأمامي", ICON_WIPER),
		row("ac_heating", "نظام التكييف والتدفئة"),
		row("audio_system", "النظام الصوتي والوسائط"),
		row("electric_windows", "عمل النوافذ الكهربائية", ICON_WIPER),
		row("interior_lighting", "الإضاءة الداخلية"),
		row("no_odors", "خلو المركبة من الروائح غير المرغوبة"),
		row("no_smoking", "حرق سجائر"),
	]
)

MECH_ROWS = "".join(
	[
		row("engine_warning", "مؤشر أعطال المحرك", ICON_ENGINE),
		row("engine_oil", "زيت المحرك", ICON_ENGINE),
		row("tires", "مستوى الإطارات", ICON_WHEEL),
		row("spare_tire_tools", "البطاريات الاحتياطية وأدواته", ICON_WHEEL),
		row("first_aid_kit", "حقيبة الإسعافات الأولية", ICON_FIRSTAID),
		row("car_jack", "رافعة السيارة", ICON_JACK),
		row("charger_cable", "وصلة شحن السيارة", ICON_EV_PLUG),
		row("safety_triangle", "مثلث الأمان", ICON_TRIANGLE),
	]
)

DOTS2 = '<div class="dots"></div><div class="dots"></div>'


def notes_block(field: str) -> str:
	"""Render the entered notes for a section; fall back to blank dotted lines."""
	return (
		'<div class="notes-lbl">ملاحظات إضافية:</div>'
		"{% if doc." + field + " %}"
		'<div class="notes-val">{{ doc.' + field + " }}</div>"
		"{% else %}" + DOTS2 + "{% endif %}"
	)


def build_html(theme: dict) -> str:
	css = """<style>
__FONT_FACE__
@page { size: A4 portrait; margin: 6mm 7mm; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Almarai', sans-serif !important; direction: rtl; color: #1a1a1a; }
.ci-wrap, .ci-wrap * { font-family: 'Almarai', sans-serif !important; }
.ci-wrap { width: 100%; font-size: 8px; line-height: 1.1; }
.ci-wrap * { line-height: 1.1 !important; }
table { border-collapse: collapse; }

/* Header */
.hdr { width: 100%; margin-bottom: 3px; }
.hdr > tbody > tr > td { vertical-align: middle; padding-bottom: 2px; }
.hdr .logo { text-align: left; width: 46%; }
.hdr .logo img { height: 40px; }
.hdr .tag { font-size: 8px; font-weight: 700; color: #4caf50; margin-top: 1px; text-align: left; letter-spacing: .2px; }
.hdr .ttl { text-align: right; }
.hdr .ttl h1 { font-size: 18px; font-weight: 900; color: __ACCENT__; margin-bottom: 3px; }
.hdr .serial { font-size: 9px; color: #333; font-weight: 700; }
.serial-line { display: inline-block; min-width: 95px; border-bottom: 1px solid #444; font-weight: 800; text-align: center; }
.hdr-rule { height: 2px; background: __ACCENT__; border: none; margin: 1px 0 4px; }

/* Meta */
.meta { width: 100%; border: 1px solid __ACCENT_LT__; border-radius: 4px; margin-bottom: 4px; }
.meta > tbody > tr > td { padding: 1px 10px !important; width: 50%; vertical-align: middle; }
.fld { width: 100%; }
.fld td { vertical-align: middle; padding: 0 !important; height: 13px; }
.fld .f-ico { width: 16px; padding-left: 5px !important; }
.fld .f-ico svg, .fld .f-ico img { width: 11px; height: 11px; display: block; }
.fld .f-lbl { white-space: nowrap; font-weight: 700; color: #333; font-size: 8.5px; padding-left: 5px !important; }
.fld .f-val { width: 100%; border-bottom: 1px dotted #bbb; font-size: 8.5px; color: #111; text-align: center; }

/* Section */
.sec { width: 100%; border: 1.2px solid __ACCENT__; border-radius: 4px; margin-bottom: 3px; }
.sec-hd { background: __ACCENT__; color: #fff; font-weight: 800; font-size: 8.5px; padding: 2px 8px; }
.sec-bd { padding: 2px; }
.layout { width: 100%; }
.layout > tbody > tr > td { vertical-align: top; }

/* Images (section illustrations, from the GateCar brand icon set) */
.img-cell { text-align: center; padding: 1px; }
.img-cell img { max-width: 100%; width: auto; height: 108px; }

/* Checklist */
.chk { width: 100%; }
.chk th { border: 1px solid #cfcfcf; padding: 1px 2px !important; font-size: 7px; font-weight: 700; text-align: center; line-height: 1.05 !important; }
.chk th.th-ic  { background: __ACCENT_BG__; width: 15px; }
.chk th.th-nm { background: __ACCENT_BG__; text-align: right; padding: 1px 5px 1px 2px !important; color: #333; }
.chk th.th-ok  { background: __ACCENT__; color: #fff; width: 28px; }
.chk th.th-dmg { background: #c62828; color: #fff; width: 28px; }
.chk th.th-na  { background: #6d6d6d; color: #fff; width: 32px; }
.chk td { border: 1px solid #e2e2e2; padding: 0px 5px !important; height: 13px; line-height: 1 !important; }
.chk td.ic { text-align: center; padding: 0 !important; }
.chk td.ic .ric { display: inline-block; width: 10px; height: 10px; vertical-align: middle; }
.chk td.ic .ric img { width: 10px; height: 10px; display: block; }
.chk td.nm { font-size: 7px; }
.chk td.cb { text-align: center; }

/* CSS checkbox */
.bx { display: inline-block; width: 7px; height: 7px; border: 1px solid #888; border-radius: 2px; line-height: 6px !important; text-align: center; font-size: 5.5px; color: transparent; vertical-align: middle; }
.bx.on { background: __ACCENT__; border-color: __ACCENT__; color: #fff; font-weight: 900; }

.dots { border-bottom: 1px dotted #bbb; height: 8px; margin-top: 1px; }
.notes-lbl { font-size: 7px; color: #555; margin-top: 1px; }
.notes-val { font-size: 8px; color: #222; margin-top: 1px; border-bottom: 1px dotted #bbb; min-height: 9px; word-wrap: break-word; }

/* Fuel */
.fuel { border: 1px solid __ACCENT_LT__; border-radius: 4px; padding: 3px 6px; height: 100%; }
.fuel-hd { font-weight: 800; color: __ACCENT__; font-size: 8px; margin-bottom: 2px; }
.fuel-gauge { text-align: center; margin-bottom: 2px; }
.fuel-gauge img { height: 34px; width: auto; }
.fuel-line { font-size: 7.5px; margin: 1.5px 0; }
.fuel-line .bx { vertical-align: middle; margin-left: 3px; }
.fuel-opts { margin-top: 1px; }
.fuel-opts span.opt { margin-left: 12px; font-size: 7.5px; white-space: nowrap; }
.fuel-sep { border-top: 1px dotted #ccc; margin: 2px 0; }
.fuel-val { font-weight: 700; color: __ACCENT__; }

/* Damage */
.dmg-bd { padding: 3px 6px; }
.dmg-text { font-size: 8.5px; color: #222; margin-bottom: 3px; }

/* Signatures */
.sigs { width: 100%; margin-top: 4px; }
.sigs td { width: 50%; text-align: center; padding: 0 12px; }
.sig-lbl { font-size: 9px; font-weight: 700; color: __ACCENT__; margin-bottom: 3px; }
.sig-lbl svg, .sig-lbl img { width: 11px; height: 11px; vertical-align: middle; margin-left: 3px; }
.sig-area { border-bottom: 1px solid #222; height: 40px; text-align: center; }
.sig-area img { max-height: 38px; max-width: 140px; }
.sig-name { font-size: 7px; color: #999; margin-top: 2px; }

/* Footer */
.foot { width: 100%; margin-top: 6px; border-top: 1px solid #ddd; padding-top: 5px; text-align: center; }
.foot .msg { text-align: center; font-size: 8.5px; color: #444; }
.foot .msg b { color: __ACCENT__; display: block; font-size: 10px; }
</style>""".replace("__FONT_FACE__", FONT_FACE)

	body = f"""
<div class="ci-wrap">

<!-- HEADER -->
<table class="hdr"><tbody><tr>
  <td class="ttl">
    <h1>__TITLE__</h1>
    <div class="serial">الرقم التسلسلي: <span class="serial-line">{{{{ doc.name }}}}</span></div>
  </td>
  <td class="logo">
    <img src="data:image/png;base64,{LOGO_HD}" alt="GateCar">
    <div class="tag">We reach you wherever you are</div>
  </td>
</tr></tbody></table>
<hr class="hdr-rule">

<!-- META -->
<table class="meta"><tbody>
<tr>
  <td>{field(ICON_PERSON, "اسم العميل:", "{{ doc.customer_name or '' }}")}</td>
  <td>{field(ICON_CAL, "رقم الحجز:", "{{ doc.booking or '' }}")}</td>
</tr>
<tr>
  <td>{field(ICON_CAL_CLOCK, "التاريخ والوقت:", "{{ doc.inspection_date or '' }}")}</td>
  <td>{field(ICON_PLATE, "رقم المركبة / اللوحة:", "{{ doc.car or '' }} / {{ doc.plate_no or '' }}")}</td>
</tr>
<tr>
  <td>{field(ICON_GAUGE, "عداد الكيلومترات (كم):", "{{ doc.odometer or '' }}")}</td>
  <td>{field(ICON_PHONE, "رقم الهاتف:", "{{ doc.phone or '' }}")}</td>
</tr>
</tbody></table>

<!-- SECTION 1: EXTERNAL -->
<table class="sec"><tbody>
<tr><td class="sec-hd">1. الفحص الخارجي للمركبة</td></tr>
<tr><td class="sec-bd">
  <table class="layout"><tbody><tr>
    <td style="width:57%; padding-left:6px;">
      <table class="chk"><thead>{THEAD}</thead><tbody>{EXT_ROWS}</tbody></table>
      {notes_block("external_notes")}
    </td>
    <td class="img-cell" style="width:43%">
      {ICON_FLEET}
    </td>
  </tr></tbody></table>
</td></tr>
</tbody></table>

<!-- SECTION 2: INTERNAL -->
<table class="sec"><tbody>
<tr><td class="sec-hd">2. الفحص الداخلي للمركبة</td></tr>
<tr><td class="sec-bd">
  <table class="layout"><tbody><tr>
    <td style="width:57%; padding-left:6px;">
      <table class="chk"><thead>{THEAD}</thead><tbody>{INT_ROWS}</tbody></table>
      {notes_block("internal_notes")}
    </td>
    <td class="img-cell" style="width:43%">
      {ICON_DASHBOARD}
    </td>
  </tr></tbody></table>
</td></tr>
</tbody></table>

<!-- SECTION 3 + 4 -->
<table class="sec"><tbody>
<tr><td class="sec-hd">3. الفحص الميكانيكي وعناصر السلامة</td></tr>
<tr><td class="sec-bd">
  <table class="layout"><tbody><tr>
    <td style="width:62%; padding-left:6px;">
      <table class="chk"><thead>{THEAD}</thead><tbody>{MECH_ROWS}</tbody></table>
      {notes_block("mechanical_notes")}
    </td>
    <td style="width:38%">
      <div class="fuel">
        <div class="fuel-hd">4. الوقود والمستندات</div>
        <div class="fuel-gauge">{ICON_FUEL}</div>
        <div class="fuel-line">{chkbox("doc.fuel_level_agreed")} مستوى الوقود المتفق عليه</div>
        <div class="fuel-line">مستوى الوقود: <span class="fuel-val">{{{{ doc.fuel_level or '—' }}}}</span></div>
        <div class="fuel-sep"></div>
        <div class="fuel-line">نوع الوقود:</div>
        <div class="fuel-opts">
          <span class="opt">{chkbox("doc.fuel_type == 'بنزين'")} بنزين</span>
          <span class="opt">{chkbox("doc.fuel_type == 'ديزل'")} ديزل</span>
        </div>
        <div class="fuel-sep"></div>
        <div class="fuel-line">{chkbox("doc.documents_present")} وجود المستندات داخل المركبة
          <br><span style="color:#777; padding-right:16px;">(رخصة المركبة – التأمين)</span></div>
        <div class="fuel-sep"></div>
        <div class="fuel-line">{chkbox("doc.car_sanitized")} تعقيم السيارة</div>
        <div class="fuel-line">{chkbox("doc.water_bottles_present")} وجود عبوتي مياه</div>
      </div>
    </td>
  </tr></tbody></table>
</td></tr>
</tbody></table>

<!-- SECTION 5: DAMAGE -->
<table class="sec"><tbody>
<tr><td class="sec-hd">5. الملاحظات أو الأضرار الموجودة مسبقاً (إن وجدت)</td></tr>
<tr><td class="dmg-bd">
  <div class="dmg-text">{{{{ doc.pre_existing_damage or '' }}}}</div>
  <div class="dots"></div><div class="dots"></div><div class="dots"></div>
</td></tr>
</tbody></table>

<!-- SIGNATURES -->
<table class="sigs"><tbody><tr>
  <td>
    <div class="sig-lbl">{ICON_PEN} توقيع العميل</div>
    <div class="sig-area">{{% if doc.customer_signature %}}<img src="{{{{ doc.customer_signature }}}}">{{% endif %}}</div>
    <div class="sig-name">{{{{ doc.customer_name or '' }}}}</div>
  </td>
  <td>
    <div class="sig-lbl">{ICON_PEN} توقيع الموظف</div>
    <div class="sig-area">{{% if doc.employee_signature %}}<img src="{{{{ doc.employee_signature }}}}">{{% endif %}}</div>
    <div class="sig-name">&nbsp;</div>
  </td>
</tr></tbody></table>

<!-- FOOTER -->
<div class="foot">
  <div class="msg"><b>شكراً لاختياركم GateCar</b>نتمنى لكم قيادة آمنة.</div>
</div>

</div>"""
	html = css + body
	return (
		html.replace("__TITLE__", theme["title"])
		.replace("__ACCENT_LT__", theme["accent_lt"])
		.replace("__ACCENT_BG__", theme["accent_bg"])
		.replace("__ACCENT__", theme["accent"])
	)


def save_to_db(name: str, html: str):
	import json
	import pymysql

	bench_root = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "..", "..", ".."))
	cfg = json.load(open(os.path.join(bench_root, "sites", "carrent", "site_config.json")))
	db = pymysql.connect(
		host="mariadb",
		user=cfg["db_name"],
		password=cfg["db_password"],
		database=cfg["db_name"],
		charset="utf8mb4",
	)
	cur = db.cursor()
	cur.execute("SELECT name FROM `tabPrint Format` WHERE name=%s", (name,))
	exists = cur.fetchone()
	if exists:
		cur.execute(
			"""UPDATE `tabPrint Format`
            SET html=%s, custom_format=1, print_format_type='Jinja', disabled=0, modified=NOW()
            WHERE name=%s""",
			(html, name),
		)
	else:
		cur.execute(
			"""INSERT INTO `tabPrint Format`
            (name, creation, modified, owner, modified_by, doc_type, module,
             print_format_type, custom_format, standard, disabled, html, print_format_builder)
            VALUES (%s, NOW(), NOW(), 'Administrator', 'Administrator', %s, 'Gate Cars',
             'Jinja', 1, 'No', 0, %s, 0)""",
			(name, DOCTYPE, html),
		)
	db.commit()
	db.close()
	print(f"Saved '{name}' ({'updated' if exists else 'inserted'}) — {len(html)} chars")


if __name__ == "__main__":
	for theme in THEMES:
		html = build_html(theme)
		out = os.path.join(HERE, theme["file"])
		with open(out, "w", encoding="utf-8") as f:
			f.write(html)
		print(f"Wrote {out} ({len(html)} chars)")
		if "--save" in sys.argv:
			save_to_db(theme["name"], html)
