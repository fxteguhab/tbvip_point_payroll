from openerp.osv import fields, osv

class stock_opname_memory(osv.osv_memory):
	_inherit = 'stock.opname.memory'
	
	_columns = {
		'branch_id': fields.many2one('tbvip.branch', 'Branch'),
	}
	
	_defaults = {
		'branch_id': lambda self, cr, uid, ctx: self.pool.get('res.users').browse(cr, uid, uid, ctx).branch_id.id,
	}
	
	def action_generate_stock_opname(self, cr, uid, ids, context=None):
		result = super(stock_opname_memory, self).action_generate_stock_opname(cr, uid, ids, context=context)
		if result and result.get('res_id', False):
			stock_inventory_obj = self.pool.get('stock.inventory')
			stock_inventory_id = result['res_id']
			# memory assumed only one
			for memory in self.browse(cr, uid, ids):
				stock_inventory_obj.write(cr, uid, [stock_inventory_id], {
					'branch_id': memory.branch_id.id
				}, context=context)
				break
		# hook for point override_so
		if context.get('is_override', False):
			for memory in self.browse(cr, uid, ids):
				row_qty = 0
				for line_id in memory.line_ids:
					row_qty += line_id.product_qty
				self.pool.get('hr.point.employee.point').input_point(cr, uid,
					activity_code='OVERRIDE_STOCK_OPNAME',
					roles={
						'ADM': [uid],
						'EMPBRC': [uid],
						'EMPALL': [uid],
					},
					required_parameters={
						'ROW_QTY': row_qty,
						'ROW_COUNT': len(memory.line_ids),
					},
					reference='SO Override - {}'.format(memory.location_id.name),
					context=context)
		
		return result
