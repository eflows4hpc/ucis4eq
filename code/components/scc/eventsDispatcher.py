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
from bson.json_util import dumps

# Third parties
from flask import jsonify

# Internal
from ucis4eq.misc import config
from ucis4eq.scc import microServiceABC

################################################################################
# Methods and classes

class eventsDispatcher(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the eventDispatcher component implementation    
        """
        
        # Select the database
        self.db = config.database

    # Service's entry point definition
    def entryPoint(self, body):
        """
        Deal with a new earthquake event
        """
        try:
            # Insert each source
            record_created = self.db.EQSources.insert(body['sources'])

            records = []
            # Store the set of events
            for key, value in body['events'].items():
                field = {}
                field['alerts'] = value
                field['sources_id'] = record_created
                #field['id'] = key
                records.append(self.db.EQEvents.insert(field))

            # Return list of Id of the newly created item
            return jsonify(result = [str(v) for v in records], response = 201)
                
        except Exception as error:
            # Error while trying to create the resource
            # Add message for debugging purpose
            print("Exception in code:")
            print('-'*80)
            traceback.print_exc(file=sys.stdout)
            print('-'*80)
            return jsonify(result = {}, response = 501)