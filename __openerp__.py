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
		"base", "hr_point_payroll"
	],
	'sequence': 150,
	'data': [
		'menu/tbvip_point_payroll_menu.xml',
		'views/tbvip_point_payroll.xml',
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
