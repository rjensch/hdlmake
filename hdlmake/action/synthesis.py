#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, 2014 CERN
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

"""This module provides the synthesis functionality to HDLMake"""

from __future__ import print_function
import logging
import sys
import os

from hdlmake.srcfile import SourceFileFactory
from hdlmake.util import path

from hdlmake.tools import (
    ToolISE, ToolPlanAhead, ToolVivado,
    ToolQuartus, ToolDiamond, ToolLibero)

from .action import Action

class ActionSynthesis(Action,
    ToolISE, ToolPlanAhead, ToolVivado,
    ToolQuartus, ToolDiamond, ToolLibero):
    """Class providing the public synthesis methods for the user"""

    def __init__(self, *args):
        Action.__init__(self, *args)
        ToolISE.__init__(self, *args)
        ToolPlanAhead.__init__(self, *args)
        ToolVivado.__init__(self, *args)
        ToolQuartus.__init__(self, *args)
        ToolDiamond.__init__(self, *args)
        ToolLibero.__init__(self, *args)

    def _load_synthesis_tool(self):
        """Returns a tool_object that provides the synthesis tool interface"""
        tool_name = self.get_top_module().manifest_dict["syn_tool"]
        if tool_name is "ise":
            tool_object = ToolISE()
        elif tool_name is "planahead":
            tool_object = ToolPlanAhead()
        elif tool_name is "vivado":
            tool_object = ToolVivado()
        elif tool_name is "quartus":
            tool_object = ToolQuartus()
        elif tool_name is "diamond":
            tool_object = ToolDiamond()
        elif tool_name is "libero":
            tool_object = ToolLibero()
        else:
            logging.error("Synthesis tool not recognized: %s", tool_name)
        return tool_object


    def _check_synthesis_makefile(self):
        """Check the manifest contains all the keys for a synthesis makefile"""
        # NOTE: top_module is not used in synthesis!!
        if not self.get_top_module().manifest_dict["syn_top"]:
            logging.error("syn_top variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not self.get_top_module().manifest_dict["syn_tool"]:
            logging.error("syn_tool variable must be set in the top manifest.")
            sys.exit("Exiting")


    def synthesis_makefile(self):
        """Generate a synthesis Makefile for the selected tool"""
        self._check_all_fetched_or_quit()
        self._check_synthesis_makefile()

        tool_object = self._load_synthesis_tool()
        tool_info = tool_object.get_keys()
        path_key = tool_info['id'] + '_path'
        name = tool_info['name']

        env = self.env
        env.check_general()
        env.check_tool(tool_object)

        if env[path_key]:
            tool_path = env[path_key]
        else:
            tool_path = ""

        logging.info("Generating synthesis makefile for " + name)
        tool_object.generate_synthesis_makefile(
            top_mod=self.get_top_module(),
            tool_path=tool_path)
        logging.info("Synthesis makefile generated.")


    def _write_project_vhd(self, tool, version):
        """Create a VHDL file containing a SDB compatible design description"""
        from string import Template
        from datetime import date
        import getpass

        today = date.today()
        date_string = today.strftime("%Y%m%d")
        template = Template("""library ieee;
use work.wishbone_pkg.all;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package sdb_meta_pkg is

  ------------------------------------------------------------------------------
  -- Meta-information sdb records
  ------------------------------------------------------------------------------

  -- Top module repository url
  constant c_SDB_REPO_URL : t_sdb_repo_url := (
    -- url (string, 63 char)
    repo_url => "$repo_url");

  -- Synthesis informations
  constant c_SDB_SYNTHESIS : t_sdb_synthesis := (
    -- Top module name (string, 16 char)
    syn_module_name  => "$syn_module_name",
    -- Commit ID (hex string, 128-bit = 32 char)
    -- git log -1 --format="%H" | cut -c1-32
    syn_commit_id    => "$syn_commit_id",
    -- Synthesis tool name (string, 8 char)
    syn_tool_name    => "$syn_tool_name",
    -- Synthesis tool version (bcd encoded, 32-bit)
    syn_tool_version => "$syn_tool_version", -- $syn_tool_version_str
    -- Synthesis date (bcd encoded, 32-bit)
    syn_date         => "$syn_date", -- $syn_date_str
    -- Synthesised by (string, 15 char)
    syn_username     => "$syn_username");

end sdb_meta_pkg;

package body sdb_meta_pkg is
end sdb_meta_pkg;""")

        project_vhd = open("project.vhd", 'w')
        date_std_logic_vector = []
        import re
        for digit in date_string:
            date_std_logic_vector.append("{0:04b}".format(int(digit)))

        syn_tool_version = version
        syn_tool_version = re.sub(r"\D", "", syn_tool_version)
        syn_tool_std_logic_vector = []
        for digit in syn_tool_version:
            syn_tool_std_logic_vector.append("{0:04b}".format(int(digit)))

        template.substitute(
            repo_url=self.top_module.url,
            syn_module_name=self.top_module.manifest_dict["syn_top"],
            syn_commit_id=self.top_module.revision,
            syn_tool_name=tool.upper(),
            syn_tool_version="0000"*(8-len(syn_tool_std_logic_vector)) +
                             ''.join(syn_tool_std_logic_vector),
	    syn_tool_version_str=syn_tool_version,
            syn_date=''.join(date_std_logic_vector),
	    syn_date_str=date_string,
            syn_username=getpass.getuser())
        project_vhd.write(template)
        project_vhd.close()


    def _check_synthesis_project(self):
        """Check the manifest contains all the keys for a synthesis project"""
        manifest = self.get_top_module().manifest_dict
        if not manifest["syn_tool"]:
            logging.error(
                "syn_tool variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not manifest["syn_device"]:
            logging.error(
                "syn_device variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not manifest["syn_grade"]:
            logging.error(
                "syn_grade variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not manifest["syn_package"]:
            logging.error(
                "syn_package variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not manifest["syn_top"]:
            logging.error(
                "syn_top variable must be set in the top manifest.")
            sys.exit("Exiting")


    def synthesis_project(self):
        """Generate a project for the specific synthesis tool"""
        self._check_all_fetched_or_quit()
        self._check_synthesis_project()

        tool_object = self._load_synthesis_tool()
        tool_info = tool_object.get_keys()
        path_key = tool_info['id'] + '_path'
        version_key = tool_info['id'] + '_version'
        name = tool_info['name']
        id_value = tool_info['id']
        ext_value = tool_info['project_ext']

        env = self.env
        env.check_general()
        env.check_tool(tool_object)

        if not self.env.options.force:
            if self.env[path_key] is None:
                logging.error("Can't generate the " + name + " project. "
                              + name + " not found.")
                quit()
        if version_key not in env or not env[version_key]:
            logging.error(name + " version cannot be deduced. Cannot generate "
                          + name + " project file properly. Please use syn_"
                          + id_value + "_version in the manifest or set")
            sys.exit("Exiting")
        logging.info("Generating project for " + name + " v. %s",
                     env[version_key])

        if (os.path.exists(self.top_module.manifest_dict["syn_project"]) or
            os.path.exists(self.top_module.manifest_dict["syn_project"] + "."
                           + ext_value)):
            logging.info("Existing project detected: updating...")
            update = True
        else:
            logging.info("No previous project: creating a new one...")
            update = False

        top_mod = self.get_top_module()
        fileset = self.build_file_set(top_mod.manifest_dict["syn_top"])
        privative_files = tool_object.supported_files(
            self.build_complete_file_set())

        if privative_files:
            logging.info("Privative / non-parseable files detected: %s",
                len(privative_files))
            fileset.add(privative_files)

        sff = SourceFileFactory()
        if self.env.options.generate_project_vhd:
            self._write_project_vhd(id_value, env[version_key])
            fileset.add([sff.new(path=path.rel2abs("project.vhd"),
                                 module=self.get_module_by_path("."))])

        tool_object.generate_synthesis_project(update=update,
                         tool_version=self.env[version_key],
                         top_mod=self.get_top_module(),
                         fileset=fileset)

        logging.info(name + " project file generated.")


    def _check_remote_synthesis(self):
        """Check we have all the variables to run a remote synthesis"""
        if not self.top_module.action == "synthesis":
            logging.error("action must be equal to \"synthesis\"")
            sys.exit("Exiting")

        if not self.top_module.manifest_dict["syn_project"]:
            logging.error("syn_project must be set in the manifest.")
            sys.exit("Exiting")


    def remote_synthesis(self):
        """Generate a Makefile that is able to run a remote synthesis"""
        self._check_all_fetched_or_quit()
        self._check_remote_synthesis()

        tool_object = self._load_synthesis_tool()
        logging.info("Generating makefile for remote synthesis.")

        top_mod = self.get_top_module()

        self.env.check_remote_tool(tool_object)
        self.env.check_general()

        files = self.build_file_set(
            self.get_top_module().manifest_dict["syn_top"])

        sff = SourceFileFactory()
        files.add(sff.new(top_mod.manifest_dict["syn_project"],
                          module=self.top_module))

        tool_object.generate_remote_synthesis_makefile(
            files=files, name=top_mod.manifest_dict["syn_project"][:-5],
            cwd=top_mod.url, user=self.env["rsynth_user"],
            server=self.env["rsynth_server"])
        logging.info("Remote synthesis makefile generated.")




