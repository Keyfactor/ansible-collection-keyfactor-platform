#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'keyfactor'
}

DOCUMENTATION = '''
---
module: keyfactor_certificate_store_type

short_description: This module is used to add, configure and delete keyfactor certificate store

version_added: "2.11"

description:
    - This module handles adding and updating store types on keyfactor.
    - The user only has to provide the name of the store they want to delete.
    - The user must provide proper list of job types
    - Multiple Choice is not available for Store Path Type. This maybe added in the future.
    - Reenrollment is not available for Job Types This maybe added in the future. 
    - Currently this module does not support checkmode.

options:
    name:
      description:
        - Name of Keyfactor Store Type
      required: true
    short_name:
      description:
        - Short Name of the Keyfactor Store Type. Required if state is present.
      required: false
    local_server:
      description:
        - Enable local server. Default false
      required: false
    allow_blueprint:
      description:
        - Enable allow blueprint setting. Default false
      required: false
    supports_entry_password;
      description:
        -  Enable  supports entry password. Default false
      required: false
    require_store_password:
        description:
            - Enable store password field. Default false
        required: false
    use_powershell:
        description:
            - Allow powershell usuage. Default false
        required: false
    custom_alias_support:
      description: Assign custom alias support. Default Forbidden
      choices;
        -'Forbidden'
        -'Optional'
        -'Required'
      required: false
    custom_alias_support:
      description: Assign custom alias support. Default Forbidden
      choices:
        -'Forbidden'
        -'Optional'
        -'Required'
      required: false
    store_path_type:
      description: Assign store path type. Default Freeform
      choices:
        -'Freeform'
        -'Fixed'
        -'Multiple Choice' Currently not supported.
      required: false
    store_path_fixed:
      description: Path for the Fixed Store Path Type Option. Required if Store path type is Fixed.
      required: false
    private_keys:
      description: Configure private keys field. Default Forbidden
      choices:
        -'Forbidden'
        -'Optional'
        -'Required'
      required: false
    pfx_password_style:
      description: Configure the PFX Password Style field.
      choices:
        - 'Default'
        - 'Custom'
      required: false
    job_types:
      description: Enable various job types for the cert store
      choices:
        - "Add"
        - "Create"
        - "Discovery"
        - "Remove"
        - "Reenrollment". Currently Not Supported
      required: false
    job_custom_fields:
      description: Add custom fields to the Store Type
      required: false
extends_documentation_fragment:
    - keyfactor

author:
    - Sulav Acharya (@sulavacharya-inf)
'''

EXAMPLES = '''

- name: Add & Update Keyfactor Store Type
    keyfactor_certificate_store_type:
      name: "PODSCS"
      short_name: "PDCS"
      local_server: False
      allow_blueprint: True
      require_store_password: True
      supports_entry_password: True
      custom_alias_support: "Required"
      use_powershell: True
      store_path_type: "Fixed"
      store_path_fixed: "abc"
      private_keys: "Required"
      pfx_password_style: "Custom"
      job_types:
        - "Add"
        - "Create"
        - "Discovery"
        - "Remove"
      job_custom_fields:
        - a
        - b
        - c
      state: present
- name: Delete Keyfactor Certificate Store Type
    keyfactor_certificate_store_type:
      name: "PODSCS"
      state: absent
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
        name=dict(type='str', required=True),
        src=dict(type='str', required=False, default="KeyfactorAPI"),
        short_name=dict(type='str', required=False),
        local_server=dict(type='bool', required=False, default=True),
        allow_blueprint=dict(type='bool', required=False, default=False),
        require_store_password=dict(type='bool', required=False, default=False),
        supports_entry_password=dict(type='bool', required=False, default=False),
        custom_alias_support=dict(type='str', required=False, default='Forbidden', choices=['Forbidden','Optional','Required']),
        pfx_password_style=dict(type='str', required=False, default='Default', choices=['Default', 'Custom']),
        private_keys=dict(type='str', required=False, default='Forbidden', choices=['Forbidden','Optional','Required']),
        use_powershell=dict(type='bool', required=False, default=False),
        store_path_type=dict(type='str', required=False, default='Freeform', choices=['Freeform','Fixed', 'Multiple Choice']),
        store_path_fixed=dict(type='str', required=False, default=''),
        store_path_choice=dict(type='list', required=False, default=[]),
        job_types=dict(type='list', required=False, default=[]),
        job_custom_fields=dict(type='list', required=False, default=[])
    )

    required_if_args = [
      ['state', 'present', ['short_name']],
      ['store_path_type', 'Multiple Choice', ['store_path_choice']],
      ['store_path_type', 'Fixed', ['store_path_fixed']]
      ]

    result = dict(
        changed=False
    )

    module = AnsibleKeyfactorModule(
        argument_spec=argument_spec,
        required_if=required_if_args,
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
    elif module.params['state'] == 'present':
        result['changed'] = handleStatePresent(module)
    module.exit_json(**result)


import json

def createPayload(module):
  payload =  {
    "Name": module.params.get("name"),
    "ShortName": module.params.get("short_name"),
    "LocalStore": module.params.get("local_server"),
    "BlueprintAllowed": module.params.get("allow_blueprint"),
    "PowerShell": module.params.get("use_powershell"),
    "PasswordOptions": {
      "EntrySupported":module.params.get("supports_entry_password"),
      "StoreRequired":module.params.get("require_store_password"),
      "Style":module.params.get("pfx_password_style"),
    },
    "CustomAliasAllowed": module.params.get("custom_alias_support"),
    "PrivateKeyAllowed": module.params.get("private_keys"),
    "JobProperties": module.params.get("job_custom_fields")
  }
  payload["SupportedOperations"] = handleSupportedOperations(module.params.get("job_types"))
  if module.params.get("store_path_type") == "Fixed":
    payload["StorePathType"] = module.params.get("store_path_fixed")
    payload["StorePathValue"] = module.params.get("store_path_fixed")
  if module.params.get("store_path_type") == "Multiple Choice":
    payload["StorePathType"] = module.params.get("store_path_choice")
    payload["StorePathValue"] = module.params.get("store_path_choice")
  else:
    payload["StorePathType"] = None
    payload["StorePathValue"] = None

  if module.params.get("local_server") != True:
    payload["ServerRequired"] = True
  else:
    payload["ServerRequired"] = False

  return payload

def handleSupportedOperations(options):
  options = [o.capitalize() for o in options]
  supported_types = {
    "Add": False,
    "Create": False,
    "Discovery": False,
    "Enrollment": False,
    "Remove": False
  }
  return {k:(True if k in options else v) for k,v in supported_types.items()}


def handleCheckMode(module):
  payload=createPayload(module)
  current = handleGet(module)
  if module.params.get("state") == "present":
    if current:
      return compareState(current, payload)
    return True
  elif module.params.get("state") == "absent":
    if current:
        return True
    return False

def createState(current):
  return {
          "Name": current.get("Name"),
          "ShortName": current.get("ShortName"),
          "LocalStore": current.get("LocalStore"),
          "SupportedOperations": current.get("SupportedOperations"),
          "PasswordOptions": current.get("PasswordOptions"),
          "StorePathType": current.get("StorePathType"),
          "StorePathValue": current.get("StorePathValue"),
          "PrivateKeyAllowed": current.get("PrivateKeyAllowed"),
          "JobProperties": current.get("JobProperties"),
          "ServerRequired": current.get("ServerRequired"),
          "PowerShell": current.get("PowerShell"),
          "BlueprintAllowed": current.get("BlueprintAllowed"),
          "CustomAliasAllowed": current.get("CustomAliasAllowed")
         }

def compareState(current, requested):
  current = createState(current)
  if current == requested:
      return True
  return False

def handleStateAbsent(module):
  current = handleGet(module)
  if current:
    return handleDelete(module, current.get("StoreType"))
  return False

def handleDelete(module, id):
    url = module.params.get('src')
    endpoint = url+'/CertificateStoreTypes/'+str(id)
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
            message = 'Unable to Delete Certificate Store Type.\n Error: '+ error + " \nMessage: " + message
            module.fail_json(msg=message)
        module.fail_json(msg='Failed.')

def handleStatePresent(module):
  current = handleGet(module)
  payload = createPayload(module)
  if current:
    if compareState(current, payload):
      return False
    payload["StoreType"] = current.get('StoreType')
    return handleUpdate(module, payload)
  return handleAdd(module, payload)

def handleAdd(module, payload):
    url = module.params.get('src')
    endpoint = url+'/CertificateStoreTypes/'
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
            message = 'Unable to add Certificate Store Types '+ error + " Message: " + message
            module.fail_json(msg=message)
        module.fail_json(msg='Failed.')

def handleUpdate(module, payload):
    url = module.params.get('src')
    endpoint = url+'/CertificateStoreTypes/'
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
            message = 'Unable to update Certificate Store Types '+ error + " Message: " + message
            module.fail_json(msg=message)
        module.fail_json(msg='Failed.')

def handleGet(module):
  url = module.params.get('src')
  endpoint = url+'/CertificateStoreTypes/'
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
      if message == 'Certificate Store Type with Name \'' + module.params['name'] + '\' does not exist.':
          return {}
      module.fail_json(msg=message)


def main():
    run_module()

if __name__ == '__main__':
    main()