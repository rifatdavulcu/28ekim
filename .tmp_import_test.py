import importlib
try:
    m = importlib.import_module('gui.invoice_widget')
    print('IMPORT_OK', getattr(m, '__file__', None))
except Exception as e:
    import traceback
    traceback.print_exc()
    print('IMPORT_FAILED', e)
