import re

import frappe


def compute_rental_tax(rental_amount: float) -> tuple[float, float]:
	"""Single source of truth for the two-tier rental tax formula.

	ضريبة الإنفاق = الإيجار × نسبة الإنفاق
	ضريبة المحلية = ضريبة الإنفاق × نسبة المحلية   (تُحسب على الضريبة الأولى، وليس على الإيجار)

	Used by Car Booking (display-only contract taxes), Car Receipt (authoritative
	invoice totals), and the monthly accrual generator — kept in one place so the
	three never drift apart.
	"""
	settings = frappe.get_cached_doc("Gate Cars Settings")
	spend_rate = settings.spending_tax_rate or 0
	local_rate = settings.local_tax_rate or 0

	spending_tax = round((rental_amount or 0) * spend_rate / 100.0, 2)
	local_tax = round(spending_tax * local_rate / 100.0, 2)
	return spending_tax, local_tax


def number_ordered_lists(html: str) -> str:
	"""Convert every <ol>…<li>…</li>…</ol> block into explicitly numbered items.

	wkhtmltopdf (used for PDF download) resets native <ol> counters after a page
	break, so long numbered lists print "1." on every item past the break. Baking
	the numbers into the markup as plain text removes the counter entirely, so the
	numbering survives page breaks in the PDF.
	"""
	if not html:
		return html

	def repl_ol(m: "re.Match") -> str:
		attrs, inner = m.group(1), m.group(2)
		start = 1
		ms = re.search(r'start\s*=\s*["\']?(\d+)', attrs)
		if ms:
			start = int(ms.group(1))
		items = re.findall(r"<li[^>]*>(.*?)</li>", inner, flags=re.DOTALL | re.IGNORECASE)
		out = ['<div class="onum">']
		for i, item in enumerate(items, start):
			out.append(
				f'<div class="onum-item"><span class="onum-n">{i}.</span>'
				f'<span class="onum-t">{item}</span></div>'
			)
		out.append("</div>")
		return "".join(out)

	return re.sub(r"<ol([^>]*)>(.*?)</ol>", repl_ol, html, flags=re.DOTALL | re.IGNORECASE)
