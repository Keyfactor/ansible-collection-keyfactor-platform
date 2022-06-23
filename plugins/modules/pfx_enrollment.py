#!/usr/bin/python

DOCUMENTATION = '''
---
module: pfx_enrollment

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
        description: Certificate authority HostName\\\\LogicalName
        required: true
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
        description: Name of the API Virtual Directory
        type: str
        default: KeyfactorAPI
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

author:
    - Matt Dobrowsky (@doebrowsk)
'''

EXAMPLES = '''
# Request a PFX with no chain and a specific password
- name: Request a chain-less PFX
  keyfactor.command.pfx_enrollment:
    subject: 'CN=testcertificate'
    template: 'WebServer'
    ca: 'CA.my.domain\\CA'
    cert_chain: False
    pfx_password: Password123!

# Request a PFX with metadata fields
- name: Request PFX with metadata fields
  keyfactor.command.pfx_enrollment:
    subject: 'CN=EnrollmentFields'
    template: 'WebServer'
    ca: 'CA.my.domain\\CA'
    metadata: {
        'Owner': 'MyTeam',
        'Reason': 'DeploymentTest'
    }

# Request a PFX with SANs
- name: Request PFX with SANs
  kkeyfactor.command.pfx_enrollment:
    subject: 'CN=CertWithSans'
    template: 'WebServer'
    ca: 'CA.my.domain\\CA'
    sans: {
        ip: 192.168.1.100,
        ip4: 192.168.1.100
    }
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

import json
from datetime import datetime, timezone
from ansible_collections.keyfactor.command.plugins.module_utils.core import AnsibleKeyfactorModule

def run_module():

    argument_spec = dict(
        vdir=dict(
            type='str',
            default='KeyfactorAPI'
        ),
        name=dict(
            type='str'
        ),
        subject=dict(
            type='str',
            required=True
        ),
        template=dict(
            type='str',
            required=True
        ),
        pfx_password=dict(
            type='str'
        ),
        ca=dict(
            type='str',
            required=True
        ),
        cert_chain=dict(
            type='bool',
            default=True
        ),
        values_from_ad=dict(
            type='bool',
            default=False
        ),
        metadata=dict(
            type='dict',
            default={}
        ),
        additional_fields=dict(
            type='dict',
            default={}
        ),
        sans=dict(
            type='dict',
            default={},
            options=dict(
                other=dict(
                    type='list',
                    elements='raw'
                ),
                rfc822=dict(
                    type='list',
                    elements='raw'
                ),
                dns=dict(
                    type='list',
                    elements='raw'
                ),
                x400=dict(
                    type='list',
                    elements='raw'
                ),
                directory=dict(
                    type='list',
                    elements='raw'
                ),
                ediparty=dict(
                    type='list',
                    elements='raw'
                ),
                uri=dict(
                    type='list',
                    elements='raw'
                ),
                ip=dict(
                    type='list',
                    elements='raw'
                ),
                ip4=dict(
                    type='list',
                    elements='raw'
                ),
                ip6=dict(
                    type='list',
                    elements='raw'
                ),
                registeredid=dict(
                    type='list',
                    elements='raw'
                ),
                ms_ntprincipalname=dict(
                    type='list',
                    elements='raw'
                ),
                ms_ntdsreplication=dict(
                    type='list',
                    elements='raw'
                )
            )
        )
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

    sans = module.params.get('sans', {})
    filtered_sans = {k: v for k,v in sans.items() if v is not None}

    payload = {
        'CustomFriendlyName': module.params.get('name', None),
        'Password': module.params.get('pfx_password', None),
        'PopulateMissingValuesFromAD': bool(module.params.get('values_from_ad', False)),
        'Subject': module.params.get('subject'),
        'IncludeChain': bool(module.params.get('cert_chain', False)),
        'CertificateAuthority': module.params.get('ca'),
        'Timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
        'Template': module.params.get('template'),
        'SANs': dict(filtered_sans),
        'Metadata': dict(module.params.get('metadata', None)),
        'AdditionalEnrollmentFields': dict(module.params.get('additional_fields', None))
    }

    resp, info = module.handleRequest('POST', endpoint, payload)
    try:
        content = resp.read()
        response = json.loads(content)
        cert_info = response['CertificateInformation']
        result = {
            'pfx_certificate': cert_info['Pkcs12Blob'],
            'pfx_password': cert_info['Password'],
            'certificate_id': cert_info['KeyfactorId']
        }
    except AttributeError:
        content = info.pop('body', '')
        message = json.loads(content)['Message']
        module.fail_json(msg=message)

def main():
    run_module()

if __name__ == '__main__':
    main()
