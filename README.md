# Ansible Collection - `keyfactor.platform`

This collection contains general plugins for Ansible to interface with the Keyfactor Platform.
Modules supporting API calls to Keyfactor are included, and roles will be added in the future.

## [Installing this collection](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html#installing-collections-with-ansible-galaxy)

To install the `keyfactor.platform` collection, you can download an available tarball from the releases section on GitHub. The tarball can be installed by running the following command.

```
ansible-galaxy collection install keyfactor-platform-1.0.0.tar.gz
```

Instead of downloading the tarball to install, you can also use this repository to build and install the collection yourself. Copy the entire repository to a local location on your machine, and run the following command to build and install the collection.

```
ansible-galaxy collection install ~/repos/ansible-collection-keyfactor-platform
```

## Using this collection

After the collection is installed, you can reference plugins in the collection with the Fully Qualified Collection Name (FQCN) `keyfactor.platform.<plugin>`.

The modules included in the collection require a few settings to be provided either by the system environment, or passed in as parameters in a playbook (which overrides the value set in the environment).

| Environment Variable | Parameter Override | Description |
| `KEYFACTOR_ADDR` | `url` | The full URL to the Keyfactor site. Should not include the API Endpoint, but must end with a "/" |
| `KEYFACTOR_USER` | `url_username` | The Keyfactor user to authenticate as when making API requests |
| `KEYFACTOR_PASSWORD` | `url_password` | The password for the Keyfactor user |
| `KEYFACTOR_IGNORE_SSL` | `validate_certs` | Set to `False` to skip validating Keyfactor's SSL cert |
| `CERTIFICATE_STORE_PATH` | `ca_path` | The path to trusted CA certs on the Ansible control node |
