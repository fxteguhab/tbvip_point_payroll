from openerp.osv import osv, fields

# ===========================================================================================================================

class sale_order(osv.osv):
	_inherit = 'sale.order'
	
	def action_button_confirm(self, cr, uid, ids, context=None):
		result = super(sale_order, self).action_button_confirm(cr, uid, ids, context)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		for sale in self.browse(cr, uid, ids):
			value = sale.amount_total
			row_count = len(sale.order_line)
			qty_sum = 0
			for line in sale.order_line:
				qty_sum += line.product_uom_qty
			# sales confirm (who confirm and employee responsible for the sales)
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
			# sales draft creator
			employee_ids = employee_obj.search(cr, uid, [
				('user_id', '=', sale.create_uid.id),
			], limit=1, context=context)
			if employee_ids and len(employee_ids) == 1:
				employee_point_obj.input_point(cr, uid,
					activity_code='ORDER',
					roles={
						'ADM': employee_ids[0],
					},
					required_parameters={
						'BON_ROW_COUNT': row_count,
					},
					context=context)
		return result
	

# ===========================================================================================================================
