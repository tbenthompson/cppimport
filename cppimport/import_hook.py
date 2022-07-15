import logging
import sys
import traceback

import cppimport

logger = logging.getLogger(__name__)


class Hook(object):
    def __init__(self):
        self._running = False

    def find_spec(self, fullname, path, target=None):
        # Prevent re-entry by the underlying importer
        if self._running:
            return

        try:
            self._running = True
            cppimport.imp(fullname, opt_in=True)
        except ImportError:
            # ImportError should be quashed because that simply means cppimport
            # didn't find anything, and probably shouldn't have found anything!
            logger.debug(traceback.format_exc())
        finally:
            self._running = False


# Add the hook to the list of import handlers for Python.
hook_obj = Hook()
sys.meta_path.insert(0, hook_obj)
