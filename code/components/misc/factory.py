#!/usr/bin/env python3

# General abstract factory 
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
#from __future__ import annotations
from abc import ABC, abstractmethod

# ###############################################################################
# Methods and classes
class Factory():

    def __init__(self):
        """
        Factory initialization
        """
        self._builders = {}
        
    # Method for registering builders    
    def registerBuilder(self, key, builder):
        #print("Registering builder for '" + key + "' builder")
        self._builders[key] = builder
            
    # Method for choosing the best builder
    def selectFrom(self, options):
        """
        Select a builder from a set 
        """
        
        if not options.keys():
            raise Exception('There are no builder to select')
        else:
            name = list(options)[0]
            
        return name, options[name]
        
    # Method to obtain an specific builder
    def __getitem__(self, key):
        return self._builders[key]
            
    # Method for look and returning the correct builder for a concrete instance
    def create(self, key, **kwargs):
        builder = self._builders.get(key)
        
        if not builder:
            raise ValueError(key)
            
        return builder(**kwargs)

class Provider(Factory):
    def get(self, service_id, **kwargs):
        return self.create(service_id, **kwargs)  
