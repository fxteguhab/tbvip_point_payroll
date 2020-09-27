from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, timedelta

# ==========================================================================================================================

class tbvip_interbranch_stock_move(osv.Model):
	_inherit = 'tbvip.interbranch.stock.move'
	
	def action_accept(self, cr, uid, ids, context=None):
		result = super(tbvip_interbranch_stock_move, self).action_accept(cr, uid, ids)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		for sm in self.browse(cr, uid, ids):
			# sender
			employee_point_obj.input_point(cr, uid,
				event_date= datetime.now(),
				activity_code='INTERBRANCH_TRANSFER_SEND',
				roles={
					'ADM': [employee_obj.get_employee_id_from_user(cr, uid, sm.input_user_id.id, context=context)],
					'EMP': [sm.prepare_employee_id.id],
				},
				required_parameters={
					'ROW_COUNT': len(sm.interbranch_stock_move_line_ids.ids),
				},
				reference='Interbranch Transfer - From {} - To {}'.format(
					sm.from_stock_location_id.name,
					sm.to_stock_location_id.name),
				context=context)
			
			# receiver
			employee_point_obj.input_point(cr, uid,
				event_date= datetime.now(),
				activity_code='INTERBRANCH_TRANSFER_RECEIVE',
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
	_inherit = 'tbvip.interbranch.stock.move.line'
	
	def write(self, cr, uid, ids, vals, context=None):
		result = super(tbvip_interbranch_stock_move_line, self).write(cr, uid, ids, vals, context=context)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		if not vals.get('is_changed', False):
			for sml in self.browse(cr, uid, ids):
				if sml.is_changed:
					employee_point_obj.input_point(cr, uid,
						event_date= datetime.now(),
						activity_code='MODIFIED_INTERBRANCH_TRANSFER',
						roles={
							'ADM': [employee_obj.get_employee_id_from_user(cr, uid, sml.header_id.input_user_id.id, context=context)],
							'EMP': [sml.header_id.prepare_employee_id.id],
						},
						required_parameters={
						},
						reference='Modified Interbranch Transfer - From {} - To {} - Product {}'.format(
							sml.header_id.from_stock_location_id.name,
							sml.header_id.to_stock_location_id.name,
							sml.product_id.name),
						context=context)
		return result