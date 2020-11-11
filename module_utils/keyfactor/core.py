from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.urls import fetch_url, url_argument_spec

import os
import json

class AnsibleKeyfactorModule(AnsibleModule):
    def __init__(self, *args, **kwargs):
        __updateSpec__(kwargs.get('argument_spec'))
        AnsibleModule.__init__(self, *args, **kwargs)
        self.__env_fallback__()

    def __env_fallback__(self):
        if (self.params['url_password'] == None):
            self.params['url_password'] = os.environ.get('KEYFACTOR_PASSWORD')

        if (self.params['url_username'] == None):
            self.params['url_username'] = os.environ.get('KEYFACTOR_USER')

        if (self.params['url'] == None):
            self.params['url'] = os.environ.get('KEYFACTOR_ADDR')

        if (self.params.get('ca_path') == None):
            self.params['ca_path'] = os.environ.get('CERTICATE_STORE_PATH')

        if (os.environ.get('KEYFACTOR_IGNORE_SSL') != None):
            self.params['validate_certs'] = False

    def handleRequest(self, method, endpoint, payload={}):
        socket_timeout = self.params['timeout']
        # allow additional headers to be passed in
        dict_headers = self.params['headers']
        dict_headers['Content-Type'] = 'application/json'
        dict_headers['X-Keyfactor-Requested-With'] = 'APIClient'
        url = self.params['url'] + endpoint
        ca_path = self.params.get('ca_path', None)
        
        body = json.dumps(payload)
        resp, info = fetch_url(self, url, data=body,
            headers=dict_headers,
            method=method,
            timeout=socket_timeout,
            unix_socket=None,
            ca_path=ca_path)
        status = info['status']
        if status in ( 401, 403 ):
            return self.fail_json(msg='Authentication failed.')
        return resp, info
    
def __updateSpec__(argument_spec):
    argument_spec.update(url_argument_spec())
    argument_spec.update(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        url_username=dict(type='str', aliases=['user'], required=False),
        url_password=dict(type='str', aliases=['password'], required=False, no_log=True),
        url=dict(type='str', required=False),
        timeout=dict(type='int', default=30),
        headers=dict(type='dict', default={}),
        force_basic_auth=dict(type='bool', required=False, default=True)
    )

