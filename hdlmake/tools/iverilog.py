#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2015 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Multi-tool support by Javier D. Garcia-Lasheras (javier@garcialasheras.com)
#
# This file is part of Hdlmake.
#
# Hdlmake is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hdlmake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hdlmake.  If not, see <http://www.gnu.org/licenses/>.
#

"""Module providing support for IVerilog (Icarus Verilog) simulator"""

from __future__ import absolute_import
import string

from .make_sim import ToolSim
from hdlmake.srcfile import VerilogFile, VHDLFile, SVFile


class ToolIVerilog(ToolSim):

    """Class providing the interface for Icarus Verilog simulator"""

    TOOL_INFO = {
        'name': 'Icarus Verilog',
        'id': 'iverilog',
        'windows_bin': 'iverilog',
        'linux_bin': 'iverilog'}

    STANDARD_LIBS = ['std', 'ieee', 'ieee_proposed', 'vl', 'synopsys']

    HDL_FILES = {VerilogFile: '', VHDLFile: '', SVFile: ''}

    CLEAN_TARGETS = {'clean': ["run.command", "ivl_vhdl_work", "work"],
                     'mrproper': ["*.vcd", "*.vvp"]}

    SIMULATOR_CONTROLS = {'vlog': 'echo $< >> run.command',
                          'vhdl': 'echo $< >> run.command',
                          'compiler': 'iverilog $(IVERILOG_OPT) '
                                      '-s $(TOP_MODULE) '
                                      '-o $(TOP_MODULE).vvp '
                                      '-c run.command'}

    def __init__(self):
        super(ToolIVerilog, self).__init__()
        self._tool_info.update(ToolIVerilog.TOOL_INFO)
        self._hdl_files.update(ToolIVerilog.HDL_FILES)
        self._standard_libs.extend(ToolIVerilog.STANDARD_LIBS)
        self._clean_targets.update(ToolIVerilog.CLEAN_TARGETS)
        self._simulator_controls.update(ToolIVerilog.SIMULATOR_CONTROLS)

    def makefile_sim_compilation(self):
        """Generate compile simulation Makefile target for IVerilog"""
        self.writeln("simulation: include_dirs $(VERILOG_OBJ) $(VHDL_OBJ)")
        self.writeln("\t\t" + self._simulator_controls['compiler'])
        self.writeln()
        self.writeln("include_dirs:")
        self.writeln("\t\techo \"# IVerilog command file,"
                     " generated by HDLMake\" > run.command")
        self.writeln()
        for inc in self.manifest_dict.get("include_dirs", []):
            self.writeln("\t\techo \"+incdir+" + inc + "\" >> run.command")
        self.writeln('\n')
        self.makefile_sim_dep_files()

    def makefile_sim_options(self):
        """Print the IVerilog options to the Makefile"""
        iverilog_opt = self.manifest_dict.get("iverilog_opt", '')
        iverilog_string = string.Template(
            """IVERILOG_OPT := ${iverilog_opt}\n""")
        self.writeln(iverilog_string.substitute(
            iverilog_opt=iverilog_opt))
