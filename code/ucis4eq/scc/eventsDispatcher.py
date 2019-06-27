#!/usr/bin/env python3
#
# Events dispatcher
# This module is part of the Automatic Alert System (AAS) solution
#
# Author:  Juan Esteban Rodríguez, Josep de la Puente
# Contact: juan.rodriguez@bself.es, josep.delapuente@bself.es
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
from ucis4eq.scc import dispatcherApp, config
from bson.json_util import dumps
from flask import request, jsonify
import sys
import subprocess
import traceback
import json
import ast
import imp

################################################################################
# Methods and classes

# Import the helpers module
#helper_module = imp.load_source('*', './helpers.py')

# Select the database
db = config.client.EQEvents

@dispatcherApp.route("/")
def get_initial_response():
    """Welcome message for the API."""
    # Message to the user
    message = {
        'apiVersion': 'v1.0',
        'status': '200',
        'message': 'Welcome to the Flask API'
    }
    # Making the message looks good
    resp = jsonify(message)
    # Returning the object
    return resp

@dispatcherApp.route("/api/v1/events", methods=['POST'])
def incommingEvents():
    """
    Function to dispatch new events.
    """
    try:
        # Create new events
        try:
            body = ast.literal_eval(json.dumps(request.get_json()))
        except:
            # Bad request as request body is not available
            # Add message for debugging purpose
            return "", 400

        # Insert each source
        record_created = db.EQSources.insert(body['sources'])

        # Store the set of events
        for key, value in body['events'].items():
            value['sources_id'] = record_created
            value['id'] = key
            record_created = db.EQEvents.insert(value)

        # Prepare the response
        if isinstance(record_created, list):
            # Return list of Id of the newly created item
            return jsonify([str(v) for v in record_created]), 201
        else:
            # Return Id of the newly created item
            return jsonify(str(record_created)), 201
    except Exception as error:
        # Error while trying to create the resource
        # Add message for debugging purpose
        print("Exception in code:")
        print('-'*80)
        traceback.print_exc(file=sys.stdout)
        print('-'*80)
        return "", 500
