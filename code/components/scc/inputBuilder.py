#!/usr/bin/env python3
#
# Input builder (Interphasing phase 1 and phase 2)
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
import traceback
import json
import yaml
from bson.json_util import dumps

# Third parties
from flask import jsonify

# Internal
from ucis4eq.misc import config
from ucis4eq.scc import microServiceABC

################################################################################
# Methods and classes

class InputParametersBuilder(microServiceABC.MicroServiceABC):
    
    # Initialization method
    def __init__(self):
        """
        Initialize the CMT statistical component implementation
        """
        
        # Select the database
        self.db = config.database
        
        # Set input parameters for the wrapper categories
        self.general = {}
        self.source = {}
        self.geometry = {}
        self.rupture = {}
        self.receivers = {}
        
    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Build the set of simulation parameters in YAML format   
        """
        # Initialize inputP dict 
        inputP = {}
        
        # Obtain information from the DB            
        # Notice that more than one results can be returned.
        # We always take the first one
        receivers = self.db["Receivers"].find_one({"id": body['region']['id']})
        
        #print({str(k).encode("utf-8"): v for k,v in receivers["infrastructures"].items()}, flush=True)
        region = self.db["Regions"].find_one({"id": body['region']['id']})
                    
        # Build the set of parameters in a YAML
        # TODO
        self.general['simulation_length'] = region['parameters']['simulation_length']
        self.general['model_id'] = region['model']['name']
        
        self.source['magnitude'] = body["event"]["magnitude"]
        self.source['longitude'] = body["event"]["longitude"]
        self.source['latitude'] = body["event"]["latitude"]
        self.source['depth'] = body["event"]["depth"]
        self.source['strike'] = body["event"]["CMT"]["strike"]
        self.source['rake'] = body["event"]["CMT"]["rake"]
        self.source['dip'] = body["event"]["CMT"]["dip"]
        self.source['corner_freq'] = region['parameters']['corner_freq']
        self.source['freq_max'] = region['parameters']['freq_max']
        
        self.geometry = region['model']['geometry']
        
        self.rupture['rupture'] = body["rupture"]
        
        self.receivers["infrastructures"] = receivers["infrastructures"]
        self.receivers["seismic_stations"] = receivers["seismic_stations"]
        
        # Prepare YAML sections
        inputP["general"] = self.general
        inputP["source"] = self.source
        inputP["geometry"] = self.geometry
        inputP["receivers"] = self.receivers
        inputP["rupture"] = "\n".join(self.rupture['rupture'])
        
        # Enable multiline writting
        yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str

        def repr_str(dumper, data):
            if '\n' in data:
                return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')
            return dumper.org_represent_str(data)

        yaml.add_representer(str, repr_str, Dumper=yaml.SafeDumper)
            
        # Write the YAML file
        # TODO: This file should be sent to other service
        inputPyaml = yaml.safe_dump(inputP)
        with open("/tmp/" + body["uuid"] + ".yaml", "w") as f:
            f.write(inputPyaml)
            #yaml.safe_dump(inputP, f)
                        
        # Return list of Id of the newly created item
        return jsonify(result = {}, response = 201)
