#!/usr/bin/env python3

# Events notifier
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
import os
import sys
import traceback
import argparse
import json
import requests


def parser():

    # Parse the arguments
    parser = argparse.ArgumentParser(
        prog='notifier',
        description='Events notifier')
    parser.add_argument('config', help='JSON configuration file')
    parser.add_argument('data', help='JSON file')
    args = parser.parse_args()

    # Check the arguments
    if not os.path.isfile(args.config):
        raise Exception("The configuration file '"+args.config+ "' doesn't exist")

    # Return them
    return args

def main():
    try:
        # Call the parser
        args = parser()

        # Read the configuration file
        with open(args.config, 'r') as f:
            config = json.load(f)

        # Read the configuration file
        with open(args.data, 'r') as f:
            data = json.load(f)

        # Perform the request
        try:
            req = requests.post(config['url']+config['routes']['POST'], json=data)
        except Exception as error:
            print("Unaccesible event dispatcher: check that dispatcher is running and available")

    except Exception as error:
        print("Exception in code:")
        print('-'*80)
        traceback.print_exc(file=sys.stdout)
        print('-'*80)

# ###############################################################################

if __name__ == "__main__":
    main()
