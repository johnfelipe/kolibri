"""
Kolibri template tags
=====================

To use

.. code-block:: html

    {% load kolibri_tags %}

    <ul>
    {% for navigation in kolibri_main_navigation %}
        <li><a href="{{ navigation.menu_url }}">{{ navigation.menu_name }}</a></li>
    {% endfor %}
    </ul>

"""
from __future__ import absolute_import, print_function, unicode_literals

import json

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from .. import hooks
from ..utils import get_async_events, get_webpack_bundle

register = template.Library()


def render_as_tags(bundle):
    """
    This function tags a bundle of file chunks and generates the appropriate script tags for them,
    be they JS or CSS files.
    :param bundle: The full module path and name of the FrontEnd Plugin
    :return: HTML of script tags for insertion into a page.
    """
    tags = []
    for chunk in bundle:
        if chunk['name'].endswith('.js'):
            tags.append('<script type="text/javascript" src="{url}"></script>'.format(url=render_as_url(chunk)))
        elif chunk['name'].endswith('.css'):
            tags.append('<link type="text/css" href="{url}" rel="stylesheet"/>'.format(url=render_as_url(chunk)))
    return mark_safe('\n'.join(tags))


def render_as_url(chunk):
    """
    This function returns the URL for a particular chunk (JS or CSS file), by appending the url or public path
    for the file to the current STATIC_URL set in settings.
    :param chunk: A dictionary with a url or publicPath attribute - this is generated by Webpack.
    :return: The URL to the file for the client.
    """
    static = getattr(settings, 'STATIC_URL')
    url = chunk.get('publicPath') or chunk['url']
    return "{static}{url}".format(static=static, url=url)


def render_as_async(bundle):
    """
    This function returns a script tag containing Javascript to register an asynchronously loading Javascript
    FrontEnd plugin against the core FrontEnd Kolibri app. It passes in the events that would trigger loading
    the plugin, both multi-time firing events (events) and one time firing events (once). It also passes in information
    about the methods that the events should be delegated to once the plugin has loaded.
    :param bundle: The full module path and name of the FrontEnd Plugin
    :return: HTML of a script tag to insert into a page.
    """
    chunks = get_webpack_bundle(bundle, None)
    async_events = get_async_events(bundle)
    urls = [render_as_url(chunk) for chunk in chunks]
    js = 'Kolibri.register_kolibri_module_async("{bundle}", ["{urls}"], {events}, {once});'.format(
        bundle=bundle,
        urls='","'.join(urls),
        events=json.dumps(async_events.get('events')),
        once=json.dumps(async_events.get('once'))
    )
    return mark_safe('<script>{js}</script>'.format(js=js))


@register.simple_tag()
def frontend_assets(unique_slug, extension=None):
    """
    This template tag returns HTML that loads all JS and CSS assets (or filtered by extension) for insertion into the
    Django template. KolibriModules loaded in this way will execute, initialize and register at page load.
    :param bundle_path: The path of the bundle (the Python module path for the Kolibri plugin, and the name of the
    Plugin Class that the KolibriModule is defined by).
    :param extension: Extension to filter files by (probably 'js' or 'css').
    :return: Marked safe HTML for insertion into the DOM.
    """
    return render_as_tags(get_webpack_bundle(unique_slug, extension))


@register.simple_tag()
def async_frontend_assets(bundle_path):
    """
    This template tag returns inline Javascript (wrapped in a script tag) that registers the events that a KolibriModule
    listens to, and a list of JS and CSS assets that need to be loaded to instantiate the KolibriModule Django template.
    KolibriModules loaded in this way will not be executed, initialized or registered until one of the defined events is
    triggered.
    :param bundle_path: The path of the bundle (the Python module path for the Kolibri plugin, and the name of the
    Plugin Class that the KolibriModule is defined by).
    :return: Inline Javascript as HTML for insertion into the DOM.
    """
    return render_as_async(bundle_path)


@register.simple_tag()
def base_frontend_sync():
    """
    This is a script tag for the BASE_FRONTEND_SYNC hook - this is used in the base.html template to populate any
    Javascript and CSS that should be loaded at page load.
    :return: HTML of script tags to insert into base.html
    """
    tags = []
    for hook in hooks.FrontEndSyncHook().registered_hooks:
        tags.append(render_as_tags(get_webpack_bundle(hook.unique_slug, None)))
    return mark_safe('\n'.join(tags))

@register.simple_tag()
def base_frontend_async():
    """
    This is a script tag for the BASE_FRONTEND_ASYNC hook - this is used in the base.html template to populate any
    Javascript and CSS that should be registered at page load, but loading deferred until needed.
    :return: HTML of script tags to insert into base.html
    """
    tags = []
    for hook in hooks.FrontEndASyncHook().registered_hooks:
        tags.append(render_as_tags(get_webpack_bundle(hook.unique_slug, None)))
    return mark_safe('\n'.join(tags))