#!/usr/bin/env python3
#
# Slip generation
# This module is part of the Smart Center Control (SSC) solution
#
# Author:  Juan Esteban Rodríguez, Josep de la Puente
# Contact: juan.rodriguez@bsc.es, josep.delapuente@bsc.es
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

################################################################################
# Module imports
# System
import sys
import os
import traceback
import json
import uuid
from bson.json_util import dumps

# Third parties
from flask import jsonify

# Internal
from ucis4eq.misc import config
from ucis4eq.scc import microServiceABC

################################################################################
# Methods and classes

class SlipGenGP(microServiceABC.MicroServiceABC):

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Call the Graves-Pitarka slip generator
        """

        result = {}
        path = "/workspace/scratch/outdata/"
        cmt = body['CMT']   
        
        # Create the input parameter for slip-gen
        # TODO: Generate the setup according to received event alert
        
        # Generate an UUID for the current slip generation
        result['id'] = str(uuid.uuid1())
        
        # Define Source file
        source = path + result['id'] + ".src "
        
        # Start running the triggering system
        args = "/root/inputs/test_ice21june.src " + source + str(cmt['strike']) + " " + str(cmt['rake']) + " " + str(cmt['dip'])
        os.system("/bin/bash -c '/root/inputs/slipgen_inputs.sh " + args + "'")

        # TODO: Generate the input parameters in real time (whenever possible)
        args = "-o " + result['id'] + " -v /root/inputs/Iceland-vs500.fk1d -s " + source + " -i /root/inputs/init_slip_21june2000_Perdersen2003.txt -a 0.99 > /dev/null 2>&1"
        os.system("/bin/bash -c '/root/scripts/launcher.sh " + args + "'")
        
        # Read the generated SRF
        with open(path + result['id'] + "/" + result['id'] + ".srf", encoding="utf-8") as f:
            #result['slipmodel'] = f.readlines();
            result['slipmodel'] = f.read().splitlines()
                
        # Return list of Id of the newly created item
        # TODO: Return the SRF in plain text 
        return jsonify(result = result, response = 201)
                
