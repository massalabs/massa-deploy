# Deployment script of Massa TestNet

This script is run inside a subfolder of massa git repository every time [the GitHub workflow for CD](https://github.com/massalabs/massa/blob/main/.github/workflows/cd.yml) detect a tag prefixed by `TEST.` :rainbow:!

## Secrets

Few secrets :key: should be defined in GitHub settings:

```
export TESTNET_USER = "CENSORED"
export TESTNET_PWD = "CENSORED"
export TESTNET_SRVS = {
   "testnet0": {
       "ip": "141.94.218.103",
       "node_privkey": "CENSORED",
       "node_pubkey": "CENSORED",
       "staking_privkey": "CENSORED",
       "bootstrap_server": false
   },
   "testnet1": {
       "ip": "149.202.86.103",
       "node_privkey": "CENSORED",
       "node_pubkey": "CENSORED",
       "staking_privkey": "CENSORED",
       "bootstrap_server": true
   },
   "testnet2": {
       "ip": "149.202.89.125",
       "node_privkey": "CENSORED",
       "node_pubkey": "CENSORED",
       "staking_privkey": "CENSORED",
       "bootstrap_server": true
   },
   "testnet3": {
       "ip": "158.69.120.215",
       "node_privkey": "CENSORED",
       "node_pubkey": "CENSORED",
       "staking_privkey": "CENSORED",
       "bootstrap_server": true
   },
   "testnet4": {
       "ip": "158.69.23.120",
       "node_privkey": "CENSORED",
       "node_pubkey": "CENSORED",
       "staking_privkey": "CENSORED",
       "bootstrap_server": true
   }
}
```
