from openerp.osv import osv, fields

# ==========================================================================================================================

class canvassing_canvas(osv.osv):
	_inherit = 'canvassing.canvas'
	
	def action_set_finish(self, cr, uid, ids, context={}):
		result = super(canvassing_canvas, self).action_set_finish(cr, uid, ids, context=context)
		# input points
		
		
		return result
	