from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp.tools.translate import _


# ==========================================================================================================================

class tbvip_bon_book(osv.osv):
	_inherit = "tbvip.bon.book"
	
	def create(self, cr, uid, vals, context=None):
		result = super(tbvip_bon_book, self).create(cr, uid, vals, context)
		residual = 	self._cek_last_book_residual(cr,uid,vals['employee_id'],vals['branch_id'])
		# input points
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		employee_point_obj.input_point(cr, uid,
			event_date = datetime.now(),
			activity_code='BON_BOOK',
			roles={
				'ADM': [employee_obj.get_employee_id_from_user(cr, uid, uid, context=context)],
				'EMP': [vals['employee_id']],
			},
			required_parameters={
				'RESIDUAL' : residual,
			},
			reference='Bon Book - {}'.format(vals['issue_date']),
			context=context)
		return result