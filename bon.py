from openerp.osv import osv, fields
from openerp.tools.translate import _


# ==========================================================================================================================

class tbvip_bon_book(osv.osv):
	_inherit = "tbvip.bon.book"
	
	def create(self, cr, uid, vals, context=None):
		result = super(tbvip_bon_book, self).create(cr, uid, vals, context)
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		employee_point_obj.input_point(cr, uid,
			activity_code='BON_BOOK',
			roles={
				'ADM': [employee_obj.get_employee_id_from_user(cr, uid, uid, context=context)],
			},
			required_parameters={
			},
			reference='Bon Book - {}'.format(vals['issue_date']),
			context=context)
		return result