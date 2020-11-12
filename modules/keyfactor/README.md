# activate virtual environment
. venv/bin/activate
# environment script
. hacking/env-setup

# Test directly
python -m ansible.modules.keyfactor.keyfactor_identity tmp/identity_args.json
python -m ansible.modules.keyfactor.keyfactor_role tmp/role_args.json
python -m ansible.modules.keyfactor.keyfactor_metadata_fields tmp/metadata_fields_args.json


### Note
	**Important**: The keyfactor address should to contain a traling / for sources field to work as intended.

# Environmental Variables
export KEYFACTOR_ADDR=https://kftest.keyfactor.lab/
export KEYFACTOR_USER=KEYFACTOR\\Administrator
export KEYFACTOR_PASSWORD=
export KEYFACTOR_IGNORE_SSL=True

# Test playbook
ansible-playbook testmod.yml