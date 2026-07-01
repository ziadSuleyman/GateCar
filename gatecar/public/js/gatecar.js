// Gate Cars Workspace Enhancements

frappe.router.on("change", function () {
	if (frappe.get_route_str() === "Workspaces/Gate Cars") {
		setTimeout(enhance_workspace, 300);
	}
	if (frappe.get_route()[0] === "Workspaces") {
		setTimeout(hide_workspace_breadcrumb, 100);
		document.body.classList.add("gatecar-workspace");
	} else {
		document.body.classList.remove("gatecar-workspace");
	}
});

function hide_workspace_breadcrumb() {
	$(".navbar-breadcrumbs").hide();
}

function enhance_workspace() {
	const cards = document.querySelectorAll(
		".workspace-container .card-widget-box .widget"
	);
	cards.forEach((card) => {
		const head = card.querySelector(".widget-head .widget-title");
		if (head && !head.dataset.enhanced) {
			head.dataset.enhanced = "1";
			const title = head.textContent.trim();
			const icons = {
				"الحجوزات": "📋",
				"استلام السيارات": "🔑",
				"القيود المالية": "💰",
				"السيارات": "🚗",
				"الزبائن": "👥",
				"المسمى الوظيفي": "🏷️",
				"الفروع والأساطيل": "🏢",
				"الموظفين والورديات": "👷",
				"المدن": "🏙️",
			};
			if (icons[title]) {
				head.innerHTML = `${icons[title]} ${title}`;
			}
		}
	});
}
