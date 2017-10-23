from openerp.osv import osv, fields

# ==========================================================================================================================

class purchase_order(osv.osv):
	_inherit = 'purchase.order'
	
	def wkf_confirm_order(self, cr, uid, ids, context=None):
		result = super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		for purchase in self.browse(cr, uid, ids):
			employee_point_obj.input_point(cr, uid,
				activity_code='PURCHASE',
				roles={
					'ADM': uid,
				},
				required_parameters={
				},
				context=context)
		return result