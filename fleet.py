from openerp.osv import osv, fields

_VEHICLE_TYPE = [
	('car', 'Car'),
	('bike', 'Bike'),
]

# ===========================================================================================================================

class fleet_vehicle(osv.osv):
	_inherit = 'fleet.vehicle'

	# COLUMNS ---------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'vehicle_type': fields.selection(_VEHICLE_TYPE, 'Vehicle Type'),
		'is_self_own': fields.boolean('Self own?', help='True if this vehicle is owned by Driver 1'),
	}

	_defaults = {
		'vehicle_type': 'car',
	}
	

# ===========================================================================================================================
