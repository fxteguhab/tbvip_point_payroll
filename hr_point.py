from openerp.osv import osv


class hr_point_type(osv.Model):
	_inherit = 'hr.point.type'
	
	# OVERRIDES -----------------------------------------------------------------------------------------------------------------
	
	def _create_salary_rule(self, cr, uid, point_type_name, context=None):
		"""
		Adds if inputs.SO_POINT > 0 else 0 clause for every created salary rules' python codes of hr_point_type for TBVIP
		"""
		salary_rule_obj = self.pool.get('hr.salary.rule')
		result = super(hr_point_type, self)._create_salary_rule(cr, uid, point_type_name, context)
		salary = salary_rule_obj.browse(cr, uid, [result], context)
		salary.amount_python_compute = salary.amount_python_compute + ' if inputs.SO_POINT > 0 else 0'
		return result