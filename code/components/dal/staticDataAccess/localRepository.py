#!/usr/bin/env python3

# Abstract factory for accessing storage repositories
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
from ucis4eq.dal.staticDataAccess.staticDataAccess import RepositoryABC

# ###############################################################################
# Methods and classes

class LocalRepository(RepositoryABC):
    def __init__(self, location):
        self._location = location

    def authenticate(self):
        pass
    
    def mkdir(self):
        print("Creating directory in Local")
        
    def tree(self):
        print("Obtaining list of files from Local")
        
    def downloadFile(self):
        print("Downloading file from Local")
        pass
        
    def uploadFile(self):
        print("Uploading file to Local")
        pass    
    
class LocalRepositoryBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, localClientKey, localClientSecret, **_ignored):
        if not self._instance:
            accessCode = self.authorize(
                localClientKey, localClientSecret)
            self._instance = LocalRepository(accessCode)
        return self._instance

    def authorize(self, key, secret):
        return 'LOCAL_ACCESS_CODE'
