#!/usr/bin/env python3

# RESTful server for event treatment
# This module is part of the Automatic Alert System (AAS) solution

# Author:  Juan Esteban Rodríguez, Josep de la Puente
# Contact: juan.rodriguez@bsc.es, josep.delapuente@bsc.es

# ###############################################################################
#       BSD 3-CLAUSE, aka BSD NEW, aka BSD REVISED, aka MODIFIED BSD LICENSE

# Copyright 2023,2024 Josep de la Puente, Juan Esteban Rodriguez

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# 3. Neither the name(s) of the copyright holder(s) nor the name(s) of its
# contributor(s) may be used to endorse or promote products derived from this
# software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND CONTRIBUTOR(S) “AS
# IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S) OR CONTRIBUTOR(S) BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# ###############################################################################
import sys
import json
import ast
import traceback
from functools import wraps

# Flask (WSGI) utils
from flask import Flask, request, jsonify

# Load slip-gen service implemented components
from ucis4eq.scc.slipGen import SlipGenGP, SlipGenGPSetup

# ###############################################################################
# Dispatcher App creation
# ###############################################################################
slipGenServiceApp = Flask(__name__)


# POST request decorator
def postRequest(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):

        """
        Function to dispatch new events.
        """
        # Create new events
        try:
            #print("INFO: Received JSON: " + str(request.get_json()))
            body = ast.literal_eval(json.dumps(request.get_json()))
        except:
            # Bad request as request body is not available
            # Add message for debugging purposes [commit aa4808f: mpc]
            print("Error in JSON request. Received the following JSON: " + str(request.get_json()))
            traceback.print_exc()
            return "Error in JSON request format " + str(request.get_json()), 400

        # Call the decorated method passing it the input JSON
        return fn(body)

    return wrapped

# Base root of the micro-services Hub
@slipGenServiceApp.route("/")
def get_initial_response():
    """Welcome message for the API."""
    # Message to the user
    message = {
        'apiVersion': 'v1.0',
        'status': '200',
        'message': 'Welcome to the UCIS4EQ Slip Generation service for PD1'
    }
    # Making the message looks good
    resp = jsonify(message)
    # Returning the object
    return resp

# ###############################################################################
# Services definition
# ###############################################################################

# Determine the kind of source for the simulation
@slipGenServiceApp.route("/preGraves-Pitarka", methods=['POST'])
@postRequest
def slipGenGPSetupService(body):
    """
    Call component implementing this service
    """
    return SlipGenGPSetup().entryPoint(body)

# Determine the kind of source for the simulation
@slipGenServiceApp.route("/Graves-Pitarka", methods=['POST'])
@postRequest
def slipGenGPService(body):
    """
    Call component implementing this service
    """
    return SlipGenGP().entryPoint(body)

# ###############################################################################
# Start the micro-services aplication
# ###############################################################################

if __name__ == '__main__':
    # Running app in debug mode
    slipGenServiceApp.run(host="0.0.0.0", debug=True, port=5002)
