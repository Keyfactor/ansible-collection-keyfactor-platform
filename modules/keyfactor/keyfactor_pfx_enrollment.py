#!/usr/bin/python

DOCUMENTATION = '''
---
module: keyfactor_pfx_enrollment

short_description: Request Enrollment for PFX Certificate in Keyfactor

version_added: "2.12"

description:
    - "This module will submit an enrollment request to Keyfactor for a new certificate. It creates a PFX enrollment request with the specified certificate contents. This enrollment method does not require a CSR is generated beforehand."

options:
    name:
        description: Optional friendly name for the certificate
        type: str
    subject:
        description: Subject for the certificate
        required: true
        type: str
    template:
        description: Template Short Name in Keyfactor
        required: true
        type: str
    pfx_password:
        description: Set the PFX password manually
        required: false
        type: str
    ca:
        description: Certificate authority
        type: str
    cert_chain:
        description: Whether or not to include the full certificate chain in the downloaded PFX
        type: bool
        default: true
    values_from_ad:
        description: Whether or not to populate missing fields from Active Directory
        type: bool
        default: false
    vdir:
        description:
            - Name of the API Virtual Directory. 
            - Default: KeyfactorAPI
        type: str
    metadata:
        description: Values for pre-defined certificate metadata fields
        type: dict
    additional_fields:
        description: Special enrollment fields to include in the enrollment request
        type: dict
    sans:
        description:
            - List of Subject Alternative Names to include on the certificate
        type: dict
        suboptions: 
            other:
                description: OtherName
                type: list
            rfc822:
                description: RFC822Name
                type: list
            dns:
                description: DNSName
                type: list
            x400:
                description: X400Address
                type: list
            directory:
                description: DirectoryName
                type: list
            ediparty:
                description: EdipartyName
                type: list
            uri:
                description: UniformResourceIdentifier
                type: list
            ip:
                description: IPAddress
                type: list
            ip4:
                description: IPv4Address
                type: list
            ip6:
                description: IPv6Address
                type: list
            registeredid:
                description: RegisteredId
                type: list
            ms_ntprincipalname:
                description: MS_NTPrincipalName
                type: list
            ms_ntdsreplication:
                description: MS_NTDSReplication
                type: list

extends_documentation_fragment:
    - keyfactor

author:
    - Matt Dobrowsky (@doebrowsk)
'''

EXAMPLES = '''
TODO
'''

RETURN = '''
pfx_certificate:
    description: Enrolled certificate content
    type: str
    returned: success
pfx_password:
    description: PFX Password for the enrolled certificate
    type: str
    returned: success
certificate_id:
    description: Certificate ID in Keyfactor
    type: int
    returned: success
'''

from json import json
from datetime import datetime
from ansible.module_utils.keyfactor.core import AnsibleKeyfactorModule

def run_module():

    argument_spec = dict(
        # TODO: add documented fields to spec
        platform=dict(type='int', required=True),
        vdir=dict(type='str', required=True, default='KeyfactorAPI')
    )

    # seed the result dict in the object
    result = dict(
        pfx_certificate=None,
        pfx_password=None,
        certificate_id=None
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
    headers['Content-Type'] = 'application/json'
    headers['X-Keyfactor-Requested-With'] = 'APIClient'
    headers['X-CertificateFormat'] = 'PFX'
    module.params['headers'] = headers
    
    enrollment_result = enroll(module)

    result.update(enrollment_result)

    module.exit_json(**result)

def enroll(module):
    url = module.params.get('vdir', 'KeyfactorAPI')
    endpoint = url+'/Enrollment/PFX'
    payload = {
        'CustomFriendlyName': module.params.get('name', None),
        'Password': module.params.get('pfx_password', None),
        'PopulateMissingValuesFromAD': bool(module.params.get('values_from_ad', False)),
        'Subject': module.params.get('subject'),
        'IncludeChain': bool(module.params.get('cert_chain', False)),
        'CertificateAuthority': module.params.get('ca'),
        'Timestamp': datetime.now(timezone.utc).isoformat(),
        'Template': module.params.get('template'),
        'SANs': dict(module.params.get('sans', {})),
        'Metadata': dict(module.params.get('metadata', None)),
        'AdditionalEnrollmentFields': dict(module.params.get('additional_fields', None))
    }

    resp, info = module.handleRequest('POST', endpoint, payload)
    try:
        content = resp.read()
        response = json.loads(content)
        result = {
            'pfx_certificate': response['Certificate'],
            'pfx_password': response['Password'],
            'certificate_id': response['KeyfactorId']
        }
        return result
    except AttributeError:
        content = info.pop('body', '')
        message = json.loads(content)['Message']
        module.fail_json(msg=message)

def main():
    run_module()

if __name__ == '__main__':
    main()
