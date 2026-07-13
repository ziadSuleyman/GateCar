# Copyright (c) 2026, Ziad Suleyman and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CustomerCar(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		customer_name: DF.Data
		emergency_number: DF.Phone | None
		international_phone: DF.Phone
		nationality: DF.Data | None
		phone: DF.Phone | None
		اسم_الأم: DF.Data | None
		التولد: DF.Data | None
		الرقم_الوطني: DF.Data | None
		العنوان: DF.Data | None
		تاريخ_الاصدار: DF.Date | None
		تاريخ_الانتهاء: DF.Date | None
		رقم_جواز_السفر: DF.Data | None
		رقم_رخصة_القيادة: DF.Data | None
		صورة_الهوية_او_جواز_السفر: DF.Attach | None
		صورة_رخصة_القيادة: DF.Attach | None
		مكان_الإصدار: DF.Data | None
		ملاحظات: DF.Data | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Customer Car"
