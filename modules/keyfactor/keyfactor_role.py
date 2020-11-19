#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'keyfactor'
}

DOCUMENTATION = '''
---
module: keyfactor_role

short_description: This module is used to configure roles in Keyfactor Command

version_added: "2.11"

description:
    - "Add Keyfactor Role to a Keyfactor Identity"
    - "Assign Permission to the specific Keyfactor Role. Attached is the complete list of available permissions."
        - AgentAutoRegistrationModify
        - AgentAutoRegistrationRead
        - AgentManagementModify
        - AgentManagementRead
        - APIRead
        - AuditingRead
        - CertificateCollectionsModify
        - CertificateEnrollmentEnrollCSR
        - CertificateEnrollmentEnrollPFX
        - CertificateEnrollmentGenerateCSR
        - CertificateEnrollmentPendingCSR
        - CertificateMetadataTypesModify
        - CertificateMetadataTypesRead
        - Certificates_EditMetadata
        - Certificates_ImportPrivateKey,
        - CertificatesDelete,
        - CertificatesImport,
        - CertificatesRead,
        - CertificatesRecover,
        - CertificatesRevoke,
        - CertificateStoreManagementModify,
        - CertificateStoreManagementRead,
        - CertificateStoreManagementSchedule
        - DashboardRead
        - MacAutoEnrollManagementModify
        - MacAutoEnrollManagementRead
        - ManagementPortalRead
        - MonitoringModify
        - MonitoringRead
        - MonitoringTest
        - PKIManagementModify
        - PKIManagementRead
        - ReportsModify
        - ReportsRead
        - SecuritySettingsModify
        - SecuritySettingsRead
        - SSHEnterpriseAdmin
        - SSHServerAdmin
        - SSHUser
        - SSLManagementModify
        - SSLManagementRead
        - SystemSettingsModify
        - SystemSettingsRead
        - WorkflowModify
        - WorkflowParticipate
        - WorkflowRead
        - WorkflowTest"
    - "This module also supports check mode."

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
        required: false
    state:
        description:
            - Whether the role should be present or absent
        required: true

extends_documentation_fragment:
    - keyfactor

author:
    - David Fleming (@david_fleming)
'''
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
    current = handleGetMode(module)
    if module.params['state'] == 'absent':
        if current:
            return True
        return False
    if module.params['state'] == 'present':
        if current:
            return not compareState(current, module)
        return True

def createRequestedState(module):
    return { 
        "name": module.params['name'], 
        "description": module.params['description'],
        "identities": [i.capitalize() for i in module.params['identities']],
        "permissions": [i.capitalize() for i in module.params['permissions']],
        }

def compareState(current, module):
    requested = createRequestedState(module)
    # This could be an unordered list. Sets do not preserve order
    requested["identities"] = set(requested["identities"])
    requested["permissions"] = set(requested["permissions"])
    # Valid is currently unused
    current.pop('Valid')
    current = {k.lower():v for (k,v) in current.items()}
    # This could be an unordered list. Sets do not preserve order
    current["identities"] =  {i.encode('ascii').strip().capitalize() for i in current["identities"].split(',')}
    current["permissions"] =  {i.encode('ascii').strip().capitalize() for i in current["permissions"].split(',')}

    for key, value in requested.items():
        if value != current.get(str(key)):
            return False
    return True


def handleStatePresent(module):
    current = handleGetMode(module)
    if current:
        if compareState(current, module):
            return False  
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
    current = handleGetMode(module)
    if current:
        return handleDelete(module)
    return False

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

def handleGetMode(module):
    url = module.params.get('src')
    endpoint = url+'/Security/1/GetRoles'
    resp, info = module.handleRequest("GET", endpoint)
    try:
        content = resp.read()
        contentSet = json.loads(content)
        collection = [collection_content for collection_content in contentSet if collection_content['Name'] == module.params['name']]
        if collection:
            collection = next(iter(collection))
        return collection
        module.fail_json(msg='Failed.')
    except AttributeError:
        content = info.pop('body', '')
        message = json.loads(content)['Message']
        if message == 'Role with Name \'' + module.params['name'] + '\' does not exist.':
            return {}
        module.fail_json(msg=message)

def main():
    run_module()

if __name__ == '__main__':
    main()