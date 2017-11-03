from openerp.osv import osv


class hr_payslip(osv.Model):
	_inherit = 'hr.payslip'
	
	# OVERRIDES -----------------------------------------------------------------------------------------------------------------
	
	def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
		result = super(hr_payslip, self).onchange_employee_id(cr, uid, ids, date_from, date_to,employee_id, contract_id, context)
		
		# Remove WORK100 from worked days
		values = result.get('value', False)
		to_be_deleted = -1
		if values:
			worked_days_line_ids = values.get('worked_days_line_ids', False)
			for idx, val in enumerate(worked_days_line_ids):
				if isinstance(val, dict):
					code = val.get('code', False)
					if code == 'WORK100':
						to_be_deleted = idx
				break
			if to_be_deleted >= 0:
				worked_days_line_ids.pop(to_be_deleted)
		return result