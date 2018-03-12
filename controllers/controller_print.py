from openerp import http
from openerp.tools.translate import _
from openerp.http import request
from datetime import datetime, date, timedelta

from openerp.addons.tbvip.controllers.controller_print import controller_print

class custom_controller_print(controller_print):

	def print_payslip_dot_matrix(self, payslip):
		result = super(custom_controller_print, self).print_payslip_dot_matrix(payslip)
	# tambahkan baris TOP Point
	# pecah dulu result asalnya ke baris2
		result_lines = result.split('\n')
		top_point = 0
		for input_line in payslip.input_line_ids:
			if input_line.code == 'TOP_POIN_BASIC':
				top_point = input_line.amount
		top_line = '|           |        |     |            |    |        |        |TOP Poin    |%-12s|' % int(top_point)
		result_lines = result_lines[:-3] + [top_line] + result_lines[-3:]
		return "\n".join(result_lines)

