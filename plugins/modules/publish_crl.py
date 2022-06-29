#!/usr/bin/python

DOCUMENTATION = '''
---
module: publish_crl

short_description: This module allows users to publish crls for a specific certificate authority.

version_added: "2.11"

description:
    - "Given Host and logical name of the CA, this module will publish the CRL."
    - "Currently, this module does not support check mode."

options:
    name:
        description:
            - Logical name of the CA for which the CRL should be published.
        required: true
    hostName :
        description:
            - Host Name of the CA for which the CRL should be published.
        required: true
    src:
        description:
            - Name of the Virtual Directory, Default: KeyfactorAPI

author:
    - David Fleming (@david_fleming)
'''

EXAMPLES = '''
- name: Publish a CRL from a CA
  keyfactor.platform.publish_crl:
    name: "CA01"
    hostName: "SubCA01"
'''

RETURN = '''
changed:
    description: Whether or not a change was made
    type: bool
    returned: always
'''

from ansible_collections.keyfactor.platform.plugins.module_utils.core import AnsibleKeyfactorModule

def run_module():
    argument_spec = dict(
        name=dict(type='str', required=True),
        hostname=dict(type='str', required=False),
        src=dict(type='str', required=False, default='KeyfactorAPI'),
    )

    result = dict(
        changed=False
    )

    module = AnsibleKeyfactorModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    result['changed'] = handlepublish(module)

    module.exit_json(**result)


def createPayload(module):
    return {
             "CertificateAuthorityLogicalName": module.params.get("name"),
             "CertificateAuthorityHostName": module.params.get("hostname")
           }

def handlepublish(module, payload):
    url = module.params.get("src", None)
    endpoint = url+'/CertificateAuthority/PublishCRL' 
    payload = createPayload(module)

    resp, info = module.handleRequest("POST", endpoint, payload)
    try:
        content = resp.read()
        contentSet = json.loads(content)
        status = info['status']
        if status in ( 200, 204 ):
            return True
        elif status is 400:
            content = info.pop('body', '')
            contentSet = json.loads(content)
            message = contentSet.get('Message', '')
            error = contentSet.get('ErrorCode', '')
            msg = 'Error: '+ error + '\n Message: '+ message
            module.fail_json(msg=msg)
            return False
        module.fail_json(msg='Unknown Error.')
    except AttributeError:
        content = info.pop('body', '')
        message = json.loads(content)['Message']
        module.fail_json(msg=message)

def main():
    run_module()

if __name__ == '__main__':
    main()