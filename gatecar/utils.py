import re


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
