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
import json

def run_module():

    argument_spec = dict(
        LogicalName=dict(type='str', required=True),
        HostName=dict(type='str', required=True),
        Delegate=dict(type='bool', required=False),
        ForestRoot=dict(type='str', required=True),
        Remote=dict(type='bool', required=False),
        Agent=dict(type='str', required=False),
        Standalone=dict(type='bool', required=False),
        MonitorThresholds=dict(type='bool', required=False),
        IssuanceMax=dict(type='int', required=False),
        IssuanceMin=dict(type='int', required=False),
        DenialMax=dict(type='int', required=False),
        FailureMax=dict(type='int', required=False),
        RFCEnforcement=dict(type='bool', required=False),
        Properties=dict(type='str', required=False),
        AllowedEnrollmentTypes=dict(type='int', required=False),
        KeyRetention=dict(type='int', required=False),
        KeyRetentionDays=dict(type='int', required=False),
        ExplicitCredentials=dict(type='bool', required=False),
        ExplicitUser=dict(type='str', required=False),
        UseAllowedRequesters=dict(type='bool', required=False),
        AllowedRequesters=dict(type='list', required=False)
        
    )

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
    
    createPayload(module)

    if module.params['state'] == 'absent':
        result['changed'] = handleStateAbsent(module)
    elif module.params['state'] == 'present':
        result['changed'] = handleStatePresent(module)

    module.exit_json(**result)

def createPayload(module):
    result = {}
    # file = open('scratch.txt', 'a')
    # file.write((str(module.params)))
    # file.close()
    for key, value in module.params.items():
        if key not in ('Id', 'headers'):
            result[key.capitalize()] = value
    return result

def createRequestedState(module):
    return createPayload(module)

def handleGet(module):
    endpoint = '/KeyfactorAPI/CertificateAuthority'
    try:
        resp, info = module.handleRequest("GET", endpoint)
        content = resp.read()
        contentSet = json.loads(content)
        return contentSet
    except AttributeError:
        content = info.pop('body', '')
        error = (json.loads(content)['ErrorCode'])
        if error == '0xA0130000':
            message = "No Certificate Authority was found."
            module.fail_json(msg=message)
        module.fail_json(msg='Failed.')

def handleCheck(module):
    contentSet = handleGet(module)
    try:
        collection = [collection_content for collection_content in contentSet if
                    (collection_content['HostName'] == module.params['HostName']
                    and collection_content['LogicalName'] == module.params['LogicalName']
                    and collection_content['ForestRoot'] == module.params['ForestRoot'])]
        if collection:
            collection = next(iter(collection))
        return collection
    except AttributeError:
        content = info.pop('body', '')
        error = (json.loads(content)['ErrorCode'])
        if error == '0xA0130000':
            message = "No Certificate Authority was found."
            module.fail_json(msg=message)
        module.fail_json(msg='Failed.')

def handleStatePresent(module):
    current = compareState(module)
    if module.params['HostName'] == current.get('HostName'):
        return handleUpdate(module)
    else:
        return handleAdd(module)

def handleAdd(module):
    endpoint = '/KeyfactorAPI/CertificateAuthority'
    payload = createPayload(module)
    resp, info = module.handleRequest("POST", endpoint, payload)
    try:
        content = resp.read()
        status = info['status']
        if status == 200:
            return True
    except AttributeError:
        status = info['status']
        content = info.pop('body', '')
        error = (json.loads(content)['ErrorCode'])
        if status != 200:
            message = 'The request was not successful'
            module.fail_json(msg=message)
        module.fail_json(msg='Failed.')

def handleStateAbsent(module):
    current = handleCheck(module)
    if current:
        return handleDelete(module)
    return False

def handleDelete(module):
    endpoint = '/KeyfactorAPI/CertificateAuthority/' + str(module.params['Id'])
    payload = createPayload(module)
    resp, info = module.handleRequest("DELETE", endpoint, payload)
    try:
        content = resp.read()
        status = info['status']
        if status == 204:
            return True
    except AttributeError:
        content = info.pop('body', '')
        error = (json.loads(content)['ErrorCode'])
        if error == '0xA0130000':
            return {}
        module.fail_json(msg='Failed.')
        
def compareState(module):
    lst = []
    lst2 = []
    dict3 = {}
    collection = handleCheck(module)
    payload = createPayload(module)
    file = open('scratch.txt', 'a')
    file.write(str(type(collection)))
    file.write(str(type(payload)))
    file.close()
    for key in collection.items():
        collection.items.encode('ascii')
    for key in payload.items():
        collection.items.encode('ascii')
    
    test = dict3(collection.items() - payload.items())

    file = open('scratch.txt', 'a')
    file.write((str(test)))
    file.close()
    file = open('scratch.txt', 'a')

def handleUpdate(module):
    endpoint = '/KeyfactorAPI/CertificateAuthority'
    payload = createPayload(module)
    resp, info = module.handleRequest("PUT", endpoint, payload)
    try:
        content = resp.read()
        status = info['status']
        if status == 200:
            return True
    except AttributeError:
        content = info.pop('body', '')
        error = (json.loads(content)['ErrorCode'])
        if error == '0xA0130000':
            message = 'Certificate Authority does not exist!'
            module.fail_json(msg=message)
        module.fail_json(msg='Failed.')

def main():
    run_module()

if __name__ == '__main__':
    main()