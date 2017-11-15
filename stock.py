from openerp.osv import osv, fields

# ===========================================================================================================================

class stock_inventory(osv.osv):
	
	_inherit = 'stock.inventory'
	
	_columns = {
		'branch_id': fields.many2one('tbvip.branch', 'Branch'),
	}
	
	_defaults = {
		'branch_id': lambda self, cr, uid, ctx: self.pool.get('res.users').browse(cr, uid, uid, ctx).branch_id.id,
	}
	
	# OVERRIDES -------------------------------------------------------------------------------------------------------------
	
	def action_done(self, cr, uid, ids, context=None):
		result = super(stock_inventory, self).action_done(cr, uid, ids, context=context)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		for inventory in self.browse(cr, uid, ids, context=context):
			row_total_qty = 0
			for line in inventory.line_ids:
				row_total_qty += line.product_qty
				delta_old_and_new_total_qty_line = abs(line.theoretical_qty - line.product_qty)
				# checking penalty
				if delta_old_and_new_total_qty_line > 0:
					branch_employee_ids = employee_obj.get_employee_id_from_branch(cr, uid, inventory.branch_id.id, context=context)
					employee_point_obj.input_point(cr, uid,
						activity_code='SO',
						roles={
							'EMPBRC': branch_employee_ids,
						},
						required_parameters={
							'OLD_QTY': line.theoretical_qty,
							'NEW_QTY': line.product_qty,
							'EMPLOYEE_BRANCH_COUNT': len(branch_employee_ids),
						},
						reference='Stock Opname - {}'.format(inventory.name),
						context=context)
			# point for doing task
			employee_point_obj.input_point(cr, uid,
				activity_code='SO',
				roles={
					'ADM': [employee_obj.get_employee_id_from_user(cr, uid, uid, context=context)],
					'EMP': [inventory.employee_id.id],
				},
				required_parameters={
					'ROW_QTY': row_total_qty
				},
				reference='Stock Opname - {}'.format(inventory.name),
				context=context)
		return result
