#!/usr/bin/env python3
#
# Events dispatcher
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

from bson.json_util import dumps
from bson import ObjectId

# Third parties
from flask import jsonify

# Internal
from ucis4eq.misc import config
from ucis4eq.scc import microServiceABC

################################################################################
# Methods and classes

class IndexPriority(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self, data):
        """
        Initialize the eventDispatcher component implementation    
        """
        # TODO: @Marisol, remember that data is the path to the data you need
        # Use like that:
    
        # 1- Read the JSON file in "data+*json"
        # 2- For each file in JSON
        # 3- Load the file data 
        # 3.1- self.classifiers = data + "Classifier_svm.sav"
            
        # Select the database
        self.db = config.database

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        This method will figure out the index priority for a given event
        """
        # TODO: Put your code here @Marisol
        #print(body, flush = True)

        # TODO: This is just an output example
        myresult = {"priority": "1"} 
        
        # Return list of Id of the newly created item
        return jsonify(result = myresult, response = 201)            
