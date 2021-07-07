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

################################################################################
# Methods and classes

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
    @config.safeRun
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
        print(domain, flush=True)

        # Build the set of parameters in a YAML
        # TODO
        self.general['simulation_length'] = domain['parameters']['simulation_length']
        self.general['model_id'] = domain['model']['name']

        self.source['magnitude'] = body["event"]["magnitude"]
        self.source['longitude'] = body["event"]["longitude"]
        self.source['latitude'] = body["event"]["latitude"]
        self.source['depth'] = body["event"]["depth"]
        self.source['strike'] = body["event"]["CMT"]["strike"]
        self.source['rake'] = body["event"]["CMT"]["rake"]
        self.source['dip'] = body["event"]["CMT"]["dip"]
        self.source['corner_freq'] = domain['mesh']['corner_freq']
        self.source['freq_max'] = domain['mesh']['freq_max']
        self.source['mesh'] = domain['mesh']['paths']

        self.geometry = domain['model']['geometry']

        self.rupture['rupture'] = body["rupture"]

        self.receivers["infrastructures"] = receivers["infrastructures"]
        self.receivers["towns"] = receivers["towns"]

        # Prepare YAML sections
        inputP["general"] = self.general
        inputP["source"] = self.source
        inputP["geometry"] = self.geometry
        inputP["receivers"] = self.receivers
        inputP["rupture"] = "\n".join(self.rupture['rupture'])

        # Return list of Id of the newly created item
        return jsonify(result = inputP, response = 201)
