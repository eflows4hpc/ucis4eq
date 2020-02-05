#!/usr/bin/env python3
#
# FDSN-WebService Listener
# This module is part of the Automatic Alert System (AAS) solution
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

################################################################################
# Module importsmon
import sys
import os
import traceback
import argparse
import json

from ucis4eq.aas import FSDNClient

################################################################################
# Methods and classes

# Arguments parser
def parser():

    # Parse the arguments
    parser = argparse.ArgumentParser(
        prog='listener',
        description='FDSN-WS Listener')
    parser.add_argument('config', help='JSON configuration file')
    parser.add_argument('-p', dest='opid',
        help='Wait for a given PID before start')
    args = parser.parse_args()

    # Check the arguments
    if not os.path.isfile(args.config):
      raise Exception("The configuration file '"+args.config+ "' doesn't exist")

    # Return them
    return args

# Main Method
def main():
    try:
        # Call the parser
        args = parser()

        # Read the configuration file
        with open(args.config, 'r') as f:
            config = json.load(f)

        if( args.opid ):
            config['listener']['opid'] = args.opid

        if( config['webservice']['interface'] == "event" ):
            ws = FSDNClient.WSEvents(config)
        else:
            ws = FSDNClient.WSGeneral(config)

    except Exception as error:
        print("Exception in code:")
        print('-'*80)
        traceback.print_exc(file=sys.stdout)
        print('-'*80)

################################################################################
# Run the program
if __name__ == "__main__":
    main()
