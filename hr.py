from openerp.osv import osv, fields
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
from openerp.tools.translate import _

# ==========================================================================================================================

class hr_employee(osv.osv):
	_inherit = 'hr.employee'
	
	def get_employee_id_from_user(self, cr, uid, user_id, context=None):
		employee_ids = self.search(cr, uid, [
			('user_id', '=', user_id),
		], limit=1, context=context)
		if employee_ids and len(employee_ids) == 1:
			return employee_ids[0]
		else:
			return 0
	
	def get_employee_id_from_branch(self, cr, uid, branch_id, context=None):
		user_obj = self.pool.get('res.users')
		user_ids = user_obj.search(cr, uid, [
			('branch_id', '=', branch_id)
		], context=context)
		employee_ids = self.search(cr, uid, [
			('user_id', 'in', user_ids),
		], context=context)
		return employee_ids


# ==========================================================================================================================

class hr_contract(osv.osv):
	_inherit = 'hr.contract'
	
	_defaults = {
		'working_hours': lambda self, cr, uid, ctx: self.pool.get('ir.model.data')
			.get_object(cr, uid, 'tbvip_point_payroll', 'resource_standard_working_schedule').id,
	}


# ==========================================================================================================================

class hr_attendance(osv.osv):
	_inherit = 'hr.attendance'

	def late_attendance(self, cr, uid, late_employee_ids, late_minutes, date, context=None):
		if late_minutes > 0:
			employee_point_obj = self.pool.get('hr.point.employee.point')
			employee_point_obj.input_point(cr, uid,
				activity_code='ATTENDANCE',
				roles={
					'EMP': late_employee_ids,
				},
				required_parameters={
					'LATE_MINUTES': late_minutes,
					'XTRA_MINUTES': 0,
				},
				reference='Attendance Late - {}'.format(date),
				context=context)

	def overtime_attendance(self, cr, uid, overtime_employee_ids, overtime_minutes, date, context=None):
		if overtime_minutes > 0:
			employee_point_obj = self.pool.get('hr.point.employee.point')
			employee_point_obj.input_point(cr, uid,
				activity_code='ATTENDANCE',
				roles={
					'EMP': overtime_employee_ids,
				},
				required_parameters={
					'LATE_MINUTES': 0,
					'XTRA_MINUTES': overtime_minutes,
				},
				reference='Attendance Overtime - {}'.format(date),
				context=context)