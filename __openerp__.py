{
	'name': 'TB VIP Point Payroll',
	'version': '0.1',
	'category': 'Sales Management',
	'description': """
		Custom implementation for Toko Besi VIP Bandung
	""",
	'author': 'Christyan Juniady and Associates',
	'maintainer': 'Christyan Juniady and Associates',
	'website': 'http://www.chjs.biz',
	'depends': [
		"base", "fleet", "hr_point_payroll", "tbvip"
	],
	'sequence': 150,
	'data': [
		'menu/tbvip_point_payroll_menu.xml',
		'views/fleet_view.xml',
		'views/tbvip_point_payroll.xml',
		'views/stock_opname_view.xml',
		'views/stock_view.xml',
		'views/hr_view.xml',
		'data/tbvip_point_payroll_data.xml',
	],
	'demo': [
	],
	'test': [
	],
	'installable': True,
	'auto_install': False,
	'qweb': [
	]
}
