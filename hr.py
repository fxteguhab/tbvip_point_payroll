from openerp.osv import osv, fields
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
from openerp.tools.translate import _

# ==========================================================================================================================

class hr_employee(osv.osv):
	_inherit = 'hr.employee'

	_columns = {
		'top_point': fields.float('TOP Point', readonly=True),
	}

	_defaults = {
		'top_point': 0,
	}
	
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
				event_date = datetime.now(),
				activity_code='ATTENDANCE',
				roles={
					'EMP': late_employee_ids,
				},
				required_parameters={
					'EARLY_MINUTES' : 0,
					'LATE_MINUTES': late_minutes,
					'EARLY_LEAVE_MINUTES': 0,
					'XTRA_MINUTES': 0,
				},
				reference='Attendance Late - {} minute(s)'.format(late_minutes),
				#reference='Attendance Late - {}'.format(date),
				context=context)

	def early_leave_attendance(self, cr, uid, late_employee_ids, erly_leave_minutes, date, context=None):
		if erly_leave_minutes > 0:
			employee_point_obj = self.pool.get('hr.point.employee.point')
			employee_point_obj.input_point(cr, uid,
				event_date = datetime.now(),
				activity_code='ATTENDANCE',
				roles={
					'EMP': late_employee_ids,
				},
				required_parameters={
					'EARLY_MINUTES' : 0,
					'LATE_MINUTES': 0,
					'EARLY_LEAVE_MINUTES': erly_leave_minutes,
					'XTRA_MINUTES': 0,
				},
				reference='Attendance Early Leave - {} minute(s)'.format(erly_leave_minutes),
				context=context)

	def early_start(self, cr, uid, overtime_employee_ids, early_minutes, date, context=None):
		if early_minutes > 0:
			employee_point_obj = self.pool.get('hr.point.employee.point')
			employee_point_obj.input_point(cr, uid,
				event_date = datetime.now(),
				activity_code='ATTENDANCE',
				roles={
					'EMP': overtime_employee_ids,
				},
				required_parameters={
					'EARLY_MINUTES' : early_minutes,
					'LATE_MINUTES': 0,
					'EARLY_LEAVE_MINUTES': 0,
					'XTRA_MINUTES': 0,
				},
				reference='Attendance Early - {} minute(s)'.format(early_minutes),
				#reference='Attendance Overtime - {}'.format(date),
				context=context)

	def overtime_attendance(self, cr, uid, overtime_employee_ids, overtime_minutes, date, context=None):
		if overtime_minutes > 0:
			employee_point_obj = self.pool.get('hr.point.employee.point')
			employee_point_obj.input_point(cr, uid,
				event_date = datetime.now(),
				activity_code='ATTENDANCE',
				roles={
					'EMP': overtime_employee_ids,
				},
				required_parameters={
					'EARLY_MINUTES' : 0,
					'LATE_MINUTES': 0,
					'EARLY_LEAVE_MINUTES': 0,
					'XTRA_MINUTES': overtime_minutes,
				},
				reference='Attendance Overtime - {} minute(s)'.format(overtime_minutes),
				#reference='Attendance Overtime - {}'.format(date),
				context=context)