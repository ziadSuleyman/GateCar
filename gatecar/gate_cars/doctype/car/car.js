// Copyright (c) 2026, Ziad Suleyman and contributors
// For license information, please see license.txt

frappe.ui.form.on("Car", {
	refresh(frm) {
		add_connection_log_buttons(frm);
	},
});

/* ── Connection "view log" buttons ──────────────────────────────────────
 * Add a list icon next to the + on the Periodic Maintenance and
 * المصاريف العامة (Car Expense) connection cards, opening that doctype's
 * list filtered by the current car.
 */
const CONNECTION_LOG_TARGETS = {
	"Periodic Maintenance": "periodic-maintenance",
	"Car Expense": "car-expense",
};

function add_connection_log_buttons(frm) {
	if (frm.is_new() || !frm.doc.name) return;
	// Match the desk route prefix actually in use ("app" or "desk").
	const app_base = window.location.pathname.split("/")[1] || "app";
	const car = frm.doc.name;

	let tries = 0;
	const timer = setInterval(() => {
		tries += 1;
		const $scope = $(frm.wrapper);
		let all_present = true;

		Object.entries(CONNECTION_LOG_TARGETS).forEach(([doctype, slug]) => {
			const $card = $scope.find(`.document-link[data-doctype="${doctype}"]`);
			if (!$card.length) {
				all_present = false;
				return;
			}
			if ($card.find(".gc-log-link").length) return; // already added

			const href = `/${app_base}/${slug}/view/list?car=${encodeURIComponent(car)}`;
			const $btn = $(
				`<a class="gc-log-link btn btn-secondary btn-xs icon-btn" href="${href}" ` +
					`title="${__("عرض السجل")}" style="margin-inline-start:4px;">` +
					`${frappe.utils.icon("list", "sm")}</a>`
			);
			$btn.on("click", (e) => {
				e.preventDefault();
				frappe.set_route("List", doctype, { car: car });
			});
			$card.find(".btn-new").after($btn);
		});

		if (all_present || tries >= 20) clearInterval(timer);
	}, 250);
}

/* ── List View Settings ─────────────────────────────────────────────── */

const STATUS_COLOR = {
	"متوفر": "green",
	"محجوز": "orange",
	"مؤجر": "blue",
	"داخل الصيانة": "red",
	"جاهز للتسليم": "purple",
	"مجمدة": "gray",
};

frappe.listview_settings["Car"] = {
	add_fields: ["current_odometer", "next_oil_change", "status"],

	// Colour the "status" column value as a coloured pill per status.
	formatters: {
		status(value) {
			if (!value) return "";
			const color = STATUS_COLOR[value] || "gray";
			return `<span class="indicator-pill ${color}">${frappe.utils.escape_html(value)}</span>`;
		},
	},

	get_indicator(doc) {
		return [__(doc.status), STATUS_COLOR[doc.status] || "gray"];
	},

	refresh(listview) {
		_style_maintenance_rows(listview);
	},

	onload(listview) {
		_style_maintenance_rows(listview);
	},
};

// Colour red any car that has an OPEN maintenance request (periodic/insurance/registration),
// is already داخل الصيانة, or has crossed its km service threshold.
function _style_maintenance_rows(listview) {
	const cars = (listview.result || []).map((d) => d.name);
	if (!cars.length) return;

	// A car is "under maintenance" if it has an open km service (Periodic Maintenance)
	// OR an open date-renewal expense (Car Expense: تأمين/تسجيل).
	Promise.all([
		frappe.db.get_list("Periodic Maintenance", {
			filters: { car: ["in", cars], docstatus: 0 },
			fields: ["car"],
			limit: 0,
		}),
		frappe.db.get_list("Car Expense", {
			filters: {
				car: ["in", cars],
				docstatus: 0,
				expense_type: ["in", ["تأمين إلزامي", "تأمين شامل", "تسجيل"]],
			},
			fields: ["car"],
			limit: 0,
		}),
	])
		.then(([pm_rows, exp_rows]) => {
			const flagged = new Set([...pm_rows, ...exp_rows].map((r) => r.car));
			(listview.result || []).forEach((doc) => {
				const km_due =
					doc.next_oil_change > 0 && doc.current_odometer >= doc.next_oil_change;
				if (flagged.has(doc.name) || doc.status === "داخل الصيانة" || km_due) {
					const $row = listview.$frappe_list
						? listview.$frappe_list.find(`[data-name="${CSS.escape(doc.name)}"]`)
						: $(`[data-name="${CSS.escape(doc.name)}"]`);
					$row.css({
						"background-color": "rgba(229, 57, 53, 0.10)",
						"border-right": "3px solid #e53935",
					});
				}
			});
		});
}
