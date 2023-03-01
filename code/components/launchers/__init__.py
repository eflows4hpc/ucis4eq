"""This is init module."""

################################################################################
# Module imports

import json

from ucis4eq.misc.factory import Provider 
from . import localRunner
from . import mn4Runner
from . import pdRunner
from . import PyCOMPSsRunner

# Create the launcher's registry
launchers = Provider()

# Register each data repository
launchers.registerBuilder('LOCAL', localRunner.LocalRunnerBuilder())
# launchers.registerBuilder('MN4', mn4Runner.MN4RunnerBuilder())
launchers.registerBuilder('MN4', PyCOMPSsRunner.PyCOMPSsRunnerBuilder())
launchers.registerBuilder('DAINT', pdRunner.PDRunnerBuilder())

# Load computational sites setting
config = None
with open("/opt/Sites.json", 'r') as f:
    config = json.load(f)
