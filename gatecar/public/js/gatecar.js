// Gate Cars Global Styles

const GATECAR_ROLE_HOME = {
	Administrator: "/desk/gate-cars",
	"مدير فرع": "/desk/إدارة-الفرع",
	"مشرف أسطول": "/desk/الأسطول",
	"موظف مبيعات": "/desk/المبيعات",
};

function redirect_to_root_login() {
	window.location.href = "/login?redirect-to=%2F";
}

function use_root_login_redirect() {
	if (frappe.app) frappe.app.redirect_to_login = redirect_to_root_login;
}

function redirect_default_desk_route() {
	const currentPath = decodeURIComponent(window.location.pathname).replace(/\/$/, "");
	const landingRoutes = ["/desk", ...Object.values(GATECAR_ROLE_HOME)];
	if (!landingRoutes.includes(currentPath) && frappe.get_route_str() !== "desk") return;

	const roles = frappe.user_roles || [];
	const destination = roles.includes("Administrator")
		? GATECAR_ROLE_HOME.Administrator
		: roles.map((role) => GATECAR_ROLE_HOME[role]).find(Boolean);
	if (destination && currentPath !== destination) window.location.replace(destination);
}

/* ══ Route Classes ════════════════════════════════════════════════════════ */

function sync_route_classes() {
	const route = frappe.get_route ? frappe.get_route() : [];

	// Workspace-specific enhancements
	if (route[0] === "Workspaces") {
		document.body.classList.add("gatecar-workspace");
		setTimeout(hide_workspace_breadcrumb, 150);
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

/* ══ Top-bar cleanup ══════════════════════════════════════════════════════ */

function remove_navbar_logo() {
	document.querySelectorAll(".gatecar-navbar-logo").forEach((logo) => logo.remove());
}

function link_navbar_home() {
	document
		.querySelectorAll(".page-head .navbar-breadcrumbs li:first-child a")
		.forEach((homeLink) => {
			homeLink.href = "/";
		});
}

function translate_sidebar_labels() {
	const translations = { Search: "بحث", Notification: "إشعارات" };
	document.querySelectorAll(".sidebar-item-label").forEach((label) => {
		const translation = translations[label.textContent.trim()];
		if (translation) label.textContent = translation;
	});
}

function ensure_fleet_workspace_icon() {
	if (frappe.get_route_str() || document.querySelector('[data-id="الأسطول"]')) return;
	const source = document.querySelector('[data-id="إدارة الفرع"]');
	const icons = source?.parentElement;
	if (!source || !icons) return;

	const fleet = source.cloneNode(true);
	fleet.dataset.id = "الأسطول";
	fleet.href = "/desk/الأسطول?sidebar=%D8%A7%D9%84%D8%A3%D8%B3%D8%B7%D9%88%D9%84";
	fleet.querySelector(".icon-title").textContent = "الأسطول";
	fleet.querySelector(".icon-title").dataset.originalTitle = "الأسطول";
	icons.insertBefore(fleet, source.nextSibling);
}

function watch_sidebar_labels() {
	if (document.body.dataset.gatecarTranslationObserver) return;
	const observer = new MutationObserver(() => {
		translate_sidebar_labels();
		ensure_fleet_workspace_icon();
	});
	observer.observe(document.body, { childList: true, subtree: true });
	document.body.dataset.gatecarTranslationObserver = "1";
	translate_sidebar_labels();
	ensure_fleet_workspace_icon();
}

// SPA navigation
frappe.router.on("change", () => {
	redirect_default_desk_route();
	sync_route_classes();
	remove_navbar_logo();
	link_navbar_home();
	translate_sidebar_labels();
	setTimeout(() => {
		remove_navbar_logo();
		link_navbar_home();
		translate_sidebar_labels();
	}, 300);
});

// Initial hard-reload
$(document).ready(function () {
	use_root_login_redirect();
	redirect_default_desk_route();
	watch_sidebar_labels();
	setTimeout(sync_route_classes, 600);
	setTimeout(link_navbar_home, 600);
	setTimeout(translate_sidebar_labels, 600);
	setTimeout(remove_navbar_logo, 700);
	setTimeout(link_navbar_home, 700);
	setTimeout(translate_sidebar_labels, 700);
	setTimeout(remove_navbar_logo, 1400);
	setTimeout(link_navbar_home, 1400);
	setTimeout(translate_sidebar_labels, 1400);
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

/* ══ Send document via WhatsApp (public share link) ═══════════════════════ */
/*  Generalised sender: injects a "send via WhatsApp" item INTO the native    */
/*  Actions (الإجراءات) dropdown for every relevant doctype. A public,        */
/*  no-login PDF link is built with a Document Share Key and passed to wa.me.  */

const GC_WA_SEND = {
	"Car Receipt": {
		noun: "فاتورة الاستلام",
		formats: ["فاتورة استلام سيارة"],
		name: (d) => d.customer_name,
		phone: (d) => gc_phone_from_booking(d.booking),
	},
	"Car Inspection": {
		noun: "نموذج الفحص",
		formats: ["نموذج استلام مركبة", "نموذج تسليم مركبة"],
		name: (d) => d.customer_name,
		phone: (d) => Promise.resolve(d.phone || ""),
	},
	"Revenue": {
		noun: "الإيصال المالي",
		formats: ["Revenue Receipt", "Payment Receipt"],
		name: (d) => d.customer_name,
		phone: (d) => gc_phone_from_booking(d.booking_reference),
	},
};

function gc_phone_from_booking(booking) {
	if (!booking) return Promise.resolve("");
	return frappe.db
		.get_value("Car Booking", booking, "international_phone")
		.then((r) => (r && r.message && r.message.international_phone) || "");
}

function gc_add_wa_actions(frm) {
	if (frm.is_new()) return;
	const cfg = GC_WA_SEND[frm.doctype];
	if (!cfg) return;
	// Custom buttons are re-added on every refresh (Frappe clears them first),
	// so they always render — unlike the native Actions dropdown.
	if (cfg.formats.length === 1) {
		frm.add_custom_button(__("إرسال عبر واتساب"), () =>
			gc_send_wa(frm, cfg, cfg.formats[0])
		);
	} else {
		cfg.formats.forEach((pf) => {
			frm.add_custom_button(
				pf,
				() => gc_send_wa(frm, cfg, pf),
				__("إرسال عبر واتساب")
			);
		});
	}
}

function gc_send_wa(frm, cfg, print_format) {
	if (frm.is_dirty()) {
		frappe.msgprint(__("احفظ المستند أولاً قبل الإرسال"));
		return;
	}
	frappe.call({
		method: "gatecar.api.get_share_url",
		args: {
			doctype: frm.doctype,
			name: frm.docname,
			print_format: print_format,
			no_letterhead: 0,
		},
		freeze: true,
		freeze_message: __("جارٍ تجهيز الرابط العام..."),
		callback: (r) => {
			if (!r.message) return;
			const url = r.message;
			Promise.resolve(cfg.phone(frm.doc)).then((phone) => {
				phone = (phone || "").replace(/[^0-9]/g, "");
				const cust = cfg.name(frm.doc) || "";
				const msg =
					`مرحباً ${cust}،\n` +
					`مرفق رابط ${cfg.noun} (${frm.docname}):\n${url}`;
				const wa =
					"https://wa.me/" + phone + "?text=" + encodeURIComponent(msg);
				window.open(wa, "_blank");
			});
		},
	});
}

Object.keys(GC_WA_SEND).forEach((dt) => {
	frappe.ui.form.on(dt, {
		refresh(frm) {
			gc_add_wa_actions(frm);
		},
	});
});

/* ══ Car Booking: live tax preview (server recomputes authoritatively) ════ */
/*  Mirrors car_booking.py compute_taxes so the values show before saving.    */

let _gc_tax_rates = null;

function gc_booking_taxes(frm) {
	if (frm.doc.docstatus !== 0) return; // read-only once submitted
	const apply = (rates) => {
		const rental = frm.doc.cost || 0;
		const st = Math.round(rental * (rates.spending_tax_rate || 0)) / 100;
		const lt = Math.round(st * (rates.local_tax_rate || 0)) / 100;
		const gt = Math.round((rental + st + lt) * 100) / 100;
		frm.set_value("spending_tax", st);
		frm.set_value("local_tax", lt);
		frm.set_value("grand_total", gt);
	};
	if (_gc_tax_rates) {
		apply(_gc_tax_rates);
		return;
	}
	Promise.all([
		frappe.db.get_single_value("Gate Cars Settings", "spending_tax_rate"),
		frappe.db.get_single_value("Gate Cars Settings", "local_tax_rate"),
	]).then(([spending_tax_rate, local_tax_rate]) => {
		_gc_tax_rates = { spending_tax_rate, local_tax_rate };
		apply(_gc_tax_rates);
	});
}

frappe.ui.form.on("Car Booking", {
	cost(frm) {
		gc_booking_taxes(frm);
	},
});
