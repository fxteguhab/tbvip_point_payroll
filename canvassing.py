from openerp.osv import osv, fields

# ==========================================================================================================================

class canvassing_canvas(osv.osv):
	_inherit = 'canvassing.canvas'
	
	def action_set_finish(self, cr, uid, ids, context={}):
		result = super(canvassing_canvas, self).action_set_finish(cr, uid, ids, context=context)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		for canvass in self.browse(cr, uid, ids):
			vehicle = canvass.fleet_vehicle_id
			employee_point_obj.input_point(cr, uid,
				activity_code='CANVASS',
				roles={
					'DRV1': [canvass.driver1_id.id],
					'DRV2': [canvass.driver2_id.id],
				},
				required_parameters={
					'VEHICLE_TYPE': vehicle.vehicle_type,
					'DISTANCE': canvass.distance,
					'SELF_OWN': vehicle.is_self_own,
				},
				reference='Canvassing - {}'.format(canvass.name),
				context=context)
		return result
