
"""Manipulates with the whole configuration.

Configuration consists of the whole data store copy and cluster state.

"""

# System imports
import os
import glob
import logging

# Local imports
import sync
import helpers
import data

_logger = logging.getLogger(__name__)

# Glob format of a data file
DATA_DIR_GLOB = '????????T??????.??????.json'
DATA_DIR_STRFTIME = '%Y%m%dT%H%M%S.%f.json'

# Path where we store configuration snapshots. None if undefined.
_data_dir = None


def _create_data_dir( data_dir):
	"""Creates the directory safely.
	"""
	try:
		os.makedirs( data_dir)
	except OSError as e:
		if e.errno == 17: # File already exists
			return True
		_logger.warn( 'Cannot create directory: %s: %s', data_dir, e)
		return False
	return True


def set_data_dir(data_dir):
	"""Sets and creates the data directory before start.
	"""
	global _data_dir
	_data_dir = data_dir

	if data_dir is None:
		return None

	if not _create_data_dir( data_dir):
		_data_dir = None
		return False

	return True



def save_configuration():
	global _data_dir

	# Don't write if there's no destination
	if _data_dir is None:
		return False

	snapshot = {}
	# Get a raw copy of all data
	snapshot[ 'copy'] = data.get_copy()
	# Get current system state
	snapshot[ 'cluster'] = sync.cluster_state.get_state()

	# Write this configuration
	file_name = _data_dir + '/' +helpers.now().strftime( DATA_DIR_STRFTIME)
	with open(file_name, 'w') as f:
		f.write( helpers.dump_json( snapshot))
	return True


def _load_from_content( content):
	# Content must contain data and state
	if not 'copy' in content or not 'cluster' in content:
		return False

	if data.push_data( content[ 'copy']):
		sync.cluster_state.update_state( content[ 'cluster'])
		return True
	return False


def _load_from_file( filename):
	try:
		with open( filename, 'r') as f:
			content = helpers.load_json( f.read())
	except (IOError, ValueError, KeyError) as e:
		_logger.warn( 'Cannot read file %s with json configuration %s', filename, e)
		return False

	return _load_from_content( content)


def load_configuration():
	"""Loads data from the newest file.

	Returns:
		Latest data or empty data if no suitable file was found.
	"""
	global _data_dir

	# Do not read file if there is no data path defined
	if _data_dir is None:
		return None

	dir_glob = _data_dir +'/' +DATA_DIR_GLOB
	_logger.debug( 'Data dir glob: %s', dir_glob)

	files = glob.glob( dir_glob)
	for filename in sorted( files, reverse=True):
		if _load_from_file( filename):
			return True

	_logger.warn('No configuration found')
	return False
