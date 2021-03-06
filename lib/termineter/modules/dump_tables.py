#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  termineter/modules/dump_tables.py
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following disclaimer
#    in the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of the project nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from __future__ import unicode_literals

import binascii
import os
import time

from c1218.errors import C1218ReadTableError
from c1219.data import C1219_TABLES
from termineter.module import TermineterModuleOptical

class Module(TermineterModuleOptical):
	def __init__(self, *args, **kwargs):
		TermineterModuleOptical.__init__(self, *args, **kwargs)
		self.author = ['Spencer McIntyre']
		self.description = 'Write Readable C12.19 Tables To A CSV File'
		self.detailed_description = 'This module will enumerate the readable tables on the smart meter and write them out to a CSV formated file for analysis. The format is table id, table name, table data length, table data.  The table data is represented in hex.'
		self.options.add_integer('LOWER', 'table id to start reading from', default=0)
		self.options.add_integer('UPPER', 'table id to stop reading from', default=256)
		self.options.add_string('FILE', 'file to write the csv data into', default='smart_meter_tables.csv')

	def run(self):
		conn = self.frmwk.serial_connection
		logger = self.logger
		lower_boundary = self.options['LOWER']
		upper_boundary = self.options['UPPER']
		out_file = open(self.options['FILE'], 'w', 1)

		number_of_tables = 0
		self.frmwk.print_status('Starting dump, writing table data to: ' + self.options['FILE'])
		for tableid in range(lower_boundary, (upper_boundary + 1)):
			try:
				data = conn.get_table_data(tableid)
			except C1218ReadTableError as error:
				data = None
				if error.code == 10:  # ISSS
					conn.stop()
					logger.warning('received ISSS error, connection stopped, will sleep before retrying')
					time.sleep(0.5)
					if not self.frmwk.serial_login():
						logger.warning('meter login failed, some tables may not be accessible')
					try:
						data = conn.get_table_data(tableid)
					except C1218ReadTableError as error:
						data = None
						if error.code == 10:
							raise error  # tried to re-sync communications but failed, you should reconnect and rerun the module
			if not data:
				continue
			tablename = C1219_TABLES.get(tableid, 'UNKNOWN')
			tableid = str(tableid)
			self.frmwk.print_status('Found readable table, ID: ' + tableid + ' Name: ' + tablename)
			# format is: table id, table name, table data length, table data
			out_file.write(','.join([tableid, tablename, str(len(data)), binascii.b2a_hex(data).decode('utf-8')]) + os.linesep)
			number_of_tables += 1

		out_file.close()
		self.frmwk.print_status('Successfully copied ' + str(number_of_tables) + ' tables to disk.')
