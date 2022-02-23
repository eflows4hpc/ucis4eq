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
from ucis4eq.launchers import config
import ucis4eq as ucis4eq
import ucis4eq.dal as dal

################################################################################
# Methods and classes

class ComputeResources(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the CMT statistical component implementation
        """
        
        # Select the database
        self.db = ucis4eq.dal.database        

    # Service's entry point definition
    @microServiceABC.MicroServiceABC.runRegistration        
    def entryPoint(self, body):
        """
        Calculate the computational resources and site
        """

        # Decide what site to use among the availables
        resources = self.db.Resources.find({}, {'_id': False}).sort('order', 1)
        resource = None
        for site in list(resources):
            if site['id'] in config.keys():
                resource = site
            break
            
        # TODO: Calculate resources (e.g  #nodes and #cores)

        # Return list of Id of the newly created item
        return jsonify(result = resource, response = 201)
