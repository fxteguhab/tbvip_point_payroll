from datetime import datetime, timedelta
from openerp.osv import osv, fields

# ==========================================================================================================================

class tbvip_day_end(osv.osv):
	_inherit = 'tbvip.day.end'
	
	def action_end_day(self, cr, uid, vals, context={}):
		branch_obj = self.pool.get('tbvip.branch')
		employee_obj = self.pool.get('hr.employee')
		employee_point_obj = self.pool.get('hr.point.employee.point')
		model_obj = self.pool.get('ir.model.data')

		employee_points = {}
		today = datetime.now()
		today_start = today.strftime("%Y-%m-%d 00:00:00")
		today_end = (today + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
		
		# Calculate today's points
		for branch_id in branch_obj.search(cr, uid, [], context=context):
			branch_employee_ids = employee_obj.get_employee_id_from_branch(cr, uid, branch_id, context=context)
			total_branch_point = 0
			for branch_employee_id in branch_employee_ids:
				employee_points[branch_employee_id] = 0
				# get employee points for today
				today_employee_point_ids = employee_point_obj.search(cr, uid, [
					('event_date', '>=', today_start),
					('event_date', '<', today_end),
					('employee_id', '=', branch_employee_id)
				], context=context)
				today_employee_points = employee_point_obj.browse(cr, uid, today_employee_point_ids, context=context)
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
			model, point_type_id = model_obj.get_object_reference(cr, uid, 'tbvip_point_payroll', 'hr_point_type_top')
			employee_point_vals = {
				'event_date': datetime.now(),
				'employee_id': top_employee_id,
				'point_type_id': point_type_id,
				'point': 1
			}
			new_employee_point_id = employee_point_obj.create(cr, uid, employee_point_vals, context)
		return True