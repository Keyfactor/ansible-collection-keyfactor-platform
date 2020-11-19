#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: keyfactor_identity

short_description: Manage Identities in Keyfactor

version_added: "2.11"

description:
    -  Module manages Identities in Keyfactor.
       Users can either add a new Keyfactor Identity or delete an existing Keyfactor Identity.
       Currently supports checkmode

options:
    name:
        description:
            - This is the Identity name.  (<domain>\<username>)
        required: true
    src:
        description:
            - Name of the Virtual Directory. Default: CMSAPI
        required: false
    state:
        description:
        required: true
            - Whether the State should be present or absent
        choices: ["present", "absent"]

extends_documentation_fragment:
    - keyfactor

author:
    - David Fleming (@david_fleming)
'''

EXAMPLES = '''
# Create Identity
- name: Create Identity in Keyfactor
  keyfactor_identity:
    name: "KEYFACTOR\\Test"
    state: 'present'
'''

RETURN = '''
changed:
    description: Whether or not a change was made
    type: bool
    returned: always
'''

from ansible.module_utils.keyfactor.core import AnsibleKeyfactorModule

def run_module():

    argument_spec = dict(
        src=dict(type='str', required=False, default="CMSAPI")
    )

    # seed the result dict in the object
    result = dict(
        changed=False
    )

    module = AnsibleKeyfactorModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        result['changed'] = checkMode(module)
        module.exit_json(**result)

    if module.params['state'] == 'absent':
        result['changed'] = handleDelete(module)
    elif module.params['state'] == 'present':
        result['changed'] = handleAdd(module)

    module.exit_json(**result)

import json


def checkMode(module):
    current = handleGet(module)
    # Since we do not update any parameter for an identity, a simple state check is
    # enough for checkMode.
    if module.params['state'] == 'absent':
        if current:
            return True
        return False
    if module.params['state'] == 'present':
        if current:
            return False
        return True

def handleAdd(module):
    url = module.params.pop('src')
    endpoint = url+'/Security/1/AddIdentity'
    payload = { "Account": module.params['name']}
    resp, info = module.handleRequest("POST", endpoint, payload)
    try:
        content = resp.read()
        if (json.loads(content)['Valid']) == True:
            return True
        module.fail_json(msg='Failed Add.')
    except AttributeError:
        content = info.pop('body', '')
        message = (json.loads(content)['Message'])
        if message == 'Cannot create Identity because it already exists.':
            return False
        if message == 'Could not find user or Group.':
            module.fail_json(msg=message)
        module.fail_json(msg='Failed Add Error.')

def handleDelete(module):
    url = module.params.pop('src')
    endpoint = url+'/Security/1/DeleteIdentity'
    payload = { "Account": module.params['name']}
    resp, info = module.handleRequest("POST", endpoint, payload)
    try:
        content = resp.read()
        if (json.loads(content)['Message']) == 'ADIdentity deleted successfully':
            return True
        module.fail_json(msg='Failed.')
    except AttributeError:
        content = info.pop('body', '')
        message = json.loads(content)['Message']
        if message == 'Can not delete Identity because it does not exist.':
            return False
        module.fail_json(msg='Failed.')

def handleGet(module):
    url = module.params.get('src')
    endpoint = url+'/Security/1/GetIdentities'
    resp, info = module.handleRequest("GET", endpoint)
    try:
        content = resp.read()
        contentSet = json.loads(content)
        collection = [collection_content for collection_content in contentSet if collection_content['AccountName'].lower() == module.params['name'].lower()]
        if collection:
            collection = next(iter(collection))
        return collection
        module.fail_json(msg='Failed.')
    except AttributeError:
        content = info.pop('body', '')
        message = json.loads(content)['Message']
        if message == 'Identity with Name \'' + module.params['name'] + '\' does not exist.':
            return {}
        module.fail_json(msg=message)

def main():
    run_module()

if __name__ == '__main__':
    main()