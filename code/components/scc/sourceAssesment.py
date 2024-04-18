#!/usr/bin/env python3

# Source Assesment
# This module is part of the Smart Center Control (SSC) solution

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
# Module imports
# System
import sys
import traceback
from bson.json_util import dumps

# Third parties
from flask import jsonify

# Internal
import ucis4eq
from ucis4eq.misc import config, microServiceABC

# ###############################################################################
# Methods and classes

class SourceType(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the sourceType component implementation    
        """

    # Service's entry point definition
    @microServiceABC.MicroServiceABC.runRegistration            
    def entryPoint(self, body):
        """
        Determine if the type of sources. This is:
           - Punctual (implemented as an UCIS4EQ component)
           - Slip distribution model (generated externally with Graves-Pitarka)
        """
        # TODO: Calculate the source type and return it
        # - 'punctual'
        # - 'slipdist'
        # - 'all' 

        sourcetype = 'slipdist'
            
        # Return list of Id of the newly created item
        return jsonify(result = sourcetype, response = 201)

class PunctualSource(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the punctualSource component implementation    
        """

    # Service's entry point definition
    @config.safeRun
    @microServiceABC.MicroServiceABC.runRegistration            
    def entryPoint(self, body):
        """
        Deal with a new earthquake event
        """
        
        # TODO: Calculate the punctual source en return it 

        # Return list of Id of the newly created item
        return jsonify(result = {}, response = 201)
