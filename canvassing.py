from openerp.osv import osv, fields
from datetime import datetime

# ==========================================================================================================================

class canvassing_canvas(osv.osv):
	_inherit = 'canvassing.canvas'
	
	def action_set_finish(self, cr, uid, ids, context={}):
		result = super(canvassing_canvas, self).action_set_finish(cr, uid, ids, context=context)
		fmt = '%H:%M:%S'
		#get max load time limit
		param_obj = self.pool.get('ir.config_parameter')
		param_ids = param_obj.search(cr, uid, [('key','in',['max_load_time'])])
		max_load_time_limit = 0
		for param_data in param_obj.browse(cr, uid, param_ids):
			if param_data.key == 'max_load_time':
				max_load_time_limit = datetime.strptime(param_data.value, fmt)
				
		# input points
		sale_order_obj = self.pool('sale.order')
		employee_obj = self.pool.get('hr.employee')
		employee_point_obj = self.pool.get('hr.point.employee.point')

		for canvass in self.browse(cr, uid, ids):
			vehicle = canvass.fleet_vehicle_id
			employee_ids = []
			time_diff = 0
			for line in canvass.stock_line_ids:
				try:
					delivery_time = datetime.strptime(line.load_time, fmt)
				except:
					delivery_time = datetime.strptime("23:59:59", fmt)

				if (delivery_time > max_load_time_limit):	
					sale_order_id = sale_order_obj.search(cr,uid,[('name', '=', line.stock_picking_id.origin)], limit=1)
					sale_order = sale_order_obj.browse(cr, uid, sale_order_id[0])
					inputer_id = employee_obj.get_employee_id_from_user(cr, uid, sale_order.create_uid.id, context=context)
					employee_ids.append(sale_order.employee_id.id)	
					employee_ids.append(inputer_id)	

			time_diff = (datetime.strptime(canvass.max_load_time, fmt) - max_load_time_limit).total_seconds()
			if (time_diff < 0):
				time_diff = 0

			employee_point_obj.input_point(cr, uid,
				activity_code='CANVASS',
				roles={
					'DRV1': [canvass.driver1_id.id],
					'DRV2': [canvass.driver2_id.id],
					'EMP' : employee_ids,
				},
				required_parameters={
					'VEHICLE_TYPE': vehicle.vehicle_type,
					'DISTANCE': canvass.distance,
					'SELF_OWN': vehicle.is_self_own,
					'MAX_TIME_DIFF':time_diff/60, #telat n minute(s)
				},
				reference='Delivery - {}'.format(canvass.name),
				context=context)
		return result
