// Gate Cars Workspace Enhancements

function sync_workspace_bg() {
	const route = frappe.get_route ? frappe.get_route() : [];
	if (route[0] === "Workspaces") {
		document.body.classList.add("gatecar-workspace");
		setTimeout(hide_workspace_breadcrumb, 150);
		// Force sidebar expanded to show all items
		setTimeout(() => {
			const sc = document.querySelector(".body-sidebar-container");
			if (sc && !sc.classList.contains("expanded")) sc.classList.add("expanded");
		}, 200);
		if (frappe.get_route_str() === "Workspaces/Gate Cars") {
			setTimeout(enhance_workspace, 350);
		}
	} else {
		document.body.classList.remove("gatecar-workspace");
	}
}

// SPA navigation
frappe.router.on("change", sync_workspace_bg);

// Initial hard-reload — wait for router to resolve first route
$(document).ready(function () {
	setTimeout(sync_workspace_bg, 600);
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
