from datetime import datetime
from openerp.osv import osv, fields
from openerp.tools.translate import _


# ===========================================================================================================================


class tbvip_additional_activity(osv.osv):
	_name = 'tbvip.additional.activity'
	_description = 'Additional Activity'
	
# COLUMNS -------------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'name': fields.char('Name', required=True),
		'desc': fields.text('Description', required=True),
	}

# ===========================================================================================================================


class tbvip_additional_activity_log(osv.osv):
	_name = 'tbvip.additional.activity.log'
	_description = 'Additional Activity Log'
	
# COLUMNS -------------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
		'branch_id': fields.many2one('tbvip.branch', 'Branch', required=True),
		'activity_time': fields.datetime('Time', required=True),
		'additional_activity_id': fields.many2one('tbvip.additional.activity', 'Activity', required=True),
		'point': fields.float('Point', required=True),
		'employee_point_id': fields.many2one('hr.point.employee.point', 'Employee Point', ondelete='set null'),
	}
	
# DEFAULTS ------------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'activity_time': datetime.now(),
		'branch_id': lambda self, cr, uid, *args: self.pool.get('res.users').browse(cr, uid, [uid]).branch_id.id,
	}
	
# OVERRIDES -----------------------------------------------------------------------------------------------------------------
	
	def name_get(self, cr, uid, ids, context=None):
		result = []
		for activity_log in self.browse(cr, uid, ids, context):
			name = "{log.activity_time} | {log.employee_id.name} -> {log.additional_activity_id.name}".format(
				log=activity_log
			)
			result.append((activity_log.id, name))
		return result
	
	def create(self, cr, uid, vals, context=None):
		self._check_point(cr, uid, [], vals, context)
		result = super(tbvip_additional_activity_log, self).create(cr, uid, vals, context)
		self._create_employee_point(cr, uid, result, context)
		return result
	
	def write(self, cr, uid, ids, vals, context=None):
		self._check_point(cr, uid, ids, vals, context)
		result = super(tbvip_additional_activity_log, self).write(cr, uid, ids, vals, context)
		# self._edit_employee_point(cr, uid, ids, vals, context)
		return result
	
	def _check_point(self, cr, uid, ids, vals, context=None):
		if vals.get('point', False):
			if context.get('menu_from', False):
				if context['menu_from'] == 'extra' and vals['point'] < 0:
					raise osv.except_osv(_('Warning!'), _("Extra point should be positive."))
				if context['menu_from'] == 'penalty' and vals['point'] > 0:
					raise osv.except_osv(_('Warning!'), _("Extra point should be negative."))
	
	def _create_employee_point(self, cr, uid, additional_activity_log_id, context=None):
		"""
		Create new hr.point.employee.point based on newly created tbvip.additional.activity.log and update its
		employee_point_id
		:param additional_activity_log_id:
		"""
		employee_point_obj = self.pool.get('hr.point.employee.point')
		model_obj = self.pool.get('ir.model.data')
		reference = 'hr_point_type_xtra'
		if context.get('menu_from', False) and context['menu_from'] == 'penalty':
			reference = 'hr_point_type_penalty'
		model, point_type_id = model_obj.get_object_reference(cr, uid, 'tbvip_point_payroll', reference)
		additional_activity_log = self.browse(cr, uid, [additional_activity_log_id], context)
		employee_point_vals = {
			'event_date': additional_activity_log.activity_time,
			'employee_id': additional_activity_log.employee_id.id,
			'point_type_id': point_type_id,
			'point': additional_activity_log.point,
			# 'reference_model': self._name,
			# 'reference_id': additional_activity_log_id,
		}
		new_employee_point_id = employee_point_obj.create(cr, uid, employee_point_vals, context)
		# Update employee_point_id
		return self.write(cr, uid, [additional_activity_log_id], {'employee_point_id': new_employee_point_id})
	
	# commented, cannot edit employee point
	# def _edit_employee_point(self, cr, uid, ids, vals, context=None):
	# 	"""
	# 	Edit previous hr_point_employee_point based on newly created tbvip_additional_activity_log and update its point
	# 	:param ids of edited tbvip_additional_activity_log
	# 	:param vals of edited tbvip_additional_activity_log
	# 	"""
	# 	if vals.get('point', False):
	# 		employee_point_obj = self.pool.get('hr.point.employee.point')
	# 		employee_point_ids = employee_point_obj.search(cr, uid, [
	# 			# ('reference_model', '=', self._name),
	# 			# ('reference_id', 'in', ids)
	# 		], context=context)
	# 		return employee_point_obj.write(cr, uid, employee_point_ids, {
	# 			'point': vals['point']
	# 		}, context=context)
		
		
# ===========================================================================================================================
