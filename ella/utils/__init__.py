from importlib import import_module

from django.core.exceptions import ImproperlyConfigured

def import_module_member(modstr, noun=''):
    module, attr = modstr.rsplit('.', 1)
    try:
        mod = import_module(module)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing %s %s: "%s"' % (noun, modstr, e))
    try:
        member = getattr(mod, attr)
    except AttributeError, e:
        raise ImproperlyConfigured('Error importing %s %s: "%s"' % (noun, modstr, e))
    return member


