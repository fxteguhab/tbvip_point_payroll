from openerp.osv import osv, fields
from openerp.tools.translate import _


# ==========================================================================================================================

class tbvip_interbranch_stock_move(osv.Model):
	_inherit = 'tbvip.interbranch.stock.move'
	
	def create(self, cr, uid, vals, context=None):
		result = super(tbvip_interbranch_stock_move, self).create(cr, uid, vals, context)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		stock_location_obj = self.pool.get('stock.location')
		employee_point_obj.input_point(cr, uid,
			activity_code='INTERBRANCH_TRANSFER',
			roles={
				'ADM': [employee_obj.get_employee_id_from_user(cr, uid, vals['input_user_id'], context=context)],
				'EMP': [vals['prepare_employee_id']],
			},
			required_parameters={
				'ROW_COUNT': len(vals['interbranch_stock_move_line_ids']),
			},
			reference='Interbranch Transfer - From {} - To {}'.format(
				stock_location_obj.browse(cr, uid, vals['from_stock_location_id']).name,
				stock_location_obj.browse(cr, uid, vals['to_stock_location_id']).name),
			context=context)
		return result
	
	def action_accept(self, cr, uid, ids, context=None):
		result = self.action_accept(cr, uid, ids)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		for sm in self.browse(cr, uid, ids):
			employee_point_obj.input_point(cr, uid,
				activity_code='INTERBRANCH_TRANSFER',
				roles={
					'ADM': [employee_obj.get_employee_id_from_user(cr, uid, uid, context=context)],
					'EMP': [sm.checked_by_id.id],
				},
				required_parameters={
					'ROW_COUNT': len(sm.interbranch_stock_move_line_ids.ids),
				},
				reference='Interbranch Transfer - From {} - To {}'.format(
					sm.from_stock_location_id.name,
					sm.to_stock_location_id.name),
				context=context)
		return result
	
# ==========================================================================================================================

class tbvip_interbranch_stock_move_line(osv.Model):
	_name = 'tbvip.interbranch.stock.move.line'
	
	def write(self, cr, uid, ids, vals, context=None):
		result = super(tbvip_interbranch_stock_move_line, self).write(cr, uid, ids, vals, context=context)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		for sml in self.browse(cr, uid, ids):
			if sml.is_changed:
				employee_point_obj.input_point(cr, uid,
					activity_code='MODIFIED_INTERBRANCH_TRANSFER',
					roles={
						'ADM': [employee_obj.get_employee_id_from_user(cr, uid, vals['input_user_id'], context=context)],
						'EMP': [vals['prepare_employee_id']],
					},
					required_parameters={
						'ROW_COUNT': len(vals['interbranch_stock_move_line_ids']),
					},
					reference='Modified Interbranch Transfer - From {} - To {} - Product {}'.format(
						sml.header_id.from_stock_location_id.name,
						sml.header_id.to_stock_location_id.name,
						sml.product_id.name),
					context=context)
		return result