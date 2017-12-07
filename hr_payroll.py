import collections
from openerp.osv import osv
from openerp.tools.translate import _


class hr_payslip(osv.Model):
	_inherit = 'hr.payslip'
	
	# OVERRIDES -----------------------------------------------------------------------------------------------------------------
	
	def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
		# insert branch_id to context to filter the search of exception working hours
		if employee_id and context:
			employee_obj = self.pool.get('hr.employee')
			employee = employee_obj.browse(cr, uid, employee_id)
			context = dict(context)
			context['branch_id'] = employee.user_id.branch_id.id
		result = super(hr_payslip, self).onchange_employee_id(cr, uid, ids, date_from, date_to, employee_id, contract_id, context)
		
		# Remove WORK100 from worked days
		values = result.get('value', False)
		to_be_deleted = -1
		if values:
			worked_days_line_ids = values.get('worked_days_line_ids', False)
			if isinstance(worked_days_line_ids, collections.Iterable):
				for idx, val in enumerate(worked_days_line_ids):
					if isinstance(val, dict):
						code = val.get('code', False)
						if code == 'WORK100':
							to_be_deleted = idx
					break
			if to_be_deleted >= 0:
				worked_days_line_ids.pop(to_be_deleted)
		return result
	
	def hr_verify_sheet(self, cr, uid, ids, context=None):
		result = self.compute_sheet(cr, uid, ids, context)
		for payslip in self.browse(cr, uid, ids, context):
			employee_week_payroll_ids = self.search(cr, uid, [
				('date_week', '=', payslip.date_week),
				('date_year', '=', payslip.date_year),
				('employee_id', '=', payslip.employee_id.id),
				('state', '=', 'done'),
			], context=context)
			if employee_week_payroll_ids and len(employee_week_payroll_ids) > 0:
				raise osv.except_osv(_('Error!'), _("This employee has already had confirmed payslip in the same week and year."))
		
		hr_attendance_obj = self.pool.get('hr.attendance')
		# Input Points per date
		for date_obj in result['total_overtime_and_late_per_date']:
			hr_attendance_obj.late_attendance(cr, uid, [result['employee_id']],
				date_obj['late'] + date_obj['early_leave'], date_obj['date'], context=context)
			hr_attendance_obj.overtime_attendance(cr, uid, [result['employee_id']],
				date_obj['early_overtime'] + date_obj['late_overtime'], date_obj['date'], context=context)
		self.compute_sheet(cr, uid, ids, context)  # compute sheet once again to rewrite xtra / penalty if there's any change
		return super(hr_payslip, self).hr_verify_sheet(cr, uid, ids, context)