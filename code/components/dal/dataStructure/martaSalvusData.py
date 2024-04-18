#!/usr/bin/env python3

# Slurm specialization launcher
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
import os
import time
import subprocess
import threading

# Internal
import ucis4eq.dal as dal
from ucis4eq.dal import staticDataMap
from ucis4eq.dal.dataStructure.dataStructure import DataStructureABC

# ###############################################################################
# Methods and classes
@staticDataMap.build
class MartaSalvusData(DataStructureABC):

    # Initialization method
    def __init__(self):
        # Select the database
        self.format = "Marta_Salvus"
        
        # Obtain format structure
        col = dal.database['DataStructure']
        query = { "id": {"$eq": self.format} }
        self.structure = col.find_one(query, {'_id': False, 'id': False})    
        
        # Obtain directories
        self.structureFileMap = None
        self.pathValidation = False
    
    # Obtain the path to an specific file    
    def prepare(self, region):
        # Obtain regions's files
        self.structureFileMap = self.filePing[region]
        
        if isinstance(self.structureFileMap, list):
            self.pathValidation = True
                    
    # Obtain the path to an specific file
    def getPathTo(self, attribute, selectors=None):
        
        path = None
        
        if not attribute == 'root' and attribute in self.structure.keys():
            attributeName = self.structure[attribute]['name']
            
            if self.pathValidation:
                matches = [match for match in self.structureFileMap if attributeName in match]
                if selectors and isinstance(selectors, list):
                    for selector in selectors:
                        generalMatches = matches
                        matches = [match for match in generalMatches if selector in match]
                        
                if matches:
                    path = matches[-1]
                                    
            else:
                path = self.structure[attribute]['name'] + "/"
            
        # Return the set of instructions
        return path
