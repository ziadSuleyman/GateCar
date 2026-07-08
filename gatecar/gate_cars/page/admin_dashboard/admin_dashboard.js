frappe.pages["admin-dashboard"].on_page_load = function (wrapper) {
	inject_css();

	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "لوحة المراقبة",
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

function inject_css() {
	if (document.getElementById("ad-style")) return;
	const link = document.createElement("link");
	link.id   = "ad-style";
	link.rel  = "stylesheet";
	link.href = "/assets/gatecar/css/admin_dashboard.css";
	document.head.appendChild(link);
}

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
	]).then(([stats, profitability, summary]) => {
		render_dashboard(page, container, stats, profitability, page.profit_month, page.profit_year, summary);
	});
}

function render_dashboard(page, container, data, profitability, filter_month, filter_year, summary) {
	const available       = data.status_map["متوفر"]          || 0;
	const rented          = data.status_map["مؤجر"]           || 0;
	const reserved        = data.status_map["محجوز"]          || 0;
	const in_maintenance  = data.status_map["داخل الصيانة"]   || 0;
	const ready           = data.status_map["جاهز للتسليم"]   || 0;
	const is_admin        = frappe.user_roles.includes("System Manager");

	// ── profit summary values ────────────────────────────────────
	const rev            = summary.period_revenue     || 0;
	const periodic       = summary.period_periodic    || 0;
	const taxes          = summary.period_taxes       || 0;
	const expense        = summary.period_expense     || 0;
	// الضريبة تُستبعد من الوعاء قبل القسمة — لا الشركة ولا المستثمر يأخذ منها.
	const revenue_ex_tax = rev - taxes;
	const company_share  = revenue_ex_tax * 0.20;
	// المستثمر: 80% من الإيراد (بعد استبعاد الضريبة) ناقص الصيانة الدورية والمصاريف العامة.
	const investor_share = (revenue_ex_tax * 0.80) - (periodic + expense);
	const net            = company_share + investor_share;

	container.html(`
		<div class="ad-wrap">

			<!-- ── Banner ── -->
			<div class="ad-banner">
				<div>
					<h3 class="ad-banner-title">لوحة المراقبة</h3>
					<p class="ad-banner-sub">مرحباً، ${frappe.session.user_fullname} — ${frappe.datetime.str_to_user(frappe.datetime.get_today())}</p>
				</div>
				<img src="/assets/gatecar/images/logo.svg" alt="Gate Cars" class="ad-banner-logo">
			</div>

			${is_admin ? `
			<!-- ── 1. ملخص الأرباح ── -->
			<div class="ad-card">
				<div class="ad-section-head" style="cursor:default;">
					<h5 class="ad-section-title"><i class="fa fa-coins"></i> ملخص الأرباح</h5>
				</div>
				<div class="ad-body open">
					<div class="ad-filter-row">
						<span class="ad-filter-label">من:</span>
						<input type="date" id="profit-date-from" class="form-control" value="${page.date_from}">
						<span class="ad-filter-label">إلى:</span>
						<input type="date" id="profit-date-to" class="form-control" value="${page.date_to}">
						<button id="calc-period-profit" class="ad-calc-btn">احسب</button>
					</div>
					<div class="ad-kpi-row">
						${kpi("إجمالي الإيرادات",         fc(rev),            "green",  "fa-arrow-up")}
						${kpi("اجمالي الضرائب",           fc(taxes),          "yellow", "fa-percent")}
						${kpi("صافي الربح",               fc(net),            net >= 0 ? "green" : "red", "fa-calculator")}
						${kpi("صافي أرباح الشركة",        fc(company_share),  "blue",   "fa-building")}
						${kpi("الصيانة الدورية",          fc(periodic),       "orange", "fa-wrench")}
						${kpi("المصاريف العامة",          fc(expense),        "red",    "fa-money")}
						${kpi("صافي أرباح المستثمرين",    fc(investor_share), investor_share >= 0 ? "purple" : "red", "fa-users")}
					</div>
				</div>
			</div>` : ""}

			<!-- ── 2. أرباح السيارات ── -->
			<div class="ad-card">
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
						<i class="fa fa-chevron-down ad-toggle-icon"></i>
					</div>
				</div>
				<div class="ad-body">
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
									<td>${car.status}</td>
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

			<!-- ── 3. ملخص الفروع ── -->
			<div class="ad-card">
				${section_head("fa-building", "ملخص الفروع")}
				<div class="ad-body">
					<div class="ad-table-wrap">
						<table class="ad-table">
							<thead><tr>
								<th>الفرع</th><th>المدينة</th><th>إجمالي</th>
								<th>متوفرة</th><th>محجوزة</th><th>مؤجرة</th>
								<th>صيانة</th><th>جاهز</th><th>مجمدة</th>
							</tr></thead>
							<tbody>
								${data.branches.map(b => `
								<tr>
									<td><strong>${b.branch_name}</strong></td>
									<td>${b.city || "-"}</td>
									<td><strong>${b.car_count}</strong></td>
									<td>${pill(b.available,       "green")}</td>
									<td>${pill(b.reserved,        "yellow")}</td>
									<td>${pill(b.rented,          "orange")}</td>
									<td>${pill(b.in_maintenance,  "red")}</td>
									<td>${pill(b.ready,           "purple")}</td>
									<td>${pill(b.frozen,          "grey")}</td>
								</tr>`).join("")}
							</tbody>
						</table>
					</div>
				</div>
			</div>

			<!-- ── 4. الأساطيل ── -->
			<div class="ad-card">
				${section_head("fa-layer-group", "الأساطيل")}
				<div class="ad-body">
					<div class="ad-table-wrap">
						<table class="ad-table">
							<thead><tr>
								<th>الأسطول</th><th>الفرع</th><th>إجمالي عدد السيارات</th>
								<th>متوفرة</th><th>مؤجرة</th>
							</tr></thead>
							<tbody>
								${data.fleets.map(f => `
								<tr>
									<td><strong>${f.fleet_name}</strong></td>
									<td>${f.branch}</td>
									<td>${f.car_count}</td>
									<td>${pill(f.available, "green")}</td>
									<td>${pill(f.rented,    "orange")}</td>
								</tr>`).join("")}
							</tbody>
						</table>
					</div>
				</div>
			</div>

			<!-- ── 5. الإجمالي العام ── -->
			<div class="ad-card">
				${section_head("fa-car", "الإجمالي العام")}
				<div class="ad-body">
					<div class="ad-kpi-row">
						${kpi("إجمالي عدد السيارات", data.total_cars,  "blue",   "fa-car")}
						${kpi("متوفرة",           available,        "green",  "fa-check-circle")}
						${kpi("محجوزة",           reserved,         "yellow", "fa-calendar")}
						${kpi("مؤجرة",            rented,           "orange", "fa-key")}
						${kpi("داخل الصيانة",     in_maintenance,   "red",    "fa-wrench")}
						${kpi("جاهز للتسليم",     ready,            "purple", "fa-thumbs-up")}
						${kpi("مجمدة",            data.frozen_cars, "grey",   "fa-ban")}
					</div>
				</div>
			</div>

			<!-- ── 6. بطاقات الفروع ── -->
			${data.branches.map(b => `
			<div class="ad-card">
				${section_head("fa-building", `${b.branch_name} <span style="font-size:12px;font-weight:400;color:var(--text-muted);margin-right:6px;">${b.city || ""}</span>`)}
				<div class="ad-body">
					<div class="ad-kpi-row">
						${kpi("إجمالي",        b.car_count,       "blue",   "fa-car")}
						${kpi("متوفرة",        b.available,       "green",  "fa-check-circle")}
						${kpi("محجوزة",        b.reserved,        "yellow", "fa-calendar")}
						${kpi("مؤجرة",         b.rented,          "orange", "fa-key")}
						${kpi("صيانة",         b.in_maintenance,  "red",    "fa-wrench")}
						${kpi("جاهز للتسليم", b.ready,           "purple", "fa-thumbs-up")}
						${kpi("مجمدة",         b.frozen,          "grey",   "fa-ban")}
					</div>
				</div>
			</div>`).join("")}

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

	// ── event: period profit button ──────────────────────────────
	container.find("#calc-period-profit").on("click", function () {
		page.date_from = container.find("#profit-date-from").val();
		page.date_to   = container.find("#profit-date-to").val();
		if (!page.date_from || !page.date_to) {
			frappe.msgprint("اختر تاريخ البداية والنهاية", "orange");
			return;
		}
		load_dashboard(page);
	});
}

// ── Helper: section head (collapsed by default) ──────────────────
function section_head(icon, title) {
	return `
		<div class="ad-section-head collapsible-toggle">
			<h5 class="ad-section-title"><i class="fa ${icon}"></i> ${title}</h5>
			<i class="fa fa-chevron-down ad-toggle-icon"></i>
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
			<div class="ad-kpi-bar"></div>
		</div>
	`;
}

// ── Helper: status pill ──────────────────────────────────────────
function pill(value, color) {
	return `<span class="ad-pill ad-pill-${color}">${value}</span>`;
}

// ── Helper: format currency ──────────────────────────────────────
function fc(val) {
	return frappe.format(val || 0, { fieldtype: "Currency" });
}
