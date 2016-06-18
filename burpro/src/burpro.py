# -*- coding: utf-8 -*-
"""
:DESCRIPTION: This code processes EXO KOR Burst data files

:REQUIRES: burpro_setup.py, burpro_run_mgr.py, burpro_process.py, .xlsx burst data files in cwd folder "data", .json config files

:AUTHOR: John Franco Saraceno, John M. Donovan
:ORGANIZATION: U.S. Geological Survey, United States Department of Interior
:CONTACT: saraceno@usgs.gov, jmd@usgs.gov

"""
# =============================================================================
# IMPORT STATEMENTS
# =============================================================================
import sys
import logging

from burpro_setup import handle_args, setup_output_dir, setup_logging, report_setup_error
from burpro_run_mgr import manage_run

# =============================================================================
# MAIN METHOD AND TESTING AREA
# =============================================================================

def main(argv=None):
    try:
        exo_filename = handle_args(burpro_version(), argv)
        output_dir = setup_output_dir(exo_filename)
        log = setup_logging(output_dir, burpro_version())

        try:
            manage_run(exo_filename, output_dir)
            log.info('BurPro done.')
        except:        
            # Logger is set up.  Handle an error by logging it and exiting
            log.error(logging.Formatter().formatException(sys.exc_info()))
            sys.exit(3)
    except Exception, setup_error:
        # Logger was not set up.  Report errors to the console.
        report_setup_error(setup_error)
        
def burpro_version():
    return '2016-06-17'

if __name__ == "__main__":
    sys.exit(main())
    