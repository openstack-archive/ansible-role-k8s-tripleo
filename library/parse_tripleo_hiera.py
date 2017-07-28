#!/usr/bin/env python

import os
import yaml

from ansible.module_utils.basic import AnsibleModule


DOCUMENTATION = '''
---
module: parse_tripleo_hiera
short_description: Translates hieradata into an oslo.config dict
version_added: "2.4"
author: "TripleO Team"
description:
   - Translates hieradata into an oslo.config dict
requirements:
options:
  hieradata:
    description:
      - A dictionary containing the hieradata
    required: false
    default: {}
  hieradata_file:
    description:
      - A path to an existing hieradata yaml file
    required: false
    default: ''
  schema:
    description:
      - Dictionary mapping a hiera key to an oslo.config group.name pair.
    required: true
'''

RETURN = ''' # '''

EXAMPLES = '''
- name: Test hieradata
  parse_tripleo_hiera:
    hieradata:
      glance::api::v1: True
    schema:
      glance::api::v1: DEFAULT.enable_glance_v1
  register: result


- name: Check values
  fail:
    msg: "DEFAULT not in conf_dict"
  when:
    - not result.conf_dict['DEFAULT']
    - not result.conf_dict['DEFAULT']['enable_glance_v1']


- name: Test include role
  include_role:
    name: 'ansible-role-k8s-tripleo'
  vars:
    hieradata:
      glance::api::v1: True
    schema:
      glance::api::v1: DEFAULT.enable_glance_v1
    fact_variable: 'glance_config'


- name: Check fact glance_config
  fail:
    msg: "glance_config not set"
  when:
    - not glance_config
'''


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

    if not (hieradata or (hieradata_file and os.path.exists(hieradata_file))):
        module.fail_json(msg="Either hieradata or hieradata_file must be set")

    if os.path.exists(hieradata_file):
        # NOTE(flaper87): This will load both, json and yaml, files
        hieradata = yaml.safe_load(open(hieradata_file))

    conf_dict = {}
    for key, mapping in schema.items():
        if key not in hieradata:
            continue

        value = hieradata[key]

        group, name = mapping.split('.')
        conf_dict.setdefault(group, {})[name] = value

    module.exit_json(**{'conf_dict': conf_dict})


if __name__ == '__main__':
    main()
