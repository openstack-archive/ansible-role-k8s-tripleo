#!/usr/bin/env python


DOCUMENTATION = '''
---
module: helm
short_description: Manages Kubernetes packages with the Helm package manager
version_added: "2.4"
author: "Flavio Percoco (flaper87)"
description:
   - Install, upgrade, delete and list packages with the Helm package manage
requirements:
  - "pyhelm"
  - "grpcio"
options:
  host:
    description:
      - Tiller's server host
    required: false
    default: "localhost"
  port:
    description:
      - Tiller's server port
    required: false
    default: 44134
  namespace:
    description:
      - Kubernetes namespace where the chart should be installed
    required: false
    default: "default"
  name:
    description:
      - Release name to manage
    required: false
    default: null
'''

RETURN = ''' # '''

EXAMPLES = '''
- name: Install helm chart
  helm:
    host: localhost
    chart:
      name: memcached
      version: 0.4.0
      source:
        type: repo
        location: https://kubernetes-charts.storage.googleapis.com
    state: installed
    name: my-memcached
    namespace: default

- name: Uninstall helm chart
  helm:
    host: localhost
    state: absent
    name: my-memcached
'''

import os
import yaml

from ansible.module_utils.basic import AnsibleModule


def main():
    """The main function."""
    module = AnsibleModule(
        argument_spec=dict(
            hieradata=dict(type='dict', default={}),
            hieradata_file=dict(type='str', default=''),
            schema=dict(type='dict'),
        ),
        supports_check_mode=True)

    schema = module.params['schema']
    hieradata = module.params['hieradata']
    hieradata_file = module.params['hieradata_file']

    if not (hieradata or hieradata_file):
        module.fail_json(msg="Either hieradata or hieradata_file must be set")

    if os.path.exists(hieradata_file):
        hieradata = yaml.safe_load(hieradata_file)

    conf_dict = {}
    for key, mapping in schema.items():
        if not key in hieradata:
            continue

        value = hieradata[key]

        group, name = mapping.split('.')
        conf_dict.setdefault(group, {})[name] = value

    module.exit_json(**{'conf_dict': conf_dict})


if __name__ == '__main__':
    main()
