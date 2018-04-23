from openerp.osv import osv, fields

# ===========================================================================================================================

class sale_order(osv.osv):
	_inherit = 'sale.order'
	
	# COLUMNS ---------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'price_type_id': fields.many2one('price.type', 'Price Type', required=True, ondelete='restrict', domain="[('type','=','sell')]", readonly="True", states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
	}
	
	def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
		result = super(sale_order, self).onchange_partner_id(cr, uid, ids, partner_id, context=context)
		partner_obj = self.pool.get('res.partner')
		partner = partner_obj.browse(cr, uid, partner_id)
		if result:
			result['value']['price_type_id'] = partner.sell_price_type_id.id
		return result
	
# ===========================================================================================================================

class sale_order_line(osv.osv):
	_inherit = 'sale.order.line'
	
	# COLUMNS ---------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'price_type_id': fields.many2one('price.type', 'Price Type', required=True, ondelete='restrict', domain="[('type','=','sell')]"),
	}
	
	# OVERRIDES -------------------------------------------------------------------------------------------------------------
	
	def onchange_product_id_price_list(self, cr, uid, ids, pricelist, product, qty=0,
			uom=False, qty_uos=0, uos=False, name='', partner_id=False,
			lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False,
			warehouse_id=False, parent_price_type_id=False, price_type_id=False, context=None):
		result = super(sale_order_line, self).product_id_change_with_wh(cr, uid, ids, pricelist, product, qty, uom,
			qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag, warehouse_id, context);
		result['value']['product_uom'] = uom
		if price_type_id == False:
			if parent_price_type_id:
				price_type_id = parent_price_type_id
				if result:
					result['value']['price_type_id'] = parent_price_type_id
				else:
					result = { 'value': { 'price_type_id': parent_price_type_id } }
		product_current_price_obj = self.pool.get('product.current.price')
		current_price = product_current_price_obj.get_current_price(cr, uid, product, price_type_id, uom)
		result['value']['price_unit'] = current_price
		if current_price == 0 and product != 0:
			pass # TODO ini terpanggil berkali2 jadi meskipun pernah dapet current price, ketika ketemu yg ngga dapet keluar warn
			# result['warning'] = {}
			# result['warning']['message'] = 'No price! : This product doesn\'t have any price for this price type and uom'
			# result['warning']['title'] = 'Set Price Error!'
		return result