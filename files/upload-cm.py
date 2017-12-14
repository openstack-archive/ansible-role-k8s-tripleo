#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import argparse
import logging
import os

from kubernetes import client, config

LOG = logging.getLogger(__name__)
FORMAT = '%(asctime)s %(levelname)-8s %(name)-15s %(message)s'
logging.basicConfig(format=FORMAT)
LOG.setLevel(logging.INFO)


def get_args():
    description = 'Create and Update configmaps for dirs'
    parser = argparse.ArgumentParser(description)

    parser.add_argument('--debug', action='store_true',
                        dest='debug', help='Enable debug')
    parser.add_argument('--replace', action='store_true',
                        dest='cm_replace', help=('Replace existing ConfigMap. '
                                                 'Existing configmaps will be '
                                                 'patched otherwise.'))
    parser.add_argument('--cm-name', required=True,
                        dest='cm_name', help='Configmap name')
    parser.add_argument('--cm-namespace', required=True,
                        dest='cm_namespace', help='Configmap namespace')
    parser.add_argument('-d', '--dirs', action='append', default=[],
                        dest='dirs', help='Dirs to upload')
    parser.add_argument('-p', '--paths', action='append', default=[],
                        dest='paths', help='File to upload')
    args = parser.parse_args()
    return args


def main():
    args = get_args()

    if args.debug:
        LOG.setLevel(logging.DEBUG)

    try:
        config.load_incluster_config()
    except config.config_exception.ConfigException:
        config.load_kube_config()

    paths = args.paths[:]

    for d in args.dirs:
        for path in os.listdir(d):
            path = os.path.join(d, path)
            if os.path.isdir(path):
                LOG.info("Ignoring subdir %s: no recursion supported" % path)
                continue
            paths.append(path)

    data = {}
    for path in paths:
        path = os.path.abspath(path)

        if not os.path.exists(path):
            LOG.info("Ignoring path %s: It doesn't exist" % path)
            continue

        with open(path, 'r') as f:
            data[os.path.basename(path)] = f.read()
        LOG.debug("Read contents for %s" % path)

    metadata = {'name': args.cm_name,
                'namespace': args.cm_namespace}

    cm = client.V1ConfigMap()
    cm.metadata = metadata
    cm.data = data

    v1 = client.CoreV1Api()

    try:
        if args.cm_replace:
            cm = v1.replace_namespaced_config_map(args.cm_name,
                                                  args.cm_namespace,
                                                  body=cm)
            LOG.info("Configmap %s replaced" % args.cm_name)

        else:
            cm = v1.patch_namespaced_config_map(args.cm_name,
                                                args.cm_namespace,
                                                body=cm)
            LOG.info("Configmap %s updated" % args.cm_name)
    except client.rest.ApiException as exc:
        if not exc.status == 404:
            raise exc

        cm = v1.create_namespaced_config_map(args.cm_namespace, body=cm)
        LOG.info("Configmap %s created" % args.cm_name)


if __name__ == '__main__':
    main()
