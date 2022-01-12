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
from ucis4eq.misc import config, microServiceABC
import ucis4eq as ucis4eq
from ucis4eq.dal import staticDataMap

################################################################################
# Methods and classes

@staticDataMap.build
class InputParametersBuilder(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the CMT statistical component implementation
        """

        # Select the database
        self.db = ucis4eq.dal.database

        # Set input parameters for the wrapper categories
        self.general = {}
        self.source = {}
        self.geometry = {}
        self.rupture = {}
        self.receivers = {}

    # Service's entry point definition
    @microServiceABC.MicroServiceABC.runRegistration
    def entryPoint(self, body):
        """
        Build the set of simulation parameters
        """
        # Initialize inputP dict
        inputP = {}

        # Obtain information from the DB
        # Notice that more than one results can be returned.
        # We always take the first one
        receivers = self.db["Receivers"].find_one({"id": body['domain']['region']})

        #print({str(k).encode("utf-8"): v for k,v in receivers["infrastructures"].items()}, flush=True)
        domain = self.db["Domains"].find_one({"id": body['domain']['id']})

        # Build the set of parameters in a YAML
        # TODO
        self.general['simulation_length_in_s'] = domain['parameters']['simulation_length']
        self.general['fmax_in_hz'] = domain['parameters']['freq_max']
        self.general['generate_mesh'] = "no"
        self.general['overwrite_mesh_path'] = "no"
        
        self.geometry['coordinates'] = domain['model']['geometry']
        self.geometry['region_ID'] = domain['region']
                
        paths = {}
        for file in domain['files']:
            if not domain['files'][file] == "":
                paths[file] = self.filePing[domain['files'][file]]
        self.geometry['filepaths'] = paths
    
        self.source['magnitude'] = body["magnitude"]
        self.source['longitude'] = body["longitude"]
        self.source['latitude'] = body["latitude"]
        self.source['depth'] = body["depth"]
        self.source['strike'] = body["CMT"]["strike"]
        self.source['rake'] = body["CMT"]["rake"]
        self.source['dip'] = body["CMT"]["dip"]

        self.rupture['filename'] = body["rupture"]

        for receiverType in receivers.keys():
            if not receiverType == "id" and not receiverType == "_id":
                self.receivers[receiverType] = receivers[receiverType]

        # Prepare YAML sections
        inputP = self.general
        inputP["geometry"] = self.geometry
        inputP["CMT_source"] = self.source
        inputP["rupture"] = self.rupture
        inputP["receivers"] = self.receivers    

        # Return list of Id of the newly created item
        return jsonify(result = inputP, response = 201)
