#!/usr/bin/python
# -*- coding: utf-8 -*-

from os.path import sep, abspath, dirname

from fabric.context_managers import settings as _settings

from provy.core.utils import import_module
from provy.core.errors import ConfigurationError

def run(provfile_path, role_name, server_name, password):
    module_path = provfile_path.replace(sep, '.')
    prov = import_module(module_path)
    roles = get_roles_for(prov, role_name)
    servers = get_servers_for(prov, server_name)

    context = {
        'abspath': dirname(abspath(provfile_path)),
        'path': dirname(provfile_path),
        'cleanup': []
    }

    for server in servers:
        host_string = "%s@%s" % (server['user'], server['address'])

        msg = "Provisioning %s..." % host_string
        print
        print "*" * len(msg)
        print msg
        print "*" * len(msg)
        with _settings(
            host_string=host_string,
            password=password
        ):
            context['host'] = server['address']
            context['user'] = server['user']
            role_instances = []
            for role in roles:
                context['role'] = role
                instance = role(prov, context)
                role_instances.append(instance)
                instance.provision()

            for role in role_instances:
                role.cleanup()

            for role in context['cleanup']:
                role.cleanup()

        msg = "%s provisioned!" % host_string
        print
        print "*" * len(msg)
        print msg
        print "*" * len(msg)
        print

def get_roles_for(prov, role_name):
    return get_items(prov, role_name, 'roles', lambda item: isinstance(item, (list, tuple)))

def get_servers_for(prov, server_name):
    return get_items(prov, server_name, 'servers', lambda item: isinstance(item, dict) and 'address' in item, recursive=True)

def get_items(prov, item_name, item_key, test_func, recursive=False):
    if not hasattr(prov, item_key):
        raise ConfigurationError('The %s collection was not found in the provyfile file.' % item_key)

    items = getattr(prov, item_key)

    for item_part in item_name.split('.'):
        items = items[item_part]

    if not recursive:
        return items

    found_items = []
    recurse_items(items, test_func, found_items)
    return found_items

def recurse_items(col, test_func, found_items):
    if not isinstance(col, dict):
        return

    if test_func(col):
        found_items.append(col)
    else:
        for key, val in col.iteritems():
            if test_func(val):
                found_items.append(val)
            else:
                recurse_items(val, test_func, found_items)

