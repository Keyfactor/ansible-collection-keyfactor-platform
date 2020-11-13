#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

#TODO Update Documentation
DOCUMENTATION = '''
---
module: keyfactor_metadata_fields

short_description: Short description goes here.

version_added: "2.11"

description:
    - "Longer description goes here"

options:
    name:
        description:
            - Name of metadata field
        required: true
    description:
        description:
            - Description of metadata field.  Required if present
        required: false
    allow_api:
        description:
            - 

extends_documentation_fragment:
    - keyfactor

author:
    - David Fleming (@david_fleming)
'''

EXAMPLES = '''
# Create a metadata field
- name: Create a Metadata Field in Keyfactor
  keyfactor_metadata_fields:
    name: "PodName"
    description: "Pod Name"
    state: "present"
    allow_api: true
    data_type: 1

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
        description=dict(type='str', required=False),
        data_type=dict(type='int', required=True, choices=[1,2,3,4,5,6,7,8]),
        hint=dict(type='str', required=False),
        validation=dict(type='str', required=False),
        enrollment=dict(type='int', required=False, choices=[0,1,2]),
        options=dict(type='str', required=False),
        default_value=dict(type='str', required=False),
        explicit_update=dict(type='bool', required=False, default=False),
        allow_api=dict(type='bool', required=False),
        display_order=dict(type='int', required=False, default=0)
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
        module.exit_json(**result)

    if module.params['state'] == 'absent':
        result['changed'] = handleStateAbsent(module)
    elif module.params['state'] == 'present':
        result['changed'] = handleStatePresent(module)

    module.exit_json(**result)

import json

def checkMode(module):
    current = handleGet(module)
    if module.params['state'] == 'absent':
        if current:
            return True
        return False
    if module.params['state'] == 'present':
        if current:
            requestedState = createRequestedState(module)
            return compareState(current,requestedState)
        return True

def handleStatePresent(module):
    current = handleGet(module)
    request = createRequestedState(module)
    if 'Id' in current:
        if compareState(current, request):
            request['id'] = current['Id']
            return handleUpdate(module, request)
        return False
    return handleAdd(module, request)

def createRequestedState(module):
    return { 
        "Name": module.params['name'], 
        "Description": module.params['description'],
        "DataType":module.params['data_type'],
        "Hint":module.params['hint'],
        "Validation":module.params['validation'],
        "Enrollment":module.params['enrollment'],
        "Options":module.params['options'],
        "DefaultValue":module.params['default_value'],
        "ExplicitUpdate":module.params['explicit_update'],
        "AllowAPI":module.params['allow_api'],
        "DisplayOrder":module.params['display_order']
        }

def compareState(currentState, requestedState):
    for key, value in currentState.items():
        if key not in ('Id', 'Enrollment'):
            if (value == None and key not in requestedState):
                continue
            if value != requestedState[key]:
                return True
    return False

def handleAdd(module, payload):
    endpoint = '/Keyfactor/Api/MetadataFields'
    resp, info = module.handleRequest("POST", endpoint, payload)
    try:
        content = resp.read()
        contentSet = json.loads(content)
        if (contentSet['Name']) == module.params['name']:
            return True
        module.fail_json(msg='Failed.')
    except AttributeError:
        content = info.pop('body', '')
        message = (json.loads(content)['Message'])
        #"Metadata Field with Name 'Gym-Badge211b' already exists."
        if message == 'Cannot create Role because it already exist.':
            return False
        if message == 'Could not find user or Group.':
            module.fail_json(msg=message)
        module.fail_json(msg='Failed.')

def handleStateAbsent(module):
    current = handleGet(module)
    if 'Id' in current:
        return handleDelete(module, current['Id'])
    return False

def handleDelete(module, id):
    endpoint = ('/Keyfactor/API/MetadataFields/' + str(id))
    resp, info = module.handleRequest("DELETE", endpoint)
    status = info['status']
    if status in ( 200, 204 ):
        return True
    return False

def handleGet(module):
    endpoint = '/Keyfactor/API/MetadataFields/' + module.params['name']
    resp, info = module.handleRequest("GET", endpoint)
    try:
        content = resp.read()
        contentSet = json.loads(content)
        if (contentSet['Name']) == module.params['name']:
            return contentSet
        module.fail_json(msg='Unknown Error.')
    except AttributeError:
        
        content = info.pop('body', '')
        message = json.loads(content)['Message']
        if message == 'MetadataFieldType with Name \'' + module.params['name'] + '\' does not exist.':
            return {}
        module.fail_json(msg=message)

def handleUpdate(module, payload):
    endpoint = '/Keyfactor/API/MetadataFields/'

    resp, info = module.handleRequest("PUT", endpoint, payload)
    try:
        content = resp.read()
        contentSet = json.loads(content)
        if (contentSet['Name']) == module.params['name']:
            return True
        module.fail_json(msg='Unknown Error.')
    except AttributeError:
        
        content = info.pop('body', '')
        message = json.loads(content)['Message']
        module.fail_json(msg=message)

def main():
    run_module()

if __name__ == '__main__':
    main()