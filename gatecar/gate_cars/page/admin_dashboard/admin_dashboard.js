frappe.pages["admin-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("لوحة المراقبة"),
		single_column: true,
	});

	page.profit_month = "";
	page.profit_year = String(new Date().getFullYear());
	page.date_from = moment().startOf("month").format("YYYY-MM-DD");
	page.date_to = moment().endOf("month").format("YYYY-MM-DD");

	page.main.html('<div class="admin-dashboard-container"></div>');
	page.set_secondary_action(__("تحديث"), () => load_dashboard(page), "refresh");

	load_dashboard(page);
};

// ponytail: admin_dashboard.css lives next to this file and is auto-bundled
// by Frappe's page-asset loader, so no manual <link> injection is needed.

function load_dashboard(page) {
	const container = page.main.find(".admin-dashboard-container");
	container.html('<div class="ad-loading"><i class="fa fa-spinner fa-spin fa-2x"></i><p style="margin-top:12px;">جارٍ التحميل…</p></div>');

	const profit_args = {};
	if (page.profit_month) {
		profit_args.month = page.profit_month;
		profit_args.year  = page.profit_year;
	}

	Promise.all([
		frappe.xcall("dashboard_stats"),
		frappe.xcall("car_profitability", profit_args),
		frappe.xcall("profit_summary", { date_from: page.date_from, date_to: page.date_to }),
		frappe.xcall("gatecar.cash.get_cash_balance_api"),
	]).then(([stats, profitability, summary, cash_balance]) => {
		render_dashboard(
			page,
			container,
			stats,
			profitability,
			page.profit_month,
			page.profit_year,
			summary,
			cash_balance || 0,
		);
	});
}

function render_dashboard(page, container, data, profitability, filter_month, filter_year, summary, cash_balance) {
	const available       = data.status_map["متوفر"]          || 0;
	const rented          = data.status_map["مؤجر"]           || 0;
	const reserved        = data.status_map["محجوز"]          || 0;
	const in_maintenance  = data.status_map["داخل الصيانة"]   || 0;
	const ready           = data.status_map["جاهز للتسليم"]   || 0;
	const is_admin        = frappe.user_roles.includes("System Manager");
	const active_branch   = data.branches[0];
	const active_fleet    = data.fleets[0];

	// ── profit summary values ────────────────────────────────────
	const rev            = summary.period_revenue     || 0;
	const periodic       = summary.period_periodic    || 0;
	const taxes          = summary.period_taxes       || 0;
	const expense        = summary.period_expense     || 0;
	const withdrawals    = summary.period_withdrawals || 0;
	// الضريبة تُستبعد من الوعاء قبل القسمة — لا الشركة ولا المستثمر يأخذ منها.
	const revenue_ex_tax = rev - taxes;
	const company_share  = revenue_ex_tax * 0.20;
	// المستثمر: 80% من الإيراد (بعد استبعاد الضريبة) ناقص الصيانة الدورية والمصاريف العامة.
	const investor_share = (revenue_ex_tax * 0.80) - (periodic + expense);
	const net            = company_share + investor_share;

	container.html(`
		<div class="ad-wrap">

			<!-- ── Banner ── -->
			<div class="ad-banner ad-gatecar-banner">
				<img src="/assets/gatecar/images/logo.svg" alt="Gate Cars" class="ad-banner-logo">
			</div>

			${is_admin ? `
			<!-- ── 1. ملخص الأرباح ── -->
			<div class="ad-card ad-profit-card">
				<div class="ad-profit-heading">
					<div>
						<span class="ad-eyebrow">الأداء المالي</span>
						<h5 class="ad-section-title"><i class="fa fa-coins"></i> ملخص الأرباح</h5>
					</div>
					<div class="ad-filter-row">
						<span class="ad-filter-label">من:</span>
						<input type="date" id="profit-date-from" class="form-control" value="${page.date_from}">
						<span class="ad-filter-label">إلى:</span>
						<input type="date" id="profit-date-to" class="form-control" value="${page.date_to}">
						<button id="calc-period-profit" class="ad-calc-btn">احسب</button>
					</div>
				</div>
				<div class="ad-body open">
					<div class="ad-profit-layout">
						<div class="ad-profit-hero">
							<i class="fa fa-calculator"></i>
							<span>صافي الربح</span>
							<strong>${fc(net)}</strong>
							<small>بعد خصم الضرائب والمصاريف</small>
						</div>
						<div class="ad-kpi-row ad-profit-metrics">
							${kpi("إجمالي الإيرادات",      fc(rev),            "green",  "fa-arrow-up")}
							${kpi("اجمالي الضرائب",        fc(taxes),          "yellow", "fa-percent")}
							${kpi("صافي أرباح الشركة",     fc(company_share),  "blue",   "fa-building")}
							${kpi("الصيانة الدورية",       fc(periodic),       "orange", "fa-wrench")}
							${kpi("المصاريف العامة",       fc(expense),        "red",    "fa-money")}
							${kpi("صافي أرباح المستثمرين", fc(investor_share), investor_share >= 0 ? "purple" : "red", "fa-users")}
							${kpi("رصيد الصندوق الحالي", fc(cash_balance), cash_balance >= 0 ? "green" : "red", "fa-cash-register")}
							${kpi("المسحوبات", fc(withdrawals), "red", "fa-arrow-down")}
						</div>
					</div>
				</div>
			</div>` : ""}

			<!-- ── 2. نظرة الأسطول ── -->
			<div class="ad-card ad-overview-card">
				<div class="ad-section-head" style="cursor:default;">
					<div>
						<span class="ad-eyebrow">الحالة الحالية</span>
						<h5 class="ad-section-title"><i class="fa fa-car"></i> نظرة الأسطول</h5>
					</div>
					<span class="ad-overview-total">${data.total_cars} سيارة</span>
				</div>
				<div class="ad-body open">
					<div class="ad-overview-layout">
						<div class="ad-total-block">
							<span>إجمالي الأسطول</span>
							<strong>${data.total_cars}</strong>
							<small>سيارة مسجلة</small>
						</div>
						<div class="ad-status-list">
							${status_item("متوفرة", available, "green", data.total_cars)}
							${status_item("مؤجرة", rented, "orange", data.total_cars)}
							${status_item("محجوزة", reserved, "yellow", data.total_cars)}
							${status_item("داخل الصيانة", in_maintenance, "red", data.total_cars)}
							${status_item("جاهز للتسليم", ready, "purple", data.total_cars)}
							${status_item("مجمدة", data.frozen_cars, "grey", data.total_cars)}
						</div>
					</div>
				</div>
			</div>

			<!-- ── 3. أرباح السيارات ── -->
			<div class="ad-card ad-table-card">
				<div class="ad-section-head collapsible-toggle">
					<h5 class="ad-section-title">
						<i class="fa fa-chart-line"></i>
						أرباح السيارات ${filter_month ? `(${filter_month}/${filter_year})` : "(الكل)"}
					</h5>
					<div style="display:flex; align-items:center; gap:8px;">
						<div class="ad-select-row" onclick="event.stopPropagation()">
							<select id="profit-month" class="ad-select">
								<option value="">كل الشهور</option>
								${[["1","يناير"],["2","فبراير"],["3","مارس"],["4","أبريل"],["5","مايو"],["6","يونيو"],
								   ["7","يوليو"],["8","أغسطس"],["9","سبتمبر"],["10","أكتوبر"],["11","نوفمبر"],["12","ديسمبر"]]
								  .map(([v,l]) => `<option value="${v}" ${filter_month == v ? "selected" : ""}>${v} - ${l}</option>`).join("")}
							</select>
							<select id="profit-year" class="ad-select">
								${["2025","2026","2027"].map(y => `<option value="${y}" ${filter_year == y ? "selected" : ""}>${y}</option>`).join("")}
							</select>
						</div>
						<i class="fa fa-chevron-down ad-toggle-icon open"></i>
					</div>
				</div>
				<div class="ad-body open">
					<div class="ad-table-wrap">
						<table class="ad-table">
							<thead><tr>
								<th>السيارة</th><th>النوع</th><th>الموديل</th><th>الحالة</th>
								${is_admin ? "<th>الإيرادات</th>" : ""}
								<th>الضرائب</th><th>الصيانة الدورية</th><th>المصاريف</th>
								${is_admin ? "<th>صافي الربح</th><th>التقرير</th>" : ""}
							</tr></thead>
							<tbody>
								${profitability.map(car => `
								<tr>
									<td><a href="/app/car/${car.name}"><strong>${car.name}</strong></a></td>
									<td>${car.brand}</td>
									<td>${car.model}</td>
									<td>${status_pill(car.status)}</td>
									${is_admin ? `<td class="ad-val-green">${fc(car.total_revenue)}</td>` : ""}
									<td class="ad-val-red">${fc(car.total_taxes || 0)}</td>
									<td class="ad-val-orange">${fc(car.total_periodic || 0)}</td>
									<td class="ad-val-red">${fc(car.total_expense || 0)}</td>
									${is_admin ? `
									<td><strong class="${car.net_profit > 0 ? "ad-val-green" : car.net_profit < 0 ? "ad-val-red" : ""}">${fc(car.net_profit)}</strong></td>
									<td><a href="/app/query-report/Owner Car Report?car=${car.name}" class="ad-report-btn"><i class="fa fa-file-alt"></i>عرض التقرير</a></td>
									` : ""}
								</tr>`).join("")}
							</tbody>
						</table>
					</div>
				</div>
			</div>


			<!-- ── 4. تفاصيل الفرع ── -->
			${active_branch ? `
			<div class="ad-card ad-branch-card">
				<div class="ad-section-head ad-branch-heading">
					<div>
						<span class="ad-eyebrow">تفاصيل الفرع</span>
						<h5 class="ad-section-title"><i class="fa fa-building"></i> <span id="selected-branch-name">${active_branch.branch_name}</span></h5>
						<span id="selected-branch-city" class="ad-branch-city">${active_branch.city || "—"}</span>
					</div>
					<label class="ad-detail-picker" for="branch-selector">
						<span class="ad-filter-label">اختر الفرع</span>
						<select id="branch-selector" class="ad-select">
							${data.branches.map((branch, index) => `<option value="${index}">${branch.branch_name}</option>`).join("")}
						</select>
					</label>
				</div>
				<div class="ad-body open">
					<div id="branch-kpis" class="ad-kpi-row">${branch_kpis(active_branch)}</div>
				</div>
			</div>` : ""}

			<!-- ── 5. تفاصيل الأسطول ── -->
			${active_fleet ? `
			<div class="ad-card ad-fleet-card">
				<div class="ad-section-head ad-fleet-heading">
					<div>
						<span class="ad-eyebrow">تفاصيل الأسطول</span>
						<h5 class="ad-section-title"><i class="fa fa-layer-group"></i> <span id="selected-fleet-name">${active_fleet.fleet_name}</span></h5>
						<span id="selected-fleet-branch" class="ad-fleet-location">${active_fleet.branch || "—"}</span>
					</div>
					<label class="ad-detail-picker" for="fleet-selector">
						<span class="ad-filter-label">اختر الأسطول</span>
						<select id="fleet-selector" class="ad-select">
							${data.fleets.map((fleet, index) => `<option value="${index}">${fleet.fleet_name}</option>`).join("")}
						</select>
					</label>
				</div>
				<div class="ad-body open"><div id="fleet-details">${fleet_details(active_fleet)}</div></div>
			</div>` : ""}

		</div>
	`);

	// ── event: collapsible toggle ────────────────────────────────
	container.find(".collapsible-toggle").on("click", function () {
		const $card = $(this).closest(".ad-card");
		const $body = $card.find(".ad-body").first();
		const $icon = $(this).find(".ad-toggle-icon");
		$body.toggleClass("open");
		$icon.toggleClass("open");
	});

	// ── event: month/year filter (stop propagation on select click) ──
	container.find("#profit-month, #profit-year").on("click", e => e.stopPropagation());
	container.find("#profit-month, #profit-year").on("change", function () {
		page.profit_month = container.find("#profit-month").val();
		page.profit_year  = container.find("#profit-year").val();
		load_dashboard(page);
	});

	container.find("#branch-selector").on("change", function () {
		const branch = data.branches[Number($(this).val())];
		if (!branch) return;
		container.find("#selected-branch-name").text(branch.branch_name);
		container.find("#selected-branch-city").text(branch.city || "—");
		container.find("#branch-kpis").html(branch_kpis(branch));
	});

	container.find("#fleet-selector").on("change", function () {
		const fleet = data.fleets[Number($(this).val())];
		if (!fleet) return;
		container.find("#selected-fleet-name").text(fleet.fleet_name);
		container.find("#selected-fleet-branch").text(fleet.branch || "—");
		container.find("#fleet-details").html(fleet_details(fleet));
	});

	// ── event: period profit button ──────────────────────────────
	container.find("#calc-period-profit").on("click", function () {
		page.date_from = container.find("#profit-date-from").val();
		page.date_to   = container.find("#profit-date-to").val();
		if (!page.date_from || !page.date_to) {
			frappe.msgprint({
				message: __("اختر تاريخ البداية والنهاية"),
				indicator: "orange",
			});
			return;
		}
		load_dashboard(page);
	});
}

// ── Helper: section head (collapsed by default) ──────────────────
function section_head(icon, title, isOpen = false) {
	return `
		<div class="ad-section-head collapsible-toggle">
			<h5 class="ad-section-title"><i class="fa ${icon}"></i> ${title}</h5>
			<i class="fa fa-chevron-down ad-toggle-icon${isOpen ? " open" : ""}"></i>
		</div>
	`;
}

// ── Helper: KPI card ─────────────────────────────────────────────
function kpi(label, value, color, icon) {
	return `
		<div class="ad-kpi ad-kpi-${color}">
			<i class="fa ${icon} ad-kpi-icon"></i>
			<div class="ad-kpi-value">${value}</div>
			<div class="ad-kpi-label">${label}</div>
		</div>
	`;
}

function status_item(label, value, color, total) {
	const percent = total ? Math.min(100, Math.round((value / total) * 100)) : 0;
	return `
		<div class="ad-status-item">
			<div class="ad-status-meta">
				<span>${label}</span>
				<strong>${value}</strong>
			</div>
			<div class="ad-status-track">
				<span class="ad-status-fill ad-status-${color}" style="width:${percent}%"></span>
			</div>
		</div>
	`;
}

function branch_kpis(branch) {
	return [
		["إجمالي", branch.car_count, "blue", "fa-car"],
		["متوفرة", branch.available, "green", "fa-check-circle"],
		["محجوزة", branch.reserved, "yellow", "fa-calendar"],
		["مؤجرة", branch.rented, "orange", "fa-key"],
		["صيانة", branch.in_maintenance, "red", "fa-wrench"],
		["جاهز للتسليم", branch.ready, "purple", "fa-thumbs-up"],
		["مجمدة", branch.frozen, "grey", "fa-ban"],
	].map(([label, value, color, icon]) => kpi(label, value, color, icon)).join("");
}

function fleet_details(fleet) {
	const availability = fleet.car_count ? Math.round((fleet.available / fleet.car_count) * 100) : 0;
	return `
		<div class="ad-fleet-details">
			<div class="ad-fleet-capacity">
				<span>المركبات المتوفرة</span>
				<strong>${fleet.available}</strong>
				<small>من ${fleet.car_count} سيارة</small>
				<span class="ad-fleet-meter"><span style="width:${availability}%"></span></span>
			</div>
			<dl class="ad-fleet-facts">
				<div><dt>إجمالي السيارات</dt><dd>${fleet.car_count}</dd></div>
				<div><dt>متوفرة</dt><dd>${fleet.available}</dd></div>
				<div><dt>مؤجرة</dt><dd>${fleet.rented}</dd></div>
			</dl>
		</div>
	`;
}

// ── Helper: status pill ──────────────────────────────────────────
function pill(value, color) {
	return `<span class="ad-pill ad-pill-${color}">${value}</span>`;
}

function status_pill(status) {
	const colors = {
		"متوفر": "green",
		"مؤجر": "orange",
		"محجوز": "yellow",
		"داخل الصيانة": "red",
		"جاهز للتسليم": "purple",
	};
	return pill(status, colors[status] || "grey");
}

// ── Helper: format currency ──────────────────────────────────────
function fc(val) {
	return frappe.format(val || 0, { fieldtype: "Currency" });
}
