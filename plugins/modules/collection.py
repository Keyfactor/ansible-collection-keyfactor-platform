#!/usr/bin/python

DOCUMENTATION = '''
---
module: collection

short_description: Create Collections.

version_added: "2.11"

description:
    - This module handles creating new or checking existing modules.
      Updating or deleting existing modules are not yet supported. We are looking
      to add these capabilities in the future. This module also currently supports check mode.

options:
    name:
        description:
            - Name of Collections Module (Needs to be unique).
        required: true
    description:
        description:
            - Description of Collections Module. Required if present
        required: false
    state:
        description:
        required: true
            - Whether the State should be present or absent
        choices: ["present", "absent"]
    query:
        description: Collections Query. Required if present or copy_from_id is not provided
        required: false
    src:
        description:
            - Name of the Virtual Directory, Default: KeyfactorAPI
    duplication_field:
        description: Duplication Field Option for Collections. Required if present
        required: false
        choices: [0,1,2,4]
            - 0 : None 
            - 1 : Common Name
            - 2 : Distinguished Name
            - 4 : Principal Name
    show_on_dashboard:
        description: Show on Dashboard.
        required: false
        default: false
    favorite:
        description: Show on Favorite list.
        required: false
        default: false
    copy_from_id:
        description: Id of the collection to be copied. Required if present or query is not provided
        required: False
        default: None

author:
    - Sulav Acharya (@sacharya-inf)
'''

EXAMPLES = '''
# Create a keyfactor collections
- name: Create a Collections in Keyfactor
  keyfactor.platform.collection:
    state: "present"
    name: "PodCollection"
    description: "Pod Collection"
    query: "CN -contains \"Pod Collection\""
    duplication_field: "0"
    show_on_dashboard: "true"
    favorite: "false"
- name: Create a Collections in Keyfactor
  keyfactor.platform.collection:
    state: "present"
    name: "PodCollection2"
    description: "Pod Collection Copied from Id"
    copy_from_id: "2"
    duplication_field: "0"
    show_on_dashboard: "false"
    favorite: "false"
'''

RETURN = '''
changed:
    description: Whether or not a change was made
    type: bool
    returned: always
msg:
    description: Message if an module does not get expected parameters
    type: str
    returned: sometimes
'''

from ansible_collections.keyfactor.platform.plugins.module_utils.core import AnsibleKeyfactorModule

def run_module():

    argument_spec = dict(
        name=dict(type='str', required=True),
        description=dict(type='str', required=False, default=''),
        state=dict(type='str', required=False, default=''),
        src=dict(type='str', required=False, default="KeyfactorAPI"),
        query=dict(type='str', required=False, default=''),
        duplication_field=dict(type='int', required=False, choices=[0,1,2,4], default=0),
        show_on_dashboard=dict(type='bool', required=False, default=False), 
        favorite=dict(type='bool', required=False, default=False),
        copy_from_id=dict(type='int', required=False, default=None),
    )

    mutually_exclusive_args = [["query", "copy_from_id"]]

    # seed the result dict in the object
    result = dict(
        changed=False
    )

    # Enable Suppot for Ansible Check-Mode
    module = AnsibleKeyfactorModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        result['changed'] = handleStateCheckMode(module)
        module.exit_json(**result)

    if module.params['state'] == 'absent':
        result['changed'] = handleStateAbsent(module)
    elif module.params['state'] == 'present':
        result['changed'] = handleStatePresent(module)

    module.exit_json(**result)

import json

def handleStateCheckMode(module):
    current = handleGet(module)
    if module.params['state'] == 'absent':
        # If something already exists the module will not delete it
        # If the does not exits then nothing will be changed.
        return False
    elif module.params['state'] == 'present':
        if current:
            # If the module currently exists then nothing will be changed
            return False
        # If the module does not exist then we create a new module
        return True

def handleStatePresent(module):
    current_state = handleGet(module)
    requested_state = createRequestedState(module)
    if current_state:
        if compareState(current_state, requested_state):
            return False
    return handleAdd(module, createRequestedState(module, True))

def createRequestedState(module, isPayload=False):
    # The Payload is different than the Requested State
    result = {
            "Name": module.params['name'], 
            "Description": module.params['description'],
            "Automated":False,
            "Query":module.params['query'],
            "DuplicationField":module.params['duplication_field'],
            "ShowOnDashboard":module.params['show_on_dashboard'],
            "Favorite":module.params['favorite'],
            "CopyFromId": module.params['copy_from_id'],
            }
    if not isPayload:
        result['Content'] = result.pop('Query')
        result.pop('CopyFromId')
        return result
    return result
        

def compareState(currentState, requestedState):
    for key, value in currentState.items():
        if str(key) in ('Id', 'src'):
            continue
        elif value != requestedState.get(str(key)):
            return False
    return True


def handleAdd(module, payload):
    url = module.params.get('src')
    endpoint = url+'/CertificateCollections/'
    resp, info = module.handleRequest("POST", endpoint, payload)
    try:
        content = resp.read()
        contentSet = json.loads(content)
        if (contentSet['Name']) == module.params['name']:
            return True
        module.fail_json(msg='Failed.')
    except Exception as e:
        content = info.pop('body', '')
        error = (json.loads(content)['ErrorCode'])
        if error == '0xA011000A':
            message = 'Unable to update the given module: ' + module.params['name'] + '\n This feature is in development.'
            module.fail_json(msg=message)
        module.fail_json(msg='Failed.')

def handleUpdate(module, payload):
    # Currently Not implemented
    pass

def handleStateAbsent(module):
    current = handleGet(module)
    if current:
        # If the given module is present there is current way to handle delete via the api
        message = 'Unable to delete the given module: ' + module.params['name'] + '\n This feature is in development.'
        module.fail_json(msg=message)
    return False

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

def main():
    run_module()

if __name__ == '__main__':
    main()