# See the file LICENSE for redistribution information.
#
# Copyright (c) 2008 WiredTiger Software.
#	All rights reserved.
#
# $Id$
#
# Auto-generate everything we can:
#	flag values
#	getter/setter code
#	manual page headers
#	structure method fields
#
# The api file is a python script that loads two dictionaries: "methods" and
# "flags".
#
# The "methods" dictionary is a set of API class objects, keyed by the
# method name.   The fields are:
#	1: the method name
#		 'handle' + '.' + 'method'
#	2: a string of comma-separated configuration key words
#		colonly	 -- column databases only
#		extfunc  -- call an external function to do the work
#		getter	 -- getter method
#		ienvlock -- locks the IENV mutex (implied by getter/setter)
#		method	 -- method returns an int
#		methodV  -- method returns void
#		noauto	 -- don't auto-generate a stub at all
#		rdonly	 -- not allowed if the database is read-only
#		restart	 -- handle WT_RESTART in the API call
#		rowonly	 -- row databases only
#		setter	 -- setter method
#		toc	 -- function takes a WT_TOC/DB argument pair
#		verify	 -- setter methods call validation function
#	3: a list of argument and name/declaration pairs
#		An argument to the method.  In an argument declaration, "@S"
#		is replaced by the argument name when needed (sometimes we.
#		need the name in a declaration, and sometimes we don't).
#	4: a list of flags, if any.
#		If there's a flags variable, but the method doesn't currently
#		take any flags, enter '__NONE__'.
#	5: a list of on-transitions, if any
#	6: a list of off-transitions, if any

flags = {}
methods = {}

class Api:
	def __init__(self, key, config, args, f, on, off):
		self.key = key
		self.handle = key.split('.')[0]
		self.method = key.split('.')[1]
		self.config = config
		self.args = args
		if f:
			flags[key] = f
		self.on = on
		self.off = off

###################################################
# WT_TOC method declarations
###################################################
methods['wt_toc.close'] = Api(
	'wt_toc.close',
	'method, ienvlock',
	['flags/u_int32_t @S'],
	['__NONE__'],
	['init'], [])

###################################################
# ENV method declarations
###################################################
methods['env.cache_hash_size_get'] = Api(
	'env.cache_hash_size_get',
	'method, getter',
	['cache_hash_size/u_int32_t *@S'],
	[],
	['init'], [])
methods['env.cache_hash_size_set'] = Api(
	'env.cache_hash_size_set',
	'method, setter, verify',
	['cache_hash_size/u_int32_t @S'],
	[],
	['init'], [])

methods['env.cache_size_get'] = Api(
	'env.cache_size_get',
	'method, getter',
	['cache_size/u_int32_t *@S'],
	[],
	['init'], [])
methods['env.cache_size_set'] = Api(
	'env.cache_size_set',
	'method, setter, verify',
	['cache_size/u_int32_t @S'],
	[],
	['init'], ['open'])

methods['env.close'] = Api(
	'env.close',
	'method',
	['flags/u_int32_t @S'],
	['__NONE__'],
	['init'], [])

methods['env.db'] = Api(
	'env.db',
	'method',
	['flags/u_int32_t @S',
	 'dbp/DB **@S'],
	['__NONE__'],
	['open'], [])

methods['env.err'] = Api(
	'env.err',
	'methodV, noauto',
	['err/int @S',
	 'fmt/const char *@S, ...'],
	[],
	['init'], [])

methods['env.errcall_get'] = Api(
	'env.errcall_get',
	'method, getter',
	['errcall/void (**@S)(const ENV *, const char *)'],
	[],
	['init'], [])
methods['env.errcall_set'] = Api(
	'env.errcall_set',
	'method, setter',
	['errcall/void (*@S)(const ENV *, const char *)'],
	[],
	['init'], [])

methods['env.errfile_get'] = Api(
	'env.errfile_get',
	'method, getter',
	['errfile/FILE **@S'],
	[],
	['init'], [])
methods['env.errfile_set'] = Api(
	'env.errfile_set',
	'method, setter',
	['errfile/FILE *@S'],
	[],
	['init'], [])

methods['env.errpfx_get'] = Api(
	'env.errpfx_get',
	'method, getter',
	['errpfx/const char **@S'],
	[],
	['init'], [])
methods['env.errpfx_set'] = Api(
	'env.errpfx_set',
	'method, setter',
	['errpfx/const char *@S'],
	[],
	['init'], [])

methods['env.errx'] = Api(
	'env.errx',
	'methodV, noauto',
	['fmt/const char *@S, ...'],
	[],
	['init'], [])

methods['env.hazard_size_get'] = Api(
	'env.hazard_size_get',
	'method, getter',
	['hazard_size/u_int32_t *@S'],
	[],
	['init'], [])
methods['env.hazard_size_set'] = Api(
	'env.hazard_size_set',
	'method, setter, verify',
	['hazard_size/u_int32_t @S'],
	[],
	['init'], ['open'])

methods['env.msgcall_get'] = Api(
	'env.msgcall_get',
	'method, getter',
	['msgcall/void (**@S)(const ENV *, const char *)'],
	[],
	['init'], [])
methods['env.msgcall_set'] = Api(
	'env.msgcall_set',
	'method, setter',
	['msgcall/void (*@S)(const ENV *, const char *)'],
	[],
	['init'], [])

methods['env.msgfile_get'] = Api(
	'env.msgfile_get',
	'method, getter',
	['msgfile/FILE **@S'],
	[],
	['init'], [])
methods['env.msgfile_set'] = Api(
	'env.msgfile_set',
	'method, setter',
	['msgfile/FILE *@S'],
	[],
	['init'], [])

methods['env.open'] = Api(
	'env.open',
	'method',
	['home/const char *@S',
	 'mode/mode_t @S',
	 'flags/u_int32_t @S'],
	['__NONE__'],
	['init'], ['open'])

methods['env.stat_clear'] = Api(
	'env.stat_clear',
	'method',
	['flags/u_int32_t @S'],
	['__NONE__'],
	['init'], [])

methods['env.stat_print'] = Api(
	'env.stat_print',
	'method',
	['stream/FILE *@S',
	 'flags/u_int32_t @S'],
	['__NONE__'],
	['init'], [])

methods['env.sync'] = Api(
	'env.sync',
	'method',
	['progress/void (*@S)(const char *, u_int64_t)',
	 'flags/u_int32_t @S'],
	['__NONE__'],
	['open'], [])

methods['env.toc'] = Api(
	'env.toc',
	'method, ienvlock',
	['flags/u_int32_t @S',
	 'tocp/WT_TOC **@S'],
	['__NONE__'],
	['open'], [])

methods['env.toc_size_get'] = Api(
	'env.toc_size_get',
	'method, getter',
	['toc_size/u_int32_t *@S'],
	[],
	['init'], [])
methods['env.toc_size_set'] = Api(
	'env.toc_size_set',
	'method, setter, verify',
	['toc_size/u_int32_t @S'],
	[],
	['init'], ['open'])

methods['env.verbose_get'] = Api(
	'env.verbose_get',
	'method, getter',
	['verbose/u_int32_t *@S'],
	[],
	['init'], [])
methods['env.verbose_set'] = Api(
	'env.verbose_set',
	'method, setter, verify',
	['verbose/u_int32_t @S'],
	['VERB_ALL',
	 'VERB_CACHE',
	 'VERB_HAZARD',
	 'VERB_MUTEX',
	 'VERB_FILEOPS',
	 'VERB_SERVERS'],
	['init'], [])

###################################################
# Db standalone method declarations
###################################################
methods['db.btree_compare_get'] = Api(
	'db.btree_compare_get',
	'method, getter',
	['btree_compare/int (**@S)(DB *, const DBT *, const DBT *)'],
	[],
	['init'], [])
methods['db.btree_compare_set'] = Api(
	'db.btree_compare_set',
	'method, setter',
	['btree_compare/int (*@S)(DB *, const DBT *, const DBT *)'],
	[],
	['init'], ['open'])

methods['db.btree_compare_dup_get'] = Api(
	'db.btree_compare_dup_get',
	'method, getter',
	['btree_compare_dup/int (**@S)(DB *, const DBT *, const DBT *)'],
	[],
	['init'], [])
methods['db.btree_compare_dup_set'] = Api(
	'db.btree_compare_dup_set',
	'method, setter',
	['btree_compare_dup/int (*@S)(DB *, const DBT *, const DBT *)'],
	[],
	['init'], ['open'])

methods['db.btree_compare_int_get'] = Api(
	'db.btree_compare_int_get',
	'method, getter',
	['btree_compare_int/int *@S'],
	[],
	['init'], [])
methods['db.btree_compare_int_set'] = Api(
	'db.btree_compare_int_set',
	'method, setter, verify',
	['btree_compare_int/int @S'],
	[],
	['init'], ['open'])

methods['db.btree_dup_offpage_get'] = Api(
	'db.btree_dup_offpage_get',
	'method, getter',
	['btree_dup_offpage/u_int32_t *@S'],
	[],
	['init'], [])
methods['db.btree_dup_offpage_set'] = Api(
	'db.btree_dup_offpage_set',
	'method, setter, verify',
	['btree_dup_offpage/u_int32_t @S'],
	[],
	['init'], ['open'])

methods['db.btree_itemsize_get'] = Api(
	'db.btree_itemsize_get',
	'method, getter',
	['intlitemsize/u_int32_t *@S',
	 'leafitemsize/u_int32_t *@S'],
	[],
	['init'], [])
methods['db.btree_itemsize_set'] = Api(
	'db.btree_itemsize_set',
	'method, setter',
	['intlitemsize/u_int32_t @S',
	 'leafitemsize/u_int32_t @S'],
	[],
	['init'], ['open'])

methods['db.btree_pagesize_get'] = Api(
	'db.btree_pagesize_get',
	'method, getter',
	['allocsize/u_int32_t *@S',
	 'intlsize/u_int32_t *@S',
	 'leafsize/u_int32_t *@S',
	 'extsize/u_int32_t *@S'],
	[],
	['init'], [])
methods['db.btree_pagesize_set'] = Api(
	'db.btree_pagesize_set',
	'method, setter',
	['allocsize/u_int32_t @S',
	 'intlsize/u_int32_t @S',
	 'leafsize/u_int32_t @S',
	 'extsize/u_int32_t @S'],
	[],
	['init'], ['open'])

methods['db.bulk_load'] = Api(
	'db.bulk_load',
	'method, rdonly, toc',
	['flags/u_int32_t @S',
	 'progress/void (*@S)(const char *, u_int64_t)',
	 'cb/int (*@S)(DB *, DBT **, DBT **)'],
	[ 'DUPLICATES' ],
	['open'], [])

methods['db.close'] = Api(
	'db.close',
	'method, toc',
	['flags/u_int32_t @S'],
	['NOWRITE',
	 'OSWRITE'],
	['init'], [])

methods['db.col_del'] = Api(
	'db.col_del',
	'method, colonly, rdonly, restart, toc',
	['toc/WT_TOC *@S',
	 'recno/u_int64_t @S',
	 'flags/u_int32_t @S'],
	['__NONE__'],
	['open'], [])

methods['db.col_get'] = Api(
	'db.col_get',
	'method, colonly, toc',
	['toc/WT_TOC *@S',
	 'recno/u_int64_t @S',
	 'data/DBT *@S',
	 'flags/u_int32_t @S'],
	['__NONE__'],
	['open'], [])

methods['db.col_put'] = Api(
	'db.col_put',
	'method, colonly, rdonly, restart, toc',
	['toc/WT_TOC *@S',
	 'recno/u_int64_t *@S',
	 'data/DBT *@S',
	 'flags/u_int32_t @S'],
	['__NONE__'],
	['open'], [])

methods['db.column_set'] = Api(
	'db.column_set',
	'method, setter, verify',
	['fixed_len/u_int32_t @S',
	 'dictionary/const char *@S',
	 'flags/u_int32_t @S'],
	[ 'REPEAT_COMP' ],
	['init'], ['open'])

methods['db.dump'] = Api(
	'db.dump',
	'method, toc',
	['stream/FILE *@S',
	 'progress/void (*@S)(const char *, u_int64_t)',
	 'flags/u_int32_t @S'],
	['DEBUG',
	 'PRINTABLES' ],
	['open'], [])

methods['db.err'] = Api(
	'db.err',
	'methodV, noauto',
	['err/int @S',
	 'fmt/const char *@S, ...'],
	[],
	['init'], [])

methods['db.errcall_get'] = Api(
	'db.errcall_get',
	'method, getter',
	['errcall/void (**@S)(const DB *, const char *)'],
	[],
	['init'], [])
methods['db.errcall_set'] = Api(
	'db.errcall_set',
	'method, setter',
	['errcall/void (*@S)(const DB *, const char *)'],
	[],
	['init'], [])

methods['db.errfile_get'] = Api(
	'db.errfile_get',
	'method, getter',
	['errfile/FILE **@S'],
	[],
	['init'], [])
methods['db.errfile_set'] = Api(
	'db.errfile_set',
	'method, setter',
	['errfile/FILE *@S'],
	[],
	['init'], [])

methods['db.errpfx_get'] = Api(
	'db.errpfx_get',
	'method, getter',
	['errpfx/const char **@S'],
	[],
	['init'], [])
methods['db.errpfx_set'] = Api(
	'db.errpfx_set',
	'method, setter',
	['errpfx/const char *@S'],
	[],
	['init'], [])

methods['db.errx'] = Api(
	'db.errx',
	'methodV, noauto',
	['fmt/const char *@S, ...'],
	[],
	['init'], [])

methods['db.huffman_set'] = Api(
	'db.huffman_set',
	'method, extfunc, setter',
	['huffman_table/u_int8_t const *@S',
	 'huffman_table_size/u_int @S',
	 'huffman_flags/u_int32_t @S'],
	[ 'ASCII_ENGLISH', 'HUFFMAN_DATA', 'HUFFMAN_KEY', 'TELEPHONE' ],
	['init'], ['open'])

methods['db.open'] = Api(
	'db.open',
	'method, toc',
	['name/const char *@S',
	 'mode/mode_t @S',
	 'flags/u_int32_t @S'],
	[ 'CREATE', 'RDONLY' ],
	['init'], [])

methods['db.row_del'] = Api(
	'db.row_del',
	'method, rdonly, restart, rowonly, toc',
	['toc/WT_TOC *@S',
	 'key/DBT *@S',
	 'flags/u_int32_t @S'],
	['__NONE__'],
	['open'], [])

methods['db.row_get'] = Api(
	'db.row_get',
	'method, rowonly, toc',
	['toc/WT_TOC *@S',
	 'key/DBT *@S',
	 'data/DBT *@S',
	 'flags/u_int32_t @S'],
	['__NONE__'],
	['open'], [])

methods['db.row_put'] = Api(
	'db.row_put',
	'method, rdonly, restart, rowonly, toc',
	['toc/WT_TOC *@S',
	 'key/DBT *@S',
	 'data/DBT *@S',
	 'flags/u_int32_t @S'],
	['__NONE__'],
	['open'], [])

methods['db.stat_clear'] = Api(
	'db.stat_clear',
	'method',
	['flags/u_int32_t @S'],
	['__NONE__'],
	['open'], [])

methods['db.stat_print'] = Api(
	'db.stat_print',
	'method, toc',
	['stream/FILE *@S',
	 'flags/u_int32_t @S'],
	['__NONE__'],
	['open'], [])

methods['db.sync'] = Api(
	'db.sync',
	'method, rdonly, toc',
	['progress/void (*@S)(const char *, u_int64_t)',
	 'flags/u_int32_t @S'],
	['OSWRITE'],
	['open'], [])

methods['db.verify'] = Api(
	'db.verify',
	'method, toc',
	['progress/void (*@S)(const char *, u_int64_t)',
	 'flags/u_int32_t @S'],
	['__NONE__'],
	['open'], [])

###################################################
# External routine flag declarations
###################################################
flags['wiredtiger_env_init'] = [
	'MEMORY_CHECK' ]

###################################################
# Internal routine flag declarations
###################################################
flags['bt_search_key_row'] = [
	'INSERT' ]

###################################################
# Structure flag declarations
###################################################
flags['env'] = [
	'MEMORY_CHECK' ]
flags['idb'] = [
	'COLUMN',
	'RDONLY',
	'REPEAT_COMP' ]
flags['ienv'] = [
	'SERVER_RUN',
	'WORKQ_RUN' ]
flags['wt_page'] = [
	'DISCARD',
	'MODIFIED',
	'PINNED' ]
