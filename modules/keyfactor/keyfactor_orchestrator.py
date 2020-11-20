#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'keyfactor'
}

DOCUMENTATION = '''
---
module: keyfactor_orchestrator

short_description: Approve/Disapprove Orchestrators in Keyfactor

version_added: "2.11"

description:
    - "Module manages Orchestrators in Keyfactor.  When orchestrators first appear in Keyfactor Command, they have a status of New. The orchestrator cannot perform any jobs while it has this status.  Once approved an orchestrator can be scheduled jobs.  An orchestrator can be disapproved to cancel any existing jobs and prevent it from being scheduled any further jobs."

options:
    name:
        description:
            - This is the name of the orchestrator.  The name in combination with the platform is used to uniquely identify an orchestrator.
        required: true
    src:
        description:
            - Name of the Virtual Directory. Default: KeyfactorPortal
        required: false
    platform:
        description:
            - This is the numeric value representing the platform the orchestrator belongs to (0 - Unknown, 1 - .Net, 2 - Java, 3 - Mac, 4 - Android, 5 - Native)
        choices: [0, 1, 2, 3, 4, 5]
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
# Approve Orchestrator
- name: Approve .Net Orchestrator
  keyfactor_orchestrator:
    name: "kftest.keyfactor.lab"
    platform: 1
    state: 'present'
# Disapprove Orchestrator
- name: Disapprove Java Orchestrator
  keyfactor_orchestrator:
    name: "kftest.keyfactor.lab"
    platform: 2
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
        # TODO: capabilities match
        # capabilities=dict(type='list', required=False, default=[]),
        platform=dict(type='int', required=True),
        src=dict(type='str', required=True, default="KeyfactorPortal")
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

    headers = {}
    headers["X-Requested-With"] = "XMLHttpRequest"
    headers["Content-Type"] = "application/json"
    module.params['headers'] = headers

    if module.params['state'] == 'absent':
        result['changed'] = handleStateAbsent(module)
    elif module.params['state'] == 'present':
        result['changed'] = handleStatePresent(module)

    module.exit_json(**result)

import json

def handleStatePresent(module):
    current = handleGet(module)
    if(current['id']):
        id = current['id']
        platform = current['cell'][2]
        status = current['cell'][4]
        capabilities = current['cell'][6]
        if(status=="Approved"):
            return False

        return handleApprove(module, id)
    return False

def handleStateAbsent(module):
    current = handleGet(module)
    if(current['id']):
        id = current['id']
        platform = current['cell'][2]
        status = current['cell'][4]
        capabilities = current['cell'][6]
        if(status=="Disapproved"):
            return False

        return handleDisapprove(module, id)
    return False

def handleApprove(module, id):
    url = module.params.get('src')
    endpoint = url+'Agent/Approve'
    payload = { 
        "agentIds": [id]
    }
    resp, info = module.handleRequest("POST", endpoint, payload)
    try:
        content = resp.read()
        if (json.loads(content)['success']) == True:
            return True
        module.fail_json(msg='Failed.')
    except AttributeError:
        content = info.pop('body', '')
        message = (json.loads(content)['Message'])
        module.fail_json(msg=content)


def handleDisapprove(module, id):
    url = module.params.get('src')
    endpoint = url+'Agent/Disapprove'
    payload = { 
        "agentIds": [id]
    }
    resp, info = module.handleRequest("POST", endpoint, payload)
    try:
        content = resp.read()
        if (json.loads(content)['success']) == True:
            return True
        module.fail_json(msg='Failed.')
    except AttributeError:
        content = info.pop('body', '')
        module.fail_json(msg=content)

def handleGet(module):
    url = module.params.get('src', None)
    endpoint = url+'/Agent/List'
    payload = { 
        "query": "ClientMachine -eq \"" + module.params['name'] + "\" AND Platform -eq \"" + str(module.params['platform']) + "\"",
        "page": 1,
        "rp": 20,
        "sortname": "name",
        "sortorder": "asc"
        }

    resp, info = module.handleRequest("POST", endpoint, payload)
    try:
        content = resp.read()
        contentSet = json.loads(content)
        if (contentSet['total']) == 1:
            return contentSet['rows'][0]
        return {}
    except AttributeError:
        content = info.pop('body', '')
        module.fail_json(msg=content)

def main():
    run_module()

if __name__ == '__main__':
    main()