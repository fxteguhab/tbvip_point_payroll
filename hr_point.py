from openerp.osv import osv, fields
from datetime import datetime, timedelta, date
from openerp import SUPERUSER_ID
import pytz
from openerp.tools.translate import _

# ==========================================================================================================================

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

# ==========================================================================================================================

class hr_point_top_log(osv.Model):
	_name = 'hr.point.top.log'
	_description = 'TOP Point log'

	_columns = {
		'employee_id': fields.many2one('hr.employee', 'Employee'),
		'branch_id': fields.related('employee_id', 'branch_id', type="char", string="Branch", store=True),
		'point': fields.integer('Point',group_operator="sum"), # mana tau kapan2 ada kemungkinan top point ngga cuman 1
	}

# ==========================================================================================================================

class hr_point_employee_point(osv.Model):
	_inherit = 'hr.point.employee.point'
	
	def _get_employee_data_basic(self, cr, uid, employee_id, context=None):
		result = super(hr_point_employee_point, self)._get_employee_data_basic(cr, uid, employee_id, context=context)
		employee_obj = self.pool.get('hr.employee')
		employee = employee_obj.browse(cr, uid, employee_id, context=context)
		result.update({'top_point': employee.top_point})
		return result

	def cron_generate_top_point(self, cr, uid, context={}):
		branch_obj = self.pool.get('tbvip.branch')
		employee_obj = self.pool.get('hr.employee')
		point_type_obj = self.pool.get('hr.point.type')
		top_point_log_obj = self.pool.get('hr.point.top.log')

	# cron diasumsikan berjalan di tengah malam. Misal dia jalan di tanggal 5 maret, 
	# maka dia menghitung TOP dari point2 di tanggal 4 maret
		today = (datetime.now() + timedelta(hours=7)).replace(hour=0, minute=0, second=0, microsecond=0)
	# debugging
		#today = datetime(2018,3,20,0,0,0)
		date_to = today - timedelta(seconds=1) - timedelta(hours=7) # perhitungkan timezone
		date_from = date_to - timedelta(hours=24)

	# hitung total point per employee dan akumulasi point per branch
		points_by_branch = {} # dikelompokkan per branch
		for branch_id in branch_obj.search(cr, uid, [], context=context):
			points_by_branch[branch_id] = {
				'total': 0,
				'employee_points': {},
			}
			branch_employee_ids = employee_obj.get_employee_id_from_branch(cr, uid, branch_id, context=context)
		# get yesterday's employee points
			point_log_ids = self.search(cr, uid, [
				('event_date', '>=', date_from.strftime("%Y-%m-%d %H:%M:%S")),
				('event_date', '<=', date_to.strftime("%Y-%m-%d %H:%M:%S")),
				('employee_id', 'in', branch_employee_ids)
			], context=context)
			for point_log in self.browse(cr, uid, point_log_ids, context=context):
				employee_id = point_log.employee_id.id
				point = point_log.point
				multiplier = point_log.point_type_id.name == 'POIN_PENALTY' and -1 or 1
			# update total point employee ybs
				if employee_id not in points_by_branch[branch_id]['employee_points']: 
					points_by_branch[branch_id]['employee_points'][employee_id] = 0
				points_by_branch[branch_id]['employee_points'][employee_id] += point * multiplier
			# update total point branch ini. hanya totalkan dari point yang positif/menambahkan
				if multiplier > 0:
					points_by_branch[branch_id]['total'] += point

		"""
		for branch_id in points_by_branch:
			print "ID cabang: %s" % branch_id
			print "Total poin di cabang: %s" % points_by_branch[branch_id]['total']
			print "Total point per employee:"
			for employee_id in points_by_branch[branch_id]['employee_points']:
				print "Employee %s: %s" % (employee_id, points_by_branch[branch_id]['employee_points'][employee_id])
			print "================================"
		"""

	# hitung siapa yang dapet paling tinggi di semua cabang
	# total point seorang employee dibandingkan dengan total PER CABANG di hari kemarin
	# lalu dicari yang paling tinggi siapa
		ratio_by_employee = {}
		for branch_id in points_by_branch:
			total_branch = points_by_branch[branch_id]['total']
			if total_branch == 0: continue # ini artinya tidak ada satupun yang berkontribusi point ke cabang itu
			for employee_id in points_by_branch[branch_id]['employee_points']:
				point = points_by_branch[branch_id]['employee_points'][employee_id]
				if point > 0:
					ratio_by_employee[employee_id] = float(point) / float(total_branch)
			# menghandle kemungkinan total point si employee hari ini negatif
			# kalau negatif, dianggap total point 0
				else:
					ratio_by_employee[employee_id] = 0
		highest_ratio = 0
		for employee_id in ratio_by_employee:
			#print "%s: %s" % (employee_id,ratio_by_employee[employee_id])
			if ratio_by_employee[employee_id] > highest_ratio:
				highest_ratio = ratio_by_employee[employee_id]

	# ok udah dapet ratio tertinggi. sekarang carilah seluruh employee dengan highest point ini
	# ini untuk mengantisipasi point tertinggi bisa dicapai oleh > 1 orang
	# hanya lakukan kalau ratio tertinggi > 0, untuk mengaitisipasi kasus super jarang yaitu
	# di hari itu semuanya point negatif sehingga total branch itu 0
		if highest_ratio > 0:
			highest_employee_ids = []
			for employee_id in ratio_by_employee:
				if str(highest_ratio) == str(ratio_by_employee[employee_id]):
					highest_employee_ids.append(employee_id)
		# update TOP point untuk employee dengan ratio tertinggi 
			for employee in employee_obj.browse(cr, uid, highest_employee_ids): 
				new_log_id = top_point_log_obj.create(cr, uid, {
					'employee_id': employee.id,
					'point': 1,
					})
				cr.execute("""
					UPDATE hr_point_top_log SET create_date='%s' 
					WHERE id=%s
					""" % (date_to.strftime("%Y-%m-%d %H:%M:%S"), new_log_id))
				employee_obj.write(cr, uid, [employee.id], {
					'top_point': employee.top_point + 1,
					})

	def cron_overtime_and_late_attendance_point(self, cr, uid, context={}):

	# versi juned, 20180212

		employee_obj = self.pool.get('hr.employee')
		payslip_obj = self.pool.get('hr.payslip')
		attendance_config_settings_obj = self.pool.get('attendance.config.settings')
		attendance_obj = self.pool.get('hr.attendance')

		date_now = (datetime.now() + timedelta(hours=7)).replace(hour=0, minute=0, second=0)
		date_from = date_now
		date_from = date_from.strftime("%Y-%m-%d")
		date_to = date_now + timedelta(hours=24)
		date_to = date_to.strftime("%Y-%m-%d")

		#debugging
		#date_from = date(2018,3,16).strftime("%Y-%m-%d")
		#date_to = date(2018,3,17).strftime("%Y-%m-%d")
	# get attendance settings
		start_tolerance_after, finish_tolerance_before, early_overtime_start, early_overtime_finish, late_overtime_start, late_overtime_finish = \
			attendance_config_settings_obj.get_attendance_setting(cr, uid, context=context)
		"""
		print start_tolerance_after
		print finish_tolerance_before
		print early_overtime_start
		print early_overtime_finish
		print late_overtime_start
		print late_overtime_finish
		"""
	# for each existing employee...
		employee_ids = employee_obj.search(cr, uid, [], context=context)
		for employee in employee_obj.browse(cr, uid, employee_ids, context=context):
		# get currently active contract
			contract_ids = payslip_obj.get_contract(cr, uid, employee, date_from, date_to, context=context)
		# no contract? pass this employee
			if not (contract_ids and len(contract_ids) > 0): continue
		# get the employee's attendance for this date
			contract_id = contract_ids[0]
			attendance_by_date = payslip_obj.get_attendance_by_date(cr, uid, employee.id, date_from, date_to, contract_id, context=context)
		# complete attendance_by_date with information about late and early
			for day in attendance_by_date:
			# no atteendance today? skip this employee
				if not attendance_by_date[day]['sign_in']: continue
				attendance_by_date[day].update({
					'early_start': 0,
					'late_start': 0,
					'early_leave': 0,
					'overtime_leave': 0,
					})
			# convert sign in hour/minute/second into minutes, rounding the second
				sign_in_minutes = attendance_by_date[day]['sign_in'].hour * 60 + attendance_by_date[day]['sign_in'].minute
				#if attendance_by_date[day]['sign_in'].second >= 30: sign_in_minutes += 1
			# how many minutes this employee is late for this day?
				start_with_tolerance = attendance_by_date[day]['start'] * 60 + start_tolerance_after
				late_start = max(0, sign_in_minutes - start_with_tolerance)
			# if late more than 30 minutes, no penalty but considered not full day
				if late_start > 30: late_start = 0 # sori guh si 30 sementara hardcode
				attendance_by_date[day]['late_start'] = int(late_start)
			# how many minutes this employee comes early?
				early_from = attendance_by_date[day]['start'] * 60 - early_overtime_start
				early_to = attendance_by_date[day]['start'] * 60 - early_overtime_finish
				early_start = 0
				if sign_in_minutes >= early_from and sign_in_minutes < early_to:
					early_start = early_to - sign_in_minutes
				elif sign_in_minutes < early_from:
					early_start = early_to - early_from
				attendance_by_date[day]['early_start'] = early_start
			# only if employee signs out
				if attendance_by_date[day]['sign_out']:
				# convert sign out hour/minute/second into minutes, rounding the second
					sign_out_minutes = attendance_by_date[day]['sign_out'].hour * 60 + attendance_by_date[day]['sign_out'].minute
					#if attendance_by_date[day]['sign_out'].second >= 30: sign_out_minutes += 1
				# how many minutes this employee leaves early?
					finish_with_tolerance = attendance_by_date[day]['finish'] * 60 - finish_tolerance_before
					early_leave = max(0, finish_with_tolerance - sign_out_minutes)
				# if early leave more than 30 minutes, no penalty but considered not full day
					if early_leave > 30: early_leave = 0 # sori guh si 30 sementara hardcode
					attendance_by_date[day]['early_leave'] = early_leave
				# how many minutes this employee stays late after store close?
					overtime_from = attendance_by_date[day]['finish'] * 60 + late_overtime_start
					overtime_to = attendance_by_date[day]['finish'] * 60 + late_overtime_finish
					overtime_leave = 0
					if sign_out_minutes > overtime_from and sign_out_minutes <= overtime_to:
						overtime_leave = sign_out_minutes - overtime_from
					elif sign_out_minutes > overtime_to:
						overtime_leave = overtime_to - overtime_from
					attendance_by_date[day]['overtime_leave'] = overtime_leave

			for day in attendance_by_date:
				print day
				print "in: %s - out: %s" % (attendance_by_date[day]['sign_in'],attendance_by_date[day]['sign_out'])
				print "start late: %s - start early: %s" % (attendance_by_date[day]['late_start'],attendance_by_date[day]['early_start'])
				print "finish early: %s - finish overtime: %s" % (attendance_by_date[day]['early_leave'],attendance_by_date[day]['overtime_leave'])
				print "=================================================================="

			for day in attendance_by_date:
				data = attendance_by_date[day]
				attendance_obj.late_attendance(cr, uid, [employee.id],
					data['late_start'] + data['early_leave'], day, context=context)
				attendance_obj.overtime_attendance(cr, uid, [employee.id],
					data['early_start'] + data['overtime_leave'], day, context=context)

		#raise osv.except_osv('test','test')

		"""
		yang di bawah ini adalah versi nibble as of 20180212
		attendance_obj = self.pool.get('hr.attendance')
		employee_obj = self.pool.get('hr.employee')
		contract_obj = self.pool.get('hr.contract')
		hr_payslip_obj = self.pool.get('hr.payslip')
		exception_working_hour_obj = self.pool.get('exception.working.hour')
		attendance_config_settings_obj = self.pool.get('attendance.config.settings')
		
		# adjusting to timezone
		if context and context.get('tz', False):
			tz = context['tz']
		else:
			user_pool = self.pool.get('res.users')
			user = user_pool.browse(cr, SUPERUSER_ID, uid)
			tz = (pytz.timezone(user.partner_id.tz)).zone if user.partner_id.tz else pytz.utc.zone
		
		#datetime_now = datetime.now() careful, debugging only
		datetime_now = datetime.strptime('2018-02-20 01:01:01','%Y-%m-%d %H:%M:%S')
		now_from = datetime_now.strftime('%Y-%m-%d 00:00:00')
		now_to = datetime_now.strftime('%Y-%m-%d 23:59:59')

		employee_ids = employee_obj.search(cr, uid, [], context=context)
		for employee in employee_obj.browse(cr, uid, employee_ids, context=context):
			contract_ids = hr_payslip_obj.get_contract(cr, uid, employee, now_from, now_to, context=context)
			if contract_ids and len(contract_ids) > 0:
				contract_id = contract_ids[0]
			else:
				continue
				
			# get attendances
			working_hours = contract_obj.browse(cr, uid, contract_id).working_hours
			attendances = attendance_obj.search(cr, uid, [
				('employee_id', '=', employee.id),
				('name', '>=', now_from),
				('name', '<=', now_to),
			], order='name ASC')
			
			# get attendance settings
			start_tolerance_after, finish_tolerance_before, early_overtime_start, early_overtime_finish, late_overtime_start, late_overtime_finish = \
				attendance_config_settings_obj.get_attendance_setting(cr, uid, context)
			tolerable_opening_datetime = False
			tolerable_closing_datetime = False
			early_overtime_init = False
			early_overtime_end = False
			late_overtime_init = False
			late_overtime_end = False
			
			list_of_day = []
			# total counter all time
			total_early_overtime = 0
			total_late_overtime = 0
			total_early_late = 0
			total_late_late = 0
			first_sign_in_of_the_date = False
			last_sign_out_of_the_date = False
			
			for attendance in attendance_obj.browse(cr, uid, attendances):
				attendance_date = datetime.strptime(attendance.name, '%Y-%m-%d %H:%M:%S')
				attendance_date = pytz.utc.localize(attendance_date, is_dst=None).astimezone(pytz.timezone(tz))
				attendance_date = datetime.strptime(attendance_date.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
				
				# set variables
				hour_from = False
				minute_from = False
				hour_to = False
				minute_to = False
				
				# search for custom working hour from Branch Working Hours if any
				custom_exception_working_hour_ids = exception_working_hour_obj.get_working_hour_ids(
					cr, uid, attendance_date.strftime('%Y-%m-%d %H:%M:%S'), limit=1, context=context)
				# if there's custom working hour
				if custom_exception_working_hour_ids and len(custom_exception_working_hour_ids) > 0:
					exception_working_hour = exception_working_hour_obj.browse(cr, uid, custom_exception_working_hour_ids[0], context=context)
					hour_from = int(exception_working_hour.open_hour)
					minute_from = (exception_working_hour.open_hour-hour_from) * 60
					hour_to = int(exception_working_hour.closed_hour)
					minute_to = (exception_working_hour.closed_hour-hour_from) * 60
				# if no custom
				else:
					# search working hour for attendance day_of_week
					day_of_week = int(attendance_date.strftime("%w"))-1
					for working_hour in working_hours.attendance_ids:
						if int(working_hour.dayofweek) == day_of_week:
							hour_from = int(working_hour.hour_from)
							minute_from = (working_hour.hour_from-hour_from) * 60
							hour_to = int(working_hour.hour_to)
							minute_to = (working_hour.hour_to-hour_to) * 60
							break
				if hour_from is not False and minute_from is not False and hour_to is not False and minute_to is not False:
					# if the attendance is signing in
					if attendance.action == 'sign_in':
						# sign in and out can be done more than once in a day, so check whether the day has been counted before
						in_date = attendance_date.strftime('%Y-%m-%d')
						if in_date not in list_of_day:
							# overtime and late
							cur_total_early_overtime, cur_total_late_overtime, cur_total_early_late, cur_total_late_late = \
								hr_payslip_obj.get_late_and_overtime(first_sign_in_of_the_date, last_sign_out_of_the_date,
									tolerable_opening_datetime, tolerable_closing_datetime, early_overtime_init,
									early_overtime_end, late_overtime_init, late_overtime_end, context=context)
							total_early_overtime += cur_total_early_overtime
							total_late_overtime += cur_total_late_overtime
							total_early_late += cur_total_early_late
							total_late_late += cur_total_late_late
							if first_sign_in_of_the_date and last_sign_out_of_the_date:
								pass
								# not gonna happen like in _get_worked_days_inject_data method,
								# because the range datetime is only for today
							
							# PROCESS NEW DATE
							list_of_day.append(in_date)
							first_sign_in_of_the_date = attendance_date
							last_sign_out_of_the_date = False
							
							# Get opening, closing, overtime datetime rules
							# new datetimes
							datetime_from = datetime(year=attendance_date.year, month=attendance_date.month, day=attendance_date.day,
								hour=int(hour_from), minute=int(minute_from))
							datetime_to = datetime(year=attendance_date.year, month=attendance_date.month, day=attendance_date.day,
								hour=int(hour_to), minute=int(minute_to))
							tolerable_opening_datetime = datetime_from + timedelta(minutes=start_tolerance_after)
							tolerable_closing_datetime = datetime_to + timedelta(minutes=-finish_tolerance_before)
							early_overtime_init = datetime_from + timedelta(minutes=-early_overtime_start)
							early_overtime_end = datetime_from + timedelta(minutes=-early_overtime_finish)
							late_overtime_init = datetime_to + timedelta(minutes=late_overtime_start)
							late_overtime_end = datetime_to + timedelta(minutes=late_overtime_finish)
					# if the attendance is signing out
					elif attendance.action == 'sign_out':
						last_sign_out_of_the_date = attendance_date
			# last date not calculated yet
			cur_total_early_overtime, cur_total_late_overtime, cur_total_early_late, cur_total_late_late = \
				hr_payslip_obj.get_late_and_overtime(first_sign_in_of_the_date, last_sign_out_of_the_date,
					tolerable_opening_datetime, tolerable_closing_datetime, early_overtime_init,
					early_overtime_end, late_overtime_init, late_overtime_end, context=context)
			total_early_overtime += cur_total_early_overtime
			total_late_overtime += cur_total_late_overtime
			total_early_late += cur_total_early_late
			total_late_late += cur_total_late_late
			if first_sign_in_of_the_date and last_sign_out_of_the_date:
				date_obj = {
					'date': first_sign_in_of_the_date.strftime('%Y-%m-%d'),
					'early_overtime': cur_total_early_overtime,
					'late_overtime': cur_total_late_overtime,
					'late': cur_total_early_late,
					'early_leave': cur_total_late_late,
				}
				attendance_obj.late_attendance(cr, uid, [employee.id],
					date_obj['late'] + date_obj['early_leave'], date_obj['date'], context=context)
				attendance_obj.overtime_attendance(cr, uid, [employee.id],
					date_obj['early_overtime'] + date_obj['late_overtime'], date_obj['date'], context=context)
		"""

# ==========================================================================================================================

class hr_point_top_reset_log(osv.osv):

	_name = 'hr.point.top.reset.log'
	_description = 'TOP Point reset log'

	_columns = {
		'create_date': fields.datetime('Reset Date'),
		'line_ids': fields.one2many('hr.point.top.reset.log.line', 'header_id', 'Reset Employees'),
	}

	_defaults = {
		'create_date': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
	}

	def create(self, cr, uid, vals, context={}):
	# reset seluruh top_point employee menjadi 0
	# sebelumnya, masukkan dulu ke line supaya ada historinya
		log_line = []
		employee_obj = self.pool.get('hr.employee')
		employee_ids = employee_obj.search(cr, uid, [])
		for employee in employee_obj.browse(cr, uid, employee_ids):
		# hanya masukkan ke log line employee yang ada top pointnya
			if employee.top_point > 0:
				log_line.append([0,False,{
					'employee_id': employee.id,
					'top_reset': employee.top_point,
					}])
		if len(log_line) > 0:
			vals.update({'line_ids': log_line})
	# reset point employeenya
		employee_obj.write(cr, uid, employee_ids, {
			'top_point': 0,
			})
	# baru masukkan record seperti biasa
		return super(hr_point_top_reset_log, self).create(cr, uid, vals, context=context)

# ==========================================================================================================================

class hr_point_top_reset_log_line(osv.osv):

	_name = 'hr.point.top.reset.log.line'
	_description = 'TOP Point reset log line'

	_columns = {
		'header_id': fields.many2one('hr.point.top.reset.log', 'Header'),
		'employee_id': fields.many2one('hr.employee', 'Employee', readonly=True),
		'top_reset': fields.float('TOP Point on Reset', readonly=True),
	}

