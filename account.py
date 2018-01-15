from datetime import datetime, timedelta
from openerp.osv import osv, fields

# ==========================================================================================================================

class tbvip_day_end(osv.osv):
	_inherit = 'tbvip.day.end'
	
	def create(self, cr, uid, vals, context={}):
		result_id = super(tbvip_day_end, self).create(cr, uid, vals, context)
		
		employee_obj = self.pool.get('hr.employee')
		employee_point_obj = self.pool.get('hr.point.employee.point')
		
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
					reference='Day End - {} - Correction {}'.format(day_end_date_datetime, vals['amend_number']),
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
			reference='Day End - {}'.format(day_end_date_datetime),
			context=context)
		return result_id
