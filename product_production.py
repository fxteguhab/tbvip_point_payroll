from openerp.osv import osv, fields

class product_production(osv.osv):
	_inherit = "product.production"

	def action_finish(self, cr, uid, ids, context=None):
		result = super(product_production, self).action_finish(cr, uid, ids, context=context)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		for pp in self.browse(cr, uid, ids):
			employee_point_obj.input_point(cr, uid,
				activity_code='DIRECT_PRODUCTION',
				roles={
					'ADM': [employee_obj.get_employee_id_from_user(cr, uid, uid, context=context)],
				},
				required_parameters={
				},
				reference='Direct Production - {}'.format(pp.id),
				context=context)
		return result
