from openerp.osv import osv, fields

# ==========================================================================================================================

class koreksi_bon(osv.osv_memory):
	_inherit = 'koreksi.bon'
	
	def action_save_koreksi_bon(self, cr, uid, ids, context=None):
		result = super(koreksi_bon, self).action_save_koreksi_bon(cr, uid, ids, context=context)
		employee_point_obj = self.pool.get('hr.point.employee.point')
		employee_obj = self.pool.get('hr.employee')
		for kb in self.browse(cr, uid, ids):
			# input points
			employee_point_obj.input_point(cr, uid,
				event_date = kb.create_date,
				activity_code='KOREKSI_BON',
				roles={
					'ADM': [employee_obj.get_employee_id_from_user(cr, uid, uid, context=context)],
				},
				required_parameters={
				},
				reference='Koreksi Bon - {}'.format(kb.id),
				context=context)
		return result
