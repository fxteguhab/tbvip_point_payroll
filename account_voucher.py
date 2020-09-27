from openerp.osv import osv, fields
from datetime import datetime, date, timedelta

# ==========================================================================================================================

class account_voucher(osv.osv):
	_inherit = 'account.voucher'
	
	# OVERRIDES -------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, val, context=None):
		result = super(account_voucher, self).create(cr, uid, val, context=context)
		voucher = self.browse(cr, uid, result)
		if voucher.type == 'payment':
			employee_point_obj = self.pool.get('hr.point.employee.point')
			employee_obj = self.pool.get('hr.employee')
			employee_point_obj.input_point(cr, uid,
				event_date = voucher.create_date,
				activity_code='SUPPLIER_PAYMENT_SAVE',
				roles={
					'ADM': [employee_obj.get_employee_id_from_user(cr, uid, uid, context=context)],
				},
				required_parameters={},
				reference='Supplier Payment Create- {}'.format(voucher.number),
				context=context)
			
		return result
	
	def proforma_voucher(self, cr, uid, ids, context=None):
		result = super(account_voucher, self).proforma_voucher(cr, uid, ids, context=context)
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		# point for doing task
		for voucher in self.browse(cr, uid, ids):
		# Customer Payment
			if voucher.type == 'receipt':
				employee_point_obj.input_point(cr, uid,
				event_date = voucher.create_date,	
				activity_code='CUSTOMER_PAYMENT',
				roles={
					'ADM': [employee_obj.get_employee_id_from_user(cr, uid, uid, context=context)],
				},
				required_parameters={},
				reference='Customer Payment - {}'.format(voucher.number),
					context=context)
		# Supplier Payment
			elif voucher.type == 'payment':
				employee_point_obj.input_point(cr, uid,
					event_date = voucher.create_date,
					activity_code='SUPPLIER_PAYMENT_VALIDATE',
					roles={
						'ADM': [employee_obj.get_employee_id_from_user(cr, uid, uid, context=context)],
					},
					required_parameters={},
					reference='Supplier Payment - {}'.format(voucher.number),
					context=context)
		
		return result