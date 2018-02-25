from openerp.osv import osv
from datetime import datetime, timedelta, date
from openerp import SUPERUSER_ID
import pytz
from openerp.tools.translate import _


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

class hr_point_employee_point(osv.Model):
	_inherit = 'hr.point.employee.point'
	
	def cron_generate_top_point(self, cr, uid, context={}):
		branch_obj = self.pool.get('tbvip.branch')
		employee_obj = self.pool.get('hr.employee')
		point_type_obj = self.pool.get('hr.point.type')
		employee_points = {}
		
		# Calculate today's points ( today = day_end_date )
		for branch_id in branch_obj.search(cr, uid, [], context=context):
			branch_employee_ids = employee_obj.get_employee_id_from_branch(cr, uid, branch_id, context=context)
			total_branch_point = 0
			for branch_employee_id in branch_employee_ids:
				employee_points[branch_employee_id] = 0
				# get employee points for today
				today_employee_point_ids = self.search(cr, uid, [
					('event_date', '>=', datetime.now().strftime("%Y-%m-%d 00:00:00")),
					('event_date', '<=', datetime.now().strftime("%Y-%m-%d 23:59:59")),
					('employee_id', '=', branch_employee_id)
				], context=context)
				today_employee_points = self.browse(cr, uid, today_employee_point_ids, context=context)
				for today_employee_point in today_employee_points:
					employee_points[branch_employee_id] += today_employee_point.point # add to employee points
					total_branch_point += today_employee_point.point # add to total
			if total_branch_point > 0:
				# if total branch point positive, calculate
				for branch_employee_id in branch_employee_ids:
					employee_points[branch_employee_id] = employee_points[branch_employee_id] / total_branch_point
			else:
				# if total branch point is zero or negative, no one gets anything
				for branch_employee_id in branch_employee_ids:
					employee_points[branch_employee_id] = 0
		
		# Search employee with the highest point from all branches
		top_employee_id = 0
		current_highest_point = 0
		for employee_id in employee_points:
			if employee_points[employee_id] > current_highest_point:
				current_highest_point = employee_points[employee_id]
				top_employee_id = employee_id
		
		# Input point TOP today if highest point of employee is not zero
		if current_highest_point > 0:
			point_type_ids = point_type_obj.search(cr, uid, [
				('name', '=', 'POIN_TOP')
			], limit=1, context=context)
			if point_type_ids and len(point_type_ids) == 1:
				employee_point_vals = {
					'event_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
					'employee_id': top_employee_id,
					'point_type_id': point_type_ids[0],
					'point': 1,
					'reference': 'CRON - Generate Top Point',
				}
				new_id = self.create(cr, uid, employee_point_vals, context)
	
	def cron_overtime_and_late_attendance_point(self, cr, uid, context={}):

	# versi juned, 20180212

		employee_obj = self.pool.get('hr.employee')
		payslip_obj = self.pool.get('hr.payslip')
		attendance_config_settings_obj = self.pool.get('attendance.config.settings')
		attendance_obj = self.pool.get('hr.attendance')

		#date_now = datetime.now() careful, debugging only
		date_now = datetime.now().replace(hour=0, minute=0, second=0)
		date_from = date_now - timedelta(hours=7)
		date_from = date_from.strftime("%Y-%m-%d")
		date_to = date_now + timedelta(hours=24) - timedelta(hours=7) - timedelta(seconds=1)
		date_to = date_to.strftime("%Y-%m-%d")

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
			print employee.name
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
					'late_leave': 0,
					})
			# convert sign in hour/minute/second into minutes, rounding the second
				sign_in_minutes = attendance_by_date[day]['sign_in'].hour * 60 + attendance_by_date[day]['sign_in'].minute
				if attendance_by_date[day]['sign_in'].second >= 30: sign_in_minutes += 1
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
					if attendance_by_date[day]['sign_out'].second >= 30: sign_out_minutes += 1
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

			"""
			for day in attendance_by_date:
				print day
				print "in: %s - out: %s" % (attendance_by_date[day]['sign_in'],attendance_by_date[day]['sign_out'])
				print "start late: %s - start early: %s" % (attendance_by_date[day]['late_start'],attendance_by_date[day]['early_start'])
				print "finish early: %s - finish overtime: %s" % (attendance_by_date[day]['early_leave'],attendance_by_date[day]['overtime_leave'])
				print "=================================================================="
			"""

			for day in attendance_by_date:
				data = attendance_by_date[day]
				attendance_obj.late_attendance(cr, uid, [employee.id],
					data['late_start'] + data['early_leave'], day, context=context)
				attendance_obj.overtime_attendance(cr, uid, [employee.id],
					data['early_start'] + data['overtime_leave'], day, context=context)


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