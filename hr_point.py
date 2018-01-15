from openerp.osv import osv
from datetime import datetime, timedelta


class hr_point_type(osv.Model):
	_inherit = 'hr.point.type'
	
	# OVERRIDES -----------------------------------------------------------------------------------------------------------------
	
	def _create_salary_rule(self, cr, uid, point_type_name, context=None):
		"""
		Adds if inputs.POIN_SALES_POINT.amount > 0 else 0 clause for every created salary rules' python codes of hr_point_type for TBVIP
		"""
		salary_rule_obj = self.pool.get('hr.salary.rule')
		result = super(hr_point_type, self)._create_salary_rule(cr, uid, point_type_name, context)
		salary = salary_rule_obj.browse(cr, uid, [result], context)
		salary.amount_python_compute = salary.amount_python_compute + ' if inputs.POIN_SALES_POINT.amount > 0 else 0'
		return result

	def action_reset_all_points(self, cr, uid, ids, context=None):
		employee_obj = self.pool.get('hr.employee')
		employee_level_obj = self.pool.get('hr.employee.level')
		employee_point_obj = self.pool.get('hr.point.employee.point')
		additional_activity_log_obj = self.pool.get('tbvip.additional.activity.log')
		
		# remove all additional activities
		all_additional_activity_ids = additional_activity_log_obj.search(cr, uid, [], context=context)
		additional_activity_log_obj.unlink(cr, uid, all_additional_activity_ids, context=context)
		
		# remove all point history
		all_employee_point_ids = employee_point_obj.search(cr, uid, [], context=context)
		employee_point_obj.unlink(cr, uid, all_employee_point_ids, context=context)
		
		# reset employee total point and level
		all_employee_ids = employee_obj.search(cr, uid, [], context=context)
		employee_obj.write(cr, uid, all_employee_ids, {
			'total_point': 0,
			'employee_level_id': employee_level_obj.get_employee_lowest_level_id(cr, uid, context=context),  # cannot use calculate_employee_level because level assignment only done if the new level is higher
		}, context=context)

class hr_point_employee_point(osv.Model):
	_name = 'hr.point.employee.point'
	
	def cron_generate_top_point(self, cr, uid, context={}):
		branch_obj = self.pool.get('tbvip.branch')
		employee_obj = self.pool.get('hr.employee')
		point_type_obj = self.pool.get('hr.point.type')
		employee_points = {}
		
		# Calculate today's points ( today = day_end_date )
		for branch_id in branch_obj.search(cr, uid, [], context=context):
			branch_employee_ids = employee_obj.get_employee_id_from_branch(cr, uid, branch_id, context=context)
			total_branch_point = 0
			for branch_employee_id in branch_employee_ids:
				employee_points[branch_employee_id] = 0
				# get employee points for today
				today_employee_point_ids = self.search(cr, uid, [
					('event_date', '>=', datetime.now().strftime("%Y-%m-%d 00:00:00")),
					('event_date', '<=', datetime.now().strftime("%Y-%m-%d 23:59:59")),
					('employee_id', '=', branch_employee_id)
				], context=context)
				today_employee_points = self.browse(cr, uid, today_employee_point_ids, context=context)
				for today_employee_point in today_employee_points:
					employee_points[branch_employee_id] += today_employee_point.point # add to employee points
					total_branch_point += today_employee_point.point # add to total
			if total_branch_point > 0:
				# if total branch point positive, calculate
				for branch_employee_id in branch_employee_ids:
					employee_points[branch_employee_id] = employee_points[branch_employee_id] / total_branch_point
			else:
				# if total branch point is zero or negative, no one gets anything
				for branch_employee_id in branch_employee_ids:
					employee_points[branch_employee_id] = 0
		
		# Search employee with the highest point from all branches
		top_employee_id = 0
		current_highest_point = 0
		for employee_id in employee_points:
			if employee_points[employee_id] > current_highest_point:
				current_highest_point = employee_points[employee_id]
				top_employee_id = employee_id
		
		# Input point TOP today if highest point of employee is not zero
		if current_highest_point > 0:
			point_type_ids = point_type_obj.search(cr, uid, [
				('name', '=', 'POIN_TOP')
			], limit=1, context=context)
			if point_type_ids and len(point_type_ids) == 1:
				employee_point_vals = {
					'event_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
					'employee_id': top_employee_id,
					'point_type_id': point_type_ids[0],
					'point': 1,
					'reference': 'CRON - Generate Top Point',
				}
				new_id = self.create(cr, uid, employee_point_vals, context)
				print 'ID: ' + new_id