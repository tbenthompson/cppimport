import sys
import cppimport.importer

class Hook(object):
    def __init__(self):
        self._running = False
        self.print_exceptions = False

    def find_module(self, fullname, path = None):
        # Prevent re-entry by the underlying importer
        if self._running:
            return

        try:
            self._running = True
            cppimport.importer.imp(fullname, opt_in = True)
        except ImportError as e:
            # ImportError should be quashed because that simply means cppimport
            # didn't find anything, and probably shouldn't have found anything!
            if self.print_exceptions:
                import traceback
                print(traceback.format_exc())
        finally:
            self._running = False

hook_obj = Hook()
sys.meta_path.insert(0, hook_obj)
