frappe.pages["branch-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("لوحة تحكم الفرع"),
		single_column: true,
	});

	page.main.html('<div class="branch-dashboard-container"></div>');
	page.set_secondary_action(__("تحديث"), () => load_branch_dashboard(page), "refresh");
	load_branch_dashboard(page);
};

function load_branch_dashboard(page) {
	const container = page.main.find(".branch-dashboard-container");
	container.html('<div class="ad-loading"><i class="fa fa-spinner fa-spin fa-2x"></i><p>جارٍ التحميل…</p></div>');

	const is_admin = frappe.user.has_role("System Manager");
	const stats_method = is_admin ? "dashboard_stats" : "branch_dashboard_stats";
	const profitability_method = is_admin ? "car_profitability" : "branch_car_profitability";

	Promise.all([
		frappe.xcall(stats_method),
		frappe.xcall(profitability_method),
	]).then(([stats, profitability]) => {
		if (stats.error) {
			container.html(`<div class="ad-loading">${stats.error}</div>`);
			return;
		}
		render_branch_dashboard(container, stats, profitability);
	});
}

function render_branch_dashboard(container, data, profitability) {
	container.html(`
		<div class="ad-wrap">
			<div class="ad-banner ad-gatecar-banner">
				<img src="/assets/gatecar/images/logo.svg" alt="Gate Cars" class="ad-banner-logo">
			</div>
			${render_overview(data)}
			${render_fleets(data.fleets)}
			${render_cars(profitability)}
			${data.branches.map(render_branch).join("")}
		</div>
	`);

	container.find(".collapsible-toggle").on("click", function () {
		const card = $(this).closest(".ad-card");
		card.find(".ad-body").first().toggleClass("open");
		$(this).find(".ad-toggle-icon").toggleClass("open");
	});
}

function render_overview(data) {
	const statuses = data.status_map;
	return `
		<div class="ad-card ad-overview-card">
			<div class="ad-section-head">
				<div><span class="ad-eyebrow">الحالة الحالية</span><h5 class="ad-section-title"><i class="fa fa-car"></i> نظرة الأسطول</h5></div>
				<span class="ad-overview-total">${data.total_cars} سيارة</span>
			</div>
			<div class="ad-body open">
				<div class="ad-overview-layout">
					<div class="ad-total-block"><span>إجمالي الأسطول</span><strong>${data.total_cars}</strong><small>سيارة مسجلة</small></div>
					<div class="ad-status-list">
						${status_item("متوفرة", statuses["متوفر"] || 0, "green", data.total_cars)}
						${status_item("مؤجرة", statuses["مؤجر"] || 0, "orange", data.total_cars)}
						${status_item("محجوزة", statuses["محجوز"] || 0, "yellow", data.total_cars)}
						${status_item("داخل الصيانة", statuses["داخل الصيانة"] || 0, "red", data.total_cars)}
						${status_item("جاهز للتسليم", statuses["جاهز للتسليم"] || 0, "purple", data.total_cars)}
						${status_item("مجمدة", data.frozen_cars, "grey", data.total_cars)}
					</div>
				</div>
			</div>
		</div>`;
}

function render_fleets(fleets) {
	const rows = fleets.map(fleet => `
		<tr><td><strong>${fleet.fleet_name}</strong></td><td>${fleet.branch}</td><td>${fleet.car_count}</td>
		<td>${pill(fleet.available, "green")}</td><td>${pill(fleet.rented, "orange")}</td></tr>`).join("");
	return render_table_card("fa-layer-group", "الأساطيل", ["الأسطول", "الفرع", "إجمالي عدد السيارات", "متوفرة", "مؤجرة"], rows);
}

function render_cars(cars) {
	const rows = cars.map(car => `
		<tr><td><a href="/app/car/${car.name}"><strong>${car.name}</strong></a></td><td>${car.brand}</td><td>${car.model}</td>
		<td>${status_pill(car.status)}</td><td class="ad-val-orange">${currency(car.total_periodic)}</td><td class="ad-val-red">${currency(car.total_expense)}</td></tr>`).join("");
	return render_table_card("fa-chart-line", "حالة السيارات والتكاليف", ["السيارة", "النوع", "الموديل", "الحالة", "تكاليف الصيانة الدورية", "مصاريف السيارة"], rows);
}

function render_table_card(icon, title, headings, rows) {
	return `
		<div class="ad-card ad-table-card">
			${collapsible_head(icon, title)}
			<div class="ad-body"><div class="ad-table-wrap"><table class="ad-table">
				<thead><tr>${headings.map(heading => `<th>${heading}</th>`).join("")}</tr></thead><tbody>${rows}</tbody>
			</table></div></div>
		</div>`;
}

function render_branch(branch) {
	return `
		<div class="ad-card ad-branch-card">
			${collapsible_head("fa-building", branch.branch_name, branch.city)}
			<div class="ad-body"><div class="ad-kpi-row">${branch_kpis(branch)}</div></div>
		</div>`;
}

function collapsible_head(icon, title, subtitle = "") {
	return `
		<div class="ad-section-head collapsible-toggle">
			<div><span class="ad-eyebrow">${subtitle}</span><h5 class="ad-section-title"><i class="fa ${icon}"></i>${title}</h5></div>
			<i class="fa fa-chevron-down ad-toggle-icon"></i>
		</div>`;
}

function status_item(label, value, color, total) {
	const percent = total ? Math.min(100, Math.round((value / total) * 100)) : 0;
	return `<div class="ad-status-item"><div class="ad-status-meta"><span>${label}</span><strong>${value}</strong></div><div class="ad-status-track"><span class="ad-status-fill ad-status-${color}" style="width:${percent}%"></span></div></div>`;
}

function branch_kpis(branch) {
	return [
		["إجمالي", branch.car_count, "blue", "fa-car"], ["متوفرة", branch.available, "green", "fa-check-circle"],
		["محجوزة", branch.reserved, "yellow", "fa-calendar"], ["مؤجرة", branch.rented, "orange", "fa-key"],
		["صيانة", branch.in_maintenance, "red", "fa-wrench"], ["جاهز للتسليم", branch.ready, "purple", "fa-thumbs-up"],
		["مجمدة", branch.frozen, "grey", "fa-ban"],
	].map(([label, value, color, icon]) => kpi(label, value, color, icon)).join("");
}

function kpi(label, value, color, icon) {
	return `<div class="ad-kpi ad-kpi-${color}"><i class="fa ${icon} ad-kpi-icon"></i><div class="ad-kpi-value">${value}</div><div class="ad-kpi-label">${label}</div></div>`;
}

function pill(value, color) {
	return `<span class="ad-pill ad-pill-${color}">${value}</span>`;
}

function status_pill(status) {
	const colors = { "متوفر": "green", "مؤجر": "orange", "محجوز": "yellow", "داخل الصيانة": "red", "جاهز للتسليم": "purple" };
	return pill(status, colors[status] || "grey");
}

function currency(value) {
	return frappe.format(value || 0, { fieldtype: "Currency" });
}
