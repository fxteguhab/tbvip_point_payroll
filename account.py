from datetime import datetime, timedelta
from openerp.osv import osv, fields

# ==========================================================================================================================

class tbvip_day_end(osv.osv):
	_inherit = 'tbvip.day.end'
	
	def create(self, cr, uid, vals, context={}):
		result_id = super(tbvip_day_end, self).create(cr, uid, vals, context)
		
		branch_obj = self.pool.get('tbvip.branch')
		employee_obj = self.pool.get('hr.employee')
		point_type_obj = self.pool.get('hr.point.type')
		employee_point_obj = self.pool.get('hr.point.employee.point')
		model_obj = self.pool.get('ir.model.data')
		
		day_end_date = vals['day_end_date']
		day_end_date_datetime = datetime.strptime(day_end_date, '%Y-%m-%d %H:%M:%S')
		day_end_date_start = day_end_date_datetime.strftime("%Y-%m-%d 00:00:00")
		day_end_date_end = (day_end_date_datetime + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
		branch_employee_ids = employee_obj.get_employee_id_from_branch(cr, uid, vals['branch_id'], context=context)
		if vals['amend_number'] > 0:
			# get latest day end for this date
			last_day_end_ids = self.search(cr, uid, [
				('id', '!=', result_id),
				('branch_id', '=', vals['branch_id']),
				('day_end_date', '>=', day_end_date_start),
				('day_end_date', '<', day_end_date_end),
			], limit=1, order="day_end_date DESC", context=context)
			if last_day_end_ids and len(last_day_end_ids) > 0:
				last_day_end = self.browse(cr, uid, last_day_end_ids[0], context=context)
				# deduct point from the latest
				employee_point_obj.cancel_input_point(cr, uid,
					activity_code='CASH_BALANCE',
					roles={
						'ADM': [employee_obj.get_employee_id_from_user(cr, uid, last_day_end.create_uid.id, context=context)],
						'EMPBRC': branch_employee_ids,
					},
					required_parameters={
						'BALANCE':  last_day_end.balance,
					},
					context=context)
		
		# input point if balanced or not, can be extra or penalty
		employee_point_obj.input_point(cr, uid,
			activity_code='CASH_BALANCE',
			roles={
				'ADM': [employee_obj.get_employee_id_from_user(cr, uid, uid, context=context)],
				'EMPBRC': branch_employee_ids,
			},
			required_parameters={
				'BALANCE':  vals['balance'],
			},
			context=context)
		
		if vals['amend_number'] == 0:
			# TOP
			employee_points = {}
			# Calculate today's points ( today = day_end_date )
			for branch_id in branch_obj.search(cr, uid, [], context=context):
				branch_employee_ids = employee_obj.get_employee_id_from_branch(cr, uid, branch_id, context=context)
				total_branch_point = 0
				for branch_employee_id in branch_employee_ids:
					employee_points[branch_employee_id] = 0
					# get employee points for today
					today_employee_point_ids = employee_point_obj.search(cr, uid, [
						('event_date', '>=', day_end_date_start),
						('event_date', '<', day_end_date_end),
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
				point_type_ids = point_type_obj.search(cr, uid, [
					('name', '=', 'POIN_TOP')
				], limit=1, context=context)
				if point_type_ids and len(point_type_ids) == 1:
					employee_point_vals = {
						'event_date': datetime.now(),
						'employee_id': top_employee_id,
						'point_type_id': point_type_ids[0],
						'point': 1
					}
					new_employee_point_id = employee_point_obj.create(cr, uid, employee_point_vals, context)
		return result_id