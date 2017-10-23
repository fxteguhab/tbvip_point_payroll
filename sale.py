from openerp.osv import osv, fields

# ===========================================================================================================================

class sale_order(osv.osv):
	_inherit = 'sale.order'
	
	def action_button_confirm(self, cr, uid, ids, context=None):
		result = super(sale_order, self).action_button_confirm(cr, uid, ids, context)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		for sale in self.browse(cr, uid, ids):
			value = sale.amount_total
			row_count = len(sale.order_line)
			qty_sum = 0
			for line in sale.order_line:
				qty_sum += line.product_uom_qty
			employee_point_obj.input_point(cr, uid,
				activity_code='SALES',
				roles={
					'ADM': uid,
					'EMP': sale.employee_id.id,
				},
				required_parameters={
					'BON_VALUE': value,
					'BON_QTY_SUM': qty_sum,
					'BON_ROW_COUNT': row_count,
				},
				context=context)
		return result
	

# ===========================================================================================================================
