from openerp.osv import osv, fields

# ==========================================================================================================================

class purchase_order(osv.osv):
	_inherit = 'purchase.order'
	
	def wkf_confirm_order(self, cr, uid, ids, context=None):
		result = super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		for purchase in self.browse(cr, uid, ids, context=context):
			# who confirms
			employee_point_obj.input_point(cr, uid,
				activity_code='PURCHASE',
				roles={
					'ADM': [employee_obj.get_employee_id_from_user(cr, uid, uid, context=context)],
				},
				required_parameters={
				},
				reference='Purchase Order - {}'.format(purchase.name),
				context=context)
			# purchase creator
			employee_point_obj.input_point(cr, uid,
				activity_code='ORDER',
				roles={
					'ADM': [employee_obj.get_employee_id_from_user(cr, uid, purchase.create_uid.id, context=context)],
				},
				required_parameters={
					'BON_ROW_COUNT': len(purchase.order_line),
				},
				reference='Purchase Order - {}'.format(purchase.name),
				context=context)
		return result