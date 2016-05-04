"""
How plugins work
----------------

From a user's perspective, plugins are enabled and disabled through the command
line interface or through a UI. Users can also configure a plugin's behavior,
but it's up to the plugin to provide the Form classes and register them.

.. note::
    We have not yet written a configuration API, for now just make sure
    configuration-related variables are kept in a central location of your
    plugin.

However, from a developer's perspective, plugins are Django applications listed
in ``INSTALLED_APPS`` and are initialized once when the server starts, mean at
the load time of the django project, i.e. Kolibri.

Loading a plugin
~~~~~~~~~~~~~~~~

In general, a plugin should **never** modify internals of Kolibri or other
plugins without using the hooks API or normal conventional Django scenarios.

.. note::

    Each app in ``INSTALLED_APPS`` is searched for the special
    ``kolibri_plugin`` module.

Everything that a plugin does is expected to be defined through
``<myapp>/kolibri_plugin.py``.


"""
from __future__ import absolute_import, print_function, unicode_literals

import importlib
import logging

from django.conf import settings

from . import hooks
from .base import KolibriPluginBase

logger = logging.getLogger(__name__)

registry = {}

__initialized = False


def initialize():
    """
    Called once to register hook callbacks.
    """
    global __initialized

    if not __initialized:
        logger.debug("Loading kolibri plugin registry...")

        for app in settings.INSTALLED_APPS:
            try:
                plugin_module = importlib.import_module(app + ".kolibri_plugin")
                logger.debug("Loaded kolibri plugin: {}".format(app))
                plugin_classes = []
                for obj in plugin_module.PLUGINS:
                    if type(obj) == type and issubclass(obj, KolibriPluginBase):
                        plugin_classes.append(obj)
                for plugin_klass in plugin_classes:
                    plugin_obj = plugin_klass()
                    for hook, callback in plugin_obj.hooks().items():
                        hooks.register_hook(hook, callback)
            except ImportError:
                pass

        __initialized = True
