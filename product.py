from openerp.osv import osv, fields

# ==========================================================================================================================

class product_product(osv.osv):
	_inherit = 'product.product'
	
	def create(self, cr, uid, vals, context=None):
		result = super(product_product, self).create(cr, uid, vals, context)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		employee_point_obj.input_point(cr, uid,
			activity_code='PRODUCT',
			roles={
				'ADM': [employee_obj.get_employee_id_from_user(cr, uid, uid, context=context)],
			},
			required_parameters={
			},
			reference='Product - {}'.format(vals.get('name', '')),
			context=context)
		return result
