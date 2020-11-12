#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'keyfactor'
}

#TODO Update Documentation
DOCUMENTATION = '''
---
module: keyfactor_role

short_description: This module is used to configure roles in Keyfactor Command

version_added: "2.11"

description:
    - "TODO:"

options:
    name:
        description:
            - Name of Role
        required: true
    description:
        description:
            - Description of Role
        required: true
    src:
        description:
            - Name of the Virtual Directory. Default: CMSAPI
        required: true
    state:
        description:
            - Whether the role should be present or absent
        required: true

extends_documentation_fragment:
    - keyfactor

author:
    - David Fleming (@david_fleming)
'''
#TODO Update Examples
EXAMPLES = '''

# Create a test role and description with permission APIRead and assign to identity KEYFACTOR\\Test
- name: Create a Role in Keyfactor
  keyfactor_role:
    name: "AnsibleTestRole"
    description: "AnsibleTestRoleDescription"
    state: 'present'
    permissions:
    - 'APIRead'
    identities: 
    - "KEYFACTOR\\Test"

- name: Delete a Role in Keyfactor
  keyfactor_role:
    name: "AnsibleTestRole"
    state: 'absent'

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
        description=dict(type='str', required=True),
        src=dict(type='str', required=False, default="CMSAPI"),
        identities=dict(type='list', required=False, default=[]),
        permissions=dict(type='list', required=False, default=[])
    )

    # seed the result dict in the object
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    module = AnsibleKeyfactorModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    if module.params['state'] == 'absent':
        result['changed'] = handleStateAbsent(module)
    elif module.params['state'] == 'present':
        result['changed'] = handleStatePresent(module)

    module.exit_json(**result)

import json

def handleStatePresent(module):
    current = handleGet(module)
    if 'Valid' in current:
        # TODO: compare to see if edit is needed, return false if not
        return handleUpdate(module)
    return handleAdd(module)

def handleAdd(module):
    url = module.params.pop('src')
    endpoint = url+'/Security/1/AddRole'
    payload = { 
        "name": module.params['name'], 
        "description": module.params['description'], 
        "identities":module.params['identities'],
        "permissions":module.params['permissions']
        }
    resp, info = module.handleRequest("POST", endpoint, payload)
    try:
        content = resp.read()
        if (json.loads(content)['Valid']) == True:
            return True
        module.fail_json(msg='Failed.')
    except AttributeError:
        content = info.pop('body', '')
        message = (json.loads(content)['Message'])
        if message == 'Cannot create Role because it already exist.':
            return False
        if message == 'Could not find user or Group.':
            module.fail_json(msg=message)
        module.fail_json(msg='Failed.')

def handleStateAbsent(module):
    return handleDelete(module)

def handleDelete(module):
    url = module.params.pop('src')
    endpoint = url+'/Security/1/DeleteRole'
    payload = { "name": module.params['name']}
    resp, info = module.handleRequest("POST", endpoint, payload)
    try:
        content = resp.read()
        if (json.loads(content)['Message']) == ('Successfully deleted Role: ' + module.params['name']):
            return True
        module.fail_json(msg='Failed.')
    except AttributeError:
        
        content = info.pop('body', '')
        message = json.loads(content)['Message']
        if message == 'Cannot delete Role because it does not exist.':
            return False
        module.fail_json(msg='Failed.')

def handleGet(module):
    url = module.params.get('src', None)
    endpoint = url+'/Security/1/EditRole'
    payload = { "name": module.params['name']}
    resp, info = module.handleRequest("POST", endpoint, payload)
    try:
        content = resp.read()
        contentSet = json.loads(content)
        if (contentSet['Valid']) == True:
            return contentSet
        module.fail_json(msg='Unknown Error.')
    except AttributeError:
        
        content = info.pop('body', '')
        message = json.loads(content)['Message']
        if message == 'Cannot edit Role because it does not exist.':
            return {}
        module.fail_json(msg=message)

def handleUpdate(module):
    #"Cannot edit Role because it does not exist."
    url = module.params.pop('src')
    endpoint = url+'/Security/1/EditRole'
    payload = { 
        "name": module.params['name'], 
        "description": module.params['description'],
        "identities":module.params['identities'],
        "permissions":module.params['permissions']
        }
    resp, info = module.handleRequest("POST", endpoint, payload)
    try:
        content = resp.read()
        contentSet = json.loads(content)
        if (contentSet['Valid']) == True:
            return True
        module.fail_json(msg='Unknown Error.')
    except AttributeError:
        
        content = info.pop('body', '')
        message = json.loads(content)['Message']
        if message == 'Cannot edit Role because it does not exist.':
            return False
        module.fail_json(msg=message)


def main():
    run_module()

if __name__ == '__main__':
    main()