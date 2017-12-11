from openerp.osv import osv


class hr_point_type(osv.Model):
	_inherit = 'hr.point.type'
	
	# OVERRIDES -----------------------------------------------------------------------------------------------------------------
	
	def _create_salary_rule(self, cr, uid, point_type_name, context=None):
		"""
		Adds if inputs.POIN_SALES_POINT.amount > 0 else 0 clause for every created salary rules' python codes of hr_point_type for TBVIP
		"""
		salary_rule_obj = self.pool.get('hr.salary.rule')
		result = super(hr_point_type, self)._create_salary_rule(cr, uid, point_type_name, context)
		salary = salary_rule_obj.browse(cr, uid, [result], context)
		salary.amount_python_compute = salary.amount_python_compute + ' if inputs.POIN_SALES_POINT.amount > 0 else 0'
		return result

	def action_reset_all_points(self, cr, uid, ids, context=None):
		employee_obj = self.pool.get('hr.employee')
		employee_level_obj = self.pool.get('hr.employee.level')
		employee_point_obj = self.pool.get('hr.point.employee.point')
		additional_activity_log_obj = self.pool.get('tbvip.additional.activity.log')
		
		# remove all additional activities
		all_additional_activity_ids = additional_activity_log_obj.search(cr, uid, [], context=context)
		additional_activity_log_obj.unlink(cr, uid, all_additional_activity_ids, context=context)
		
		# remove all point history
		all_employee_point_ids = employee_point_obj.search(cr, uid, [], context=context)
		employee_point_obj.unlink(cr, uid, all_employee_point_ids, context=context)
		
		# reset employee total point and level
		all_employee_ids = employee_obj.search(cr, uid, [], context=context)
		employee_obj.write(cr, uid, all_employee_ids, {
			'total_point': 0,
			'employee_level_id': employee_level_obj.get_employee_lowest_level_id(cr, uid, context=context),  # cannot use calculate_employee_level because level assignment only done if the new level is higher
		}, context=context)