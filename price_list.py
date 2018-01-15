
from openerp.osv import osv, fields
from openerp.tools.translate import _


# ==========================================================================================================================

class price_list(osv.osv):
	_inherit = 'price.list'
	
	def create(self, cr, uid, vals, context=None):
		result = super(price_list, self).create(cr, uid, vals, context)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		row_count = 0
		if vals['type'] == 'product':
			row_count += len(vals['line_product_ids'])
		elif vals['type'] == 'category':
			row_count += len(vals['line_category_ids'])
		employee_point_obj.input_point(cr, uid,
			activity_code='PRICE_LIST',
			roles={
				'ADM': [employee_obj.get_employee_id_from_user(cr, uid, uid, context=context)],
			},
			required_parameters={
				'ROW_COUNT': row_count,
			},
			reference='Price List - {}'.format(vals['name']),
			context=context)
		return result

# ==========================================================================================================================

class product_current_price(osv.osv):
	_inherit = 'product.current.price'
	
	def create(self, cr, uid, vals, context=None):
		result = super(product_current_price, self).create(cr, uid, vals, context)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		product_obj = self.pool.get('product.product')
		employee_point_obj.input_point(cr, uid,
			activity_code='PRODUCT_CURRENT_PRICE',
			roles={
				'ADM': [employee_obj.get_employee_id_from_user(cr, uid, uid, context=context)],
			},
			required_parameters={
			},
			reference='Product Current Price - {}'.format(product_obj.browse(cr, uid, vals['product_id']).name),
			context=context)
		return result
