from openerp.osv import osv, fields
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
from openerp.tools.translate import _

# ==========================================================================================================================

class hr_employee(osv.osv):
	_inherit = 'hr.employee'
	
	def get_employee_id_from_user(self, cr, uid, user_id, context=None):
		employee_ids = self.search(cr, uid, [
			('user_id', '=', user_id),
		], limit=1, context=context)
		if employee_ids and len(employee_ids) == 1:
			return employee_ids[0]
		else:
			return 0
	
	def get_employee_id_from_branch(self, cr, uid, branch_id, context=None):
		user_obj = self.pool.get('res.users')
		user_ids = user_obj.search(cr, uid, [
			('branch_id', '=', branch_id)
		], context=context)
		employee_ids = self.search(cr, uid, [
			('user_id', 'in', user_ids),
		], context=context)
		return employee_ids