#!/usr/bin/python

DOCUMENTATION = '''
---
module: collection_permissions

short_description: This module is used to configure permissions for keyfactor collections

version_added: "2.11"

description:
    - This module handles adding and updating permissions on a specific collection for a given keyfactor role.
      The user will provide a keyfactor role_id and a list of appropriate permissions: Read, EditMetadata, Recover, Revoke and Delete 
      This permissions will be updating the existing permissions of that collection for the given keyfactor role.
      Currently this module does not support checkmode.


options:
    name:
        description:
            - Name of Keyfactor Collection
        required: true
    state:
        description:
            - Whether the Role should be Present or Absent
        required: true
    src:
        description:
            - Name of the Virtual Directory, Default: KeyfactorAPI
    role_id:
        description:
            - Primary Key Id for Keyfactor Role
        required: true
    permissions:
        description:
            - Set of permissions for the collection to have. Required only if the state is present
            - ['Read', 'EditMetadata', 'Recover', 'Revoke', 'Delete']
        required: false

author:
    - Sulav Acharya (@sulavacharya-inf)
'''

EXAMPLES = '''

# Remove Permissions from Keyfactor Collection
- name: Remove a Permission from Keyfactor Collection
  keyfactor.platform.collection_permissions:
      name: "Pod Collection"
      state: "absent"
      role_id: 2

- name: Add permissions to the Keyfactor Collection
  keyfactor.platform.collection_permissions:
      name: "Pod Collection"
      state: "present"
      role_id: 2
      permissions: ['Read', 'EditMetadata', 'Recover', 'Revoke', 'Delete']
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
        src=dict(type='str', required=False, default="KeyfactorAPI"),
        role_id=dict(type='int', required=True),
        permissions=dict(type='list', required=False, choices=['Read', 'EditMetadata', 'Recover', 'Revoke', 'Delete'], default=[]),
    )

    # seed the result dict in the object
    result = dict(
        changed=False
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


    isValid, current, msg = validate(module)
    if not isValid:
        module.fail_json(msg=msg)

    payload = create_payload(module)
    if module.params['state'] in ('absent', 'present'):
        result['changed'] = handleChange(module, payload, current.get(str('Id')))
    else:
        msg = 'Invalid state \"' + module.params['state'] + '\"'
        module.fail_json(msg=msg)

    module.exit_json(**result)

import json

def create_payload(module):
    # Create Payload for update
    return  [{
            "RoleId": module.params['role_id'],
            "Permissions": module.params['permissions']
            }]

def validate(module):
    current = handleGet(module)
    if not current:
        return False, {}, 'Certificate Collections with Name \'' + module.params['name'] + '\' does not exist.'
    else:
        if module.params['state'] == 'present':
            if module.params['permissions'] == []:
                return False, {}, 'Certificate Collections Permissions is required on state present'
        elif module.params['state'] == 'absent':
            if module.params['permissions'] != []:
                return False, {}, 'Certificate Collections Permissions must be empty on state absent'
        return True, current, ''

def handleGet(module):
    url = module.params.get('src', None)
    endpoint = url+'/CertificateCollections/'
    resp, info = module.handleRequest("GET", endpoint)
    try:
        content = resp.read()
        contentSet = json.loads(content)
        collection = [collection_content for collection_content in contentSet if collection_content['Name'] == module.params['name']]
        if collection:
            collection = next(iter(collection))
        return collection
    except AttributeError:
        content = info.pop('body', '')
        message = json.loads(content)['Message']
        if message == 'Certificate Collections with Name \'' + module.params['name'] + '\' does not exist.':
            return {}
        module.fail_json(msg=message)

def handleChange(module, payload, id):
    url = module.params.get('src')
    endpoint = url+'/CertificateCollections/'+str(id)+'/Permissions'
    resp, info = module.handleRequest("POST", endpoint, payload)
    try:
        status = info['status']
        if status in ( 200, 204 ):
            return True
        else:
            content = info.pop('body', '')
            message = json.loads(content)['Message']
            module.fail_json(msg=message)
    except AttributeError:
        content = info.pop('body', '')
        message = json.loads(content)['Message']
        module.fail_json(msg=message)

def main():
    run_module()

if __name__ == '__main__':
    main()