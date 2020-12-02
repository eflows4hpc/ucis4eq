#!/usr/bin/env python3
#
# Salvus (Wave propagation simulator)
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
import yaml
from bson.json_util import dumps

# Third parties
from flask import jsonify

# Internal
from ucis4eq.misc import config
from ucis4eq.scc import microServiceABC

################################################################################
# Methods and classes

class SalvusRun(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self, input):
        """
        Initialize SalvusRun instance
        """
        
        # Select the database
        self.input = input

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Call the Salvus-Flow Marta's wrapper
        """

        # Enable multiline writting
        yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str

        def repr_str(dumper, data):
            if '\n' in data:
                return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')
            return dumper.org_represent_str(data)

        yaml.add_representer(str, repr_str, Dumper=yaml.SafeDumper)
        
        # Create the drectory for the current execution
        workSpace = "/workspace/runs/" + body["uuid"]
        os.makedirs(workSpace, exist_ok=True)
        os.chdir(workSpace)
        
        # Create symbolic link to the model
        modelName =  body["input"]["general"]["model_id"] + ".bm"
        #os.symlink(self.input + "/" + modelName, workSpace + "/" + modelName)
              
        # Write the YAML file
        inputPyaml = yaml.safe_dump(body["input"])
        pfile = workSpace + "/" + body["uuid"] + ".yaml"
        with open(pfile, "w") as f:
           f.write(inputPyaml)

        # TODO: Retrieve the model path from the DB or something similar
    
        # TODO: Obtain this information from the DB or whatever other mechanism
        site = "demo"
        nprocs = 4
        wtime = 1800

        # Build the arguments for the wrapper
        args = site + " " + str(nprocs) + " " + str(wtime) + " " + pfile + " " + workSpace + "/output"
         
        # Run it!
        print("python /root/salvusWrapper/trial_configuration.py " + args, flush=True)
        os.system("/bin/bash -c 'python /root/salvusWrapper/trial_configuration.py " + args + "'")

        # Return list of Id of the newly created item
        return jsonify(result = workSpace + "/output", response = 201)
        

class SalvusPost(microServiceABC.MicroServiceABC):

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Call the Salvus-Flow Marta's wrapper
        """
       
        # Run postprocess
        os.system("/bin/bash -c 'python /root/salvusWrapper/plot_pgd_pgv_pga.py " + body + "'")
       
        # Return list of Id of the newly created item
        # TODO: Return the SRF in plain text 
        return jsonify(result = {}, response = 201)        
                
