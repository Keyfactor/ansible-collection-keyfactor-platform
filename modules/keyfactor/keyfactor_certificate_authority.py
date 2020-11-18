#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'keyfactor'
}

DOCUMENTATION = '''
---
module: keyfactor_certificate_authority

short_description: This module is used to configure certificate authorities in the Keyfactor Command

version_added: "2.11"

description:
    - "Using this module, a user is able to create or delete a certificate authority."
    - "Currently the Full Scan & Incremental Scan Settings are not configurable though this ansible module. This maybe added in the future."
    - "Currently the ExplicitCredentials settings are not configurable through this ansible module. This maybe added in the future."
    - "This module supports ansible check mode."

options:
    name:
        description:  
            - "Logical Name of the Certificate Authority."
        required: true
    host_name:
        description:  
            - "Host Name of the Certificate Authority."
        required: true
    forest_root:
        description:  
            - "Template Forest of the Certificate Authority."
        required: true
    allowed_enrollment_types:
        description:
            - "Enable PFX or CSR enrollment." Default is 0
        choices:
            - 0: Both PFX & CSR Enrollment are turned off.
            - 1: Only PFX Enrollment is turned on.
            - 2: Only CSR Enrollment is turned on.
            - 3: Both PFX & CSR Enrollment are turned on.
        required: false
    rfc_enforcement:
        description: 
            - "Enforce RFC 2818 Complicance." Default is 0
        required: false
    standalone:
        description: 
            - "Enable the StandAlone feature for this CA." Default is False
        required: false
    orchestrator:
        description:
            - "Set CA as a remote orchestrator. Provide the Agent Id"
        required: false
    key_retention:
        description:
            - "Add key retention to the CA. Default is 0"
        required: false
        choices:
            - 0: Turn off Key Retention
            - 1: Indifinite
            - 2: After Expiration
            - 3: From Issuance
    key_retention_days:
        description:
            - "Provide the number of days for key retention."
            - "If Key Retention is turned off, the key retention is set to Null"
        required: false
    monitor:
        description:
            - "Enable CA Monitoring."
        required: false
    issuance_max:
        description:
            - "Set Issurance Greater than value." Default: None
            - "Required if Monitor is true."
        required: false
    issuance_min:
        description:
            - "Set Issurance Less than value." Default: None
            - "Required if Monitor is true."
        required: false
    denial_max:
        description:
            - "Set Failures Greater than value." Default: None
            - "Required if Monitor is true."
        required: false
    failure_max:
        description:
            - "Set Denials Greater than value." Default: None
            - "Required if Monitor is true."
        required: false
    delegate:
        description:
            - "Delegate Management Operation." Default: False
        required: false
    use_allowed_requesters:
        description:
            - "Ristrict Allowed Requesters." Default: False
        required: false
    allowed_requesters:
        description:
            - "Allowed Requesters Security Roles." Default: []
        required: false
    src:
        description:
            - Name of the Virtual Directory, Default: KeyfactorAPI
        required: false
    state:
        description:
            - Whether the role should be present or absent
        required: true

extends_documentation_fragment:
    - keyfactor

author:
    - Anthony Batlouni (@abatlouni-inf)
'''

EXAMPLES = '''
# Create a test role and description with permission APIRead and assign to identity KEYFACTOR\\Test
- name: Create Keyfactor CA 
    keyfactor_certificate_authority:
      name: PodCA
      host_name: PodCA_HostName
      forest_root: PodCA_ForestName
      allowed_enrollment_types: 3
      sync_external_certificates: true
      standalone: true
      rfc_enforcement: false
      key_retention: 1
      key_retention_days: 50
      monitor: true
      issuance_max: 6
      issuance_min: 2
      denial_max: 1
      failure_max: 2
      use_allowed_requesters: true
      allowed_requesters:
        - "AnsibleTestRole"
      state: 'present'
  - name: Delete Keyfactor CA 
    keyfactor_certificate_authority:
      name: PodCA
      host_name: PodCA_HostName
      forest_root: PodCA_ForestName
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
        name=dict(type='str', required=True),
        host_name=dict(type='str', required=True),
        forest_root=dict(type='str', required=True),
        src=dict(type='str', required=False, default="KeyfactorAPI"),
        allowed_enrollment_types=dict(type='int', required=False, default=0, choices=[0,1,2,3]),
        sync_external_certificates=dict(type='bool', required=False, default=False),
        rfc_enforcement=dict(type='bool', required=False, default=False),
        standalone=dict(type='bool', required=False, default=False),
        orchestrator=dict(type='str', required=False, default=None),
        key_retention=dict(type='int', required=False, default=0, choices=[0,1,2,3]),
        key_retention_days=dict(type='int', required=False, default=None),
        monitor=dict(type='bool', required=False, default=False),
        issuance_max=dict(type='int', required=False, default=None),
        issuance_min=dict(type='int', required=False, default=None),
        denial_max=dict(type='int', required=False, default=None),
        failure_max=dict(type='int', required=False, default=None),
        delegate=dict(type='bool', required=False, default=False),
        use_allowed_requesters=dict(type='bool', required=False, default=False),
        allowed_requesters=dict(type='list', required=False, default=[]),
    )

    mutually_exclusive_args = [["orchestrator", "monitor"]]

    result = dict(
        changed=False
    )

    module = AnsibleKeyfactorModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        result['changed'] = handleCheckMode(module)
        module.exit_json(**result)

    if module.params['state'] == 'absent':
        result['changed'] = handleStateAbsent(module)
        pass
    elif module.params['state'] == 'present':
        result['changed'] = handleStatePresent(module)
    else:
        msg = "Module Does Not Support State: " + module.params["state"]
        module.fail_json(msg=msg)

    module.exit_json(**result)

def createPayload(module):
    payload = {
        "LogicalName": module.params["name"],
        "HostName": module.params["host_name"],
        "ForestRoot": module.params["forest_root"],
        "AllowedEnrollmentTypes": module.params["allowed_enrollment_types"],
        "RFCEnforcement": module.params["rfc_enforcement"],
        "Standalone": module.params["standalone"],
        "Properties": "{\"syncExternal\":false}",
        "Remote": False,
        "Agent": module.params["orchestrator"],
        "KeyRetention": module.params["key_retention"],
        "KeyRetentionDays": module.params["key_retention_days"],
        "MonitorThresholds": module.params["monitor"],
        "IssuanceMax": module.params["issuance_max"],
        "IssuanceMin": module.params["issuance_min"],
        "DenialMax": module.params["denial_max"],
        "FailureMax": module.params["failure_max"],
        "UseAllowedRequesters": module.params["use_allowed_requesters"],
        "AllowedRequesters": module.params["allowed_requesters"],
        "Delegate": module.params["delegate"]
    }
    if module.params.get("sync_external_certificates"):
        payload["Properties"] = "{\"syncExternal\":true}"
    if module.params.get("orchestrator"):
        payload["Remote"] = True
    if module.params.get("key_retention") in (0, 1):
        payload["KeyRetentionDays"] = None
    if module.params.get("monitor") != False:
        if not all([
            module.params.get("issuance_max"),
            module.params.get("issuance_min"),
            module.params.get("denial_max"),
            module.params.get("failure_max"),
            ]):
            msg = "Please provide proper values for issuance_max, issuance_min, denial_max, failure_max."
            module.fail_json(msg=msg)
        elif module.params.get("issuance_min") > module.params.get("issuance_max"):
            msg = "Issuance Less Than: \"Greater Than\" threshold cannot be smaller than \"Less Than\" threshold"
            module.fail_json(msg=msg)
    else:
        payload["IssuanceMax"] = None
        payload["IssuanceMin"] = None
        payload["DenialMax"] = None
        payload["FailureMax"] = None
    if not module.params.get("use_allowed_requesters"):
        payload["AllowedRequesters"] = []
    return payload

def handleCheckMode(module):
    requested = createPayload(module)
    current = handleGet(module)
    if module.params["state"] == "present":
        if current:
            return compareState(current, requested)
        return True
    elif module.params["state"] == "absent":
        if current:
            return True
        return False

def createState(current):
    return {
            "LogicalName": current.get("LogicalName"),
            "HostName": current.get("HostName"),
            "ForestRoot": current.get("ForestRoot"),
            "AllowedEnrollmentTypes": current.get("AllowedEnrollmentTypes"),
            "RFCEnforcement": current.get("RFCEnforcement"),
            "Standalone": current.get("Standalone"),
            "Properties": current.get("Properties"),
            "Remote": current.get("Remote"),
            "Agent": current.get("Agent"),
            "KeyRetention": current.get("KeyRetention"),
            "KeyRetentionDays": current.get("KeyRetentionDays"),
            "MonitorThresholds": current.get("MonitorThresholds"),
            "IssuanceMax": current.get("IssuanceMax"),
            "IssuanceMin": current.get("IssuanceMin"),
            "DenialMax": current.get("DenialMax"),
            "FailureMax": current.get("FailureMax"),
            "Delegate": current.get("Delegate"),
            'UseAllowedRequesters': current.get("UseAllowedRequesters"),
            "AllowedRequesters": current.get("AllowedRequesters"),
           }

def compareState(current, requested):
  current = createState(current)
  for k,v in current.items():
    if v != requested.get(k):
      return False
  return True

def handleStatePresent(module):
    current = handleGet(module)
    payload=createPayload(module)
    if current:
        if compareState(current, payload):
            return False
        payload["Id"] = current.get('Id')
        return handleUpdate(module, payload)
    return handleAdd(module, payload)

def handleStateAbsent(module):
    current = handleGet(module)
    if current:
        return handleDelete(module, current.get("Id"))
    return False

def handleDelete(module, id):
    url = module.params.get('src')
    endpoint = url+'/CertificateAuthority/'+str(id)
    resp, info = module.handleRequest("DELETE", endpoint)
    try:
        content = resp.read()
        status = info['status']
        if status == 204:
            return True
    except AttributeError:
        status = info['status']
        content = info.pop('body', '')
        error = (json.loads(content)['ErrorCode'])
        message = (json.loads(content)['Message'])
        if error:
            message = 'Unable to Delete Certificate Authority '+ error + " Message: " + message
            module.fail_json(msg=message)
        module.fail_json(msg='Failed.')

def handleAdd(module, payload):
    url = module.params.get('src')
    endpoint = url+'/CertificateAuthority/'
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
        message = (json.loads(content)['Message'])
        if error:
            message = 'Unable to add Certificate Authority '+ error + " Message: " + message
            module.fail_json(msg=message)
        module.fail_json(msg='Failed.')

def handleUpdate(module, payload):
    url = module.params.get('src')
    endpoint = url+'/CertificateAuthority/'
    resp, info = module.handleRequest("PUT", endpoint, payload)
    try:
        content = resp.read()
        status = info['status']
        if status == 200:
            return True
    except AttributeError:
        status = info['status']
        content = info.pop('body', '')
        error = (json.loads(content)['ErrorCode'])
        message = (json.loads(content)['Message'])
        if error:
            message = 'Unable to update Certificate Authority '+ error + " Message: " + message
            module.fail_json(msg=message)
        module.fail_json(msg='Failed.')


def handleGet(module):
    url = module.params.get('src')
    endpoint = url+'/CertificateAuthority/'
    resp, info = module.handleRequest("GET", endpoint)
    try:
        content = resp.read()
        contentSet = json.loads(content)
        collection = [collection_content for collection_content in contentSet if
                        (collection_content['HostName'] == module.params['host_name']
                        and collection_content['LogicalName'] == module.params['name']
                        and collection_content['ForestRoot'] == module.params['forest_root'])]
        if collection:
            collection = next(iter(collection))
        return collection
    except AttributeError:
        content = info.pop('body', '')
        message = json.loads(content)['Message']
        if message == 'Certificate Authority with Logical \'' + module.params['name'] + '\' does not exist.':
            return {}
        module.fail_json(msg=message)


def main():
    run_module()

if __name__ == '__main__':
    main()