#!/usr/bin/python

DOCUMENTATION = '''
---
module: metadata_fields

short_description: Short description goes here.

version_added: "2.11"

description:
    - "Longer description goes here"

options:
    name:
        description:
            - Name of metadata field
        required: true
    src:
        description:
            - Name of the Virtual Directory, Default: KeyfactorAPI
        required: false
    description:
        description:
            - Description of metadata field.  Required if present
        required: false
    data_type:
        description:
            - Data type of the metadata field. Required if present
            - choices:
                - 0 : string
                - 1 : integer
                - 2 : datetime
                - 3 : boolean
                - 4 : multi-value
                - 5 : big text
                - 6 : ip address
                - 7 : binary
        required: false
    hint:
        description: 
            - Addition field to add hints
        required: false
    validation:
        description: 
            - Regular expression defination for the content
        required: false
    enrollment:
        description: Add enrollment handling states
            - choices:
                - 0: Optional
                - 1: Required
                - 2: Hidden
    options:
        description: 
            - Options for datatype 4, multiple choice
        required: false
    default:
        description:
            - Default value for the meta field
            - Not supported for data type 2 (datetime) & 5 (bigtext)
        required: false
    explicit_update:
        description:
            - Require flag in Legacy API to overwrite values. Default false
        required: false
    allow_api:
        description:
            - Allow Legacy API to get and set values. Default false
        required: false
    display_order:
        description:
            - Order in which the fields apprear. Default 0
        required: false

author:
    - David Fleming (@david_fleming)
'''

EXAMPLES = '''
# Create a metadata field
- name: Create a Metadata Field in Keyfactor
  keyfactor.platform.metadata_fields:
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

from ansible_collections.keyfactor.platform.plugins.module_utils.core import AnsibleKeyfactorModule

def run_module():

    argument_spec = dict(
        src=dict(type='str', required=False, default="KeyfactorAPI"),
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
        result['changed'] = checkMode(module)
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
    url = module.params.get('src')
    endpoint = url+'/MetadataFields/'
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
    url = module.params.pop('src')
    endpoint = url+'/MetadataFields/' + str(id)
    resp, info = module.handleRequest("DELETE", endpoint)
    status = info['status']
    if status in ( 200, 204 ):
        return True
    return False

def handleGet(module):
    url = module.params.get('src', None)
    endpoint = url+'/MetadataFields/' + module.params['name']
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
    url = module.params.get('src')
    endpoint = url+'/MetadataFields/'

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