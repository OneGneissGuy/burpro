# -*- coding: utf-8 -*-
"""
:DESCRIPTION: This code processes EXO KOR Burst data files

:REQUIRES: burpro_setup.py, burpro_run_mgr.py, burpro_process.py,
           .xlsx burst data files in cwd folder "data", .json config files

:AUTHOR: John Franco Saraceno, John M. Donovan
:ORGANIZATION: U.S. Geological Survey, United States Department of Interior
:CONTACT: saraceno@usgs.gov, jmd@usgs.gov

"""
# =============================================================================
# IMPORT STATEMENTS
# =============================================================================
from __future__ import print_function

import datetime
import logging
import os
import sys


from burpro_setup import handle_args, setup_output_dir, report_setup_error
from burpro_setup import setup_logger, takedown_logger
from burpro_run_mgr import manage_run
# =============================================================================
# MAIN METHOD AND TESTING AREA
# =============================================================================


def main(argv=None):
    try:
        version = burpro_version()
        files = handle_args(version, argv)
        print(files)
        for exo_filename in files:
            output_dir = setup_output_dir(exo_filename)
            run_log = 'BurPro'
            device_log = 'EXOdevices'
            log_ext = '.log'
            setup_logger(run_log, os.path.join(output_dir, run_log + log_ext))
            setup_logger(device_log, os.path.join(output_dir,
                                                  device_log + log_ext))
    # TODO: make these log instances more descriptive
            log = logging.getLogger(run_log)
            log.info('USGS California Water Science Center')
            log.info('BurPro Revision ' + version)
            try:
                print(exo_filename)
                manage_run(exo_filename, output_dir)
                takedown_logger(run_log)
                takedown_logger(device_log)
                log.info('BurPro done.')

            except:
                # Logger is set up.  Handle an error by logging it and exiting
                log.error(logging.Formatter().formatException(sys.exc_info()))
                sys.exit(3)
    except Exception, setup_error:
        # Logger was not set up.  Report errors to the console.
        report_setup_error(setup_error)


def burpro_version():
    # TODO: Return production code version, not current date when src is stable
    return datetime.datetime.now().strftime("%Y-%m-%d")

if __name__ == "__main__":
    sys.exit(main())
