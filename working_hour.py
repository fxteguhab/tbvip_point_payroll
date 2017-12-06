from openerp.osv import osv, fields

# ==========================================================================================================================

class exception_working_hour(osv.osv):
	_inherit = 'exception.working.hour'
	
	# COLUMNS ------------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'branch_id': fields.many2one('tbvip.branch', 'Branch', required=True),
	}
	
	# DEFAULTS --------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'branch_id': lambda self, cr, uid, *args: self.pool.get('res.users').browse(cr, uid, [uid]).branch_id,
	}
	
	# ONCHANGES --------------------------------------------------------------------------------------------------------------
	
	def onchange_branch_id(self, cr, uid, ids, branch_id, context=None):
		context = {} if context is None else context
		result_value = {}
		branch_obj = self.pool.get('tbvip.branch')
		
		branch = branch_obj.browse(cr, uid, [branch_id], context)
		result_value['open_hour'] = branch.default_open_hour
		result_value['closed_hour'] = branch.default_closed_hour
		
		return {'value': result_value}
	
	# OVERRIDES ------------------------------------------------------------------------------------------------------------------
	
	def name_get(self, cr, uid, ids, context=None):
		""" Notes: Not calling super.name_get so that it won't call self.browse two times """
		result = []
		for working_hour in self.browse(cr, uid, ids, context):
			open_hour, open_minute = divmod(working_hour.open_hour * 60, 60)
			closed_hour, closed_minute = divmod(working_hour.closed_hour * 60, 60)
			name = "{wh.branch_id.name} | {wh.date} -> {0:02.0f}:{1:02.0f}-{2:02.0f}:{3:02.0f}".format(
				open_hour, open_minute, closed_hour, closed_minute, wh=working_hour,
			)
			result.append((working_hour.id, name))
		return result
	
	def get_working_hour_ids(self, cr, uid, date, limit=None, context=None):
		""" Attention! You have to put branch_id as parameter in the context if you want to use it """
		if context.get('branch_id', False):
			return self.search(cr, uid, [
				('branch_id', '=', context['branch_id']),
				('date', '=', date)
			], limit=limit, context=context)
		else:
			super(exception_working_hour, self).get_working_hour_ids(cr, uid, date, limit, context)
