# -*- coding: utf-8 -*-
"""
Copy and modify this code for your own plugin.
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging

from kolibri.plugins.base import KolibriPluginBase

logger = logging.getLogger(__name__)


class NavMenuPlugin(KolibriPluginBase):
    """
    An example plugin that demonstrates how the Kolibri plugin system works.
    """

    @classmethod
    def enable(cls):
        """
        A plugin must implement this abstract method. It's called by the command
        ``kolibri plugin <NAME> enable`` to modify the kolibri settings file.

        :return: Nothing, though it may modify the mutable config parameter
        """
        super(NavMenuPlugin, cls).enable()
        logger.info("Enabled example plugin")

    @classmethod
    def disable(cls):
        """
        A plugin must implement this abstract method. It's called by the command
        ``kolibri plugin <NAME> disable`` to modify the kolibri settings file.

        :return: Nothing, though it may modify the mutable config parameter
        """
        super(NavMenuPlugin, cls).disable()
        logger.info("Disable example plugin")


class ExtendedPlugin(NavMenuPlugin):
    """
    Demonstrates plugin inheritance.
    """

    @classmethod
    def enable(cls):
        # Do nothing because the parent will initialize the plugin as we want
        pass

    @classmethod
    def disable(cls):
        # Do nothing because the parent will initialize the plugin as we want
        pass
