from openerp.osv import osv, fields

# ===========================================================================================================================

class stock_inventory(osv.osv):
	
	_inherit = 'stock.inventory'
	
	# OVERRIDES -------------------------------------------------------------------------------------------------------------
	
	def action_done(self, cr, uid, ids, context=None):
		result = super(stock_inventory, self).action_done(cr, uid, ids, context=context)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		for inventory in self.browse(cr, uid, ids, context=context):
			row_qty = 0
			for line in inventory.line_ids:
				row_qty += line.product_qty
			employee_point_obj.input_point(cr, uid,
				activity_code='SO',
				roles={
					'ADM': uid,
					'EMP': inventory.employee_id.id,
				},
				required_parameters={
					'ROW_QTY': row_qty
				},
				context=context)
		return result
