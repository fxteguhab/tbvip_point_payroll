from openerp.osv import osv, fields
from datetime import datetime, timedelta
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
	#VALIDATE STOCK OPNAME
	def action_done(self, cr, uid, ids, context=None):
		result = super(stock_inventory, self).action_done(cr, uid, ids, context=context)
		# input points
		is_override =context.get('is_override', False)
		if is_override:
			activity_str = 'OVERRIDE_STOCK_OPNAME'
		else:
			activity_str = 'SO'
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
						event_date= datetime.now(),
						activity_code=activity_str,
						roles={
							'EMPBRC': branch_employee_ids,
						},
						required_parameters={
							'OLD_QTY': line.theoretical_qty,
							'NEW_QTY': line.product_qty,
							'EMPLOYEE_BRANCH_COUNT': len(branch_employee_ids),
						},
						#reference='Stock Opname - {}'.format(inventory.name),
						reference= inventory.name + ' @{}'.format(inventory.location_id.name),
						context=context)
			# point for doing task
			employee_point_obj.input_point(cr, uid,
				event_date= datetime.now(),
				activity_code=activity_str,
				roles={
					'ADM': [employee_obj.get_employee_id_from_user(cr, uid, uid, context=context)],
					'EMP': [inventory.employee_id.id],
					'EMPALL': [inventory.employee_id.id],
				},
				required_parameters={
					'ROW_QTY': row_total_qty,
					'ROW_COUNT': len(inventory.line_ids),
				},
				#reference='Stock Opname - {}'.format(inventory.name),
				reference= inventory.name + ' @{}'.format(inventory.location_id.name),
				context=context)
		return result


class stock_bonus_usage(osv.osv):
	_inherit = 'stock.bonus.usage'
	
	def action_approve(self, cr, uid, ids, context=None):
		result = super(stock_bonus_usage, self).action_approve(cr, uid, ids, context)
		for bonus_usage in self.browse(cr, uid, ids, context=context):
			self.pool.get('hr.point.employee.point').input_point(cr, uid,
				event_date= datetime.now(),
				activity_code='BONUS_PRODUCT_USAGE',
				roles={
					'ADM': [uid],
				},
				required_parameters={
					'ROW_COUNT': len(bonus_usage.bonus_usage_line_ids),
				},
				reference='Approve Bonus Usage - {}'.format(bonus_usage.name),
				context=context)
		return result