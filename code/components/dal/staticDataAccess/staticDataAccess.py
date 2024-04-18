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
#from __future__ import annotations
from abc import ABC, abstractmethod

import ucis4eq
from ucis4eq.misc.factory import Factory 

# ###############################################################################
# Methods and classes

class SDAFactory(Factory):
    
    # Method for choosing best repository
    def selectFrom(self, repositories, repo):
        """
        Select a repository from a set 
        """
 
        # TODO: Add some mechanism for choosing a repository,
        #       load balancing, etc...
        if repo in repositories.keys():
            repository = repo
        elif len(repositories.keys()) == 1:
            repository = list(repositories)[0]
        elif ucis4eq.dal.repository in repositories.keys():
            repository = ucis4eq.dal.repository
        else:
            print("WARNING: No repository found for current file")
            return None, None
                           
        return repository, repositories[repository]

class SDAProvider(SDAFactory):
    def get(self, service_id, **kwargs):
        return self.create(service_id, **kwargs)

class RepositoryABC(ABC):
    """
    The Product interface declares the operations that all concrete repositories
    must implement.
    """
    
    @abstractmethod
    def authenticate(self):
        """
        Authenticates against a repository
        """
        pass

    @abstractmethod
    def mkdir(self, rpath):
        """
        Creates a new directory
        """        
        pass
        
    @abstractmethod
    def tree(self, rpath):
        """
        Obtains the list of files in a remote directory
        """        
        pass        

    @abstractmethod
    def downloadFile(self):
        """
        Downloads a file
        """        
        pass
        
    @abstractmethod
    def uploadFile(self):
        """
        Upload a file
        """        
        pass
        
