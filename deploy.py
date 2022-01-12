import copy
import json
import os
import sys
import time
import toml

ROOT_PATH = ".."  # this script is run inside a subfolder of massa git repository
CONFIG_PATH = f'{ROOT_PATH}/massa-node/base_config/config.toml'
PEERS_PATH = f'{ROOT_PATH}/massa-node/storage/peers.json'
WALLET_PATH = f'{ROOT_PATH}/massa-client/wallet.dat'
STAKING_KEYS_PATH = f'{ROOT_PATH}/massa-node/config/staking_keys.json'
NODE_PRIVKEY_PATH = f'{ROOT_PATH}/massa-node/config/node_privkey.key'


if __name__ == "__main__":
    # load config files
    print("loading config file...")
    config_data = toml.load(CONFIG_PATH)
    with open(PEERS_PATH) as json_file:
        peers = json.load(json_file)

    testnet_user = os.environ['TESTNET_USER']
    testnet_pwd = os.environ['TESTNET_PWD']
    # Example value for $TESTNET_SRVS:
    # {
    #    "testnet0": {
    #        "ip": "141.94.218.103",
    #        "node_privkey": "CENSORED",
    #        "node_pubkey": "CENSORED",
    #        "staking_privkey": "CENSORED",
    #        "bootstrap_server": false
    #    },
    #    "testnet1": {
    #        "ip": "149.202.86.103",
    #        "node_privkey": "CENSORED",
    #        "node_pubkey": "CENSORED",
    #        "staking_privkey": "CENSORED",
    #        "bootstrap_server": true
    #    },
    #    "testnet2": {
    #        "ip": "149.202.89.125",
    #        "node_privkey": "CENSORED",
    #        "node_pubkey": "CENSORED",
    #        "staking_privkey": "CENSORED",
    #        "bootstrap_server": true
    #    },
    #    "testnet3": {
    #        "ip": "158.69.120.215",
    #        "node_privkey": "CENSORED",
    #        "node_pubkey": "CENSORED",
    #        "staking_privkey": "CENSORED",
    #        "bootstrap_server": true
    #    },
    #    "testnet4": {
    #        "ip": "158.69.23.120",
    #        "node_privkey": "CENSORED",
    #        "node_pubkey": "CENSORED",
    #        "staking_privkey": "CENSORED",
    #        "bootstrap_server": true
    #    }
    # }
    srvs = os.environ['TESTNET_SRVS']

    for srv_name, srv in srvs.items():
        print("distributing to", srv_name, "...")

        # setup node staking keys
        res_staking_keys = [srv["staking_privkey"], ]
        with open(STAKING_KEYS_PATH, "w") as json_file:
            json_file.write(json.dumps(res_staking_keys, indent=2))

        # setup peers
        res_peers = [p for p in peers if p["ip"] != srv["ip"]]
        with open(PEERS_PATH, "w") as json_file:
            json_file.write(json.dumps(res_peers, indent=2))

        # setup node privkey
        with open(NODE_PRIVKEY_PATH, "w") as outf:
            outf.write(srv["node_privkey"])

        # setup node wallet
        res_wallet = [srv["staking_privkey"]]
        with open(WALLET_PATH, "w") as json_file:
            json_file.write(json.dumps(res_wallet, indent=2))

        # setup config
        cfg = copy.deepcopy(config_data)
        cfg["network"]["target_bootstrap_connections"] = len(
            srvs) - 1  # connect to all bootstrap srvs
        # connect to 3 peers
        cfg["network"]["target_out_nonbootstrap_connections"] = 3
        # allow 10 people in
        cfg["network"]["max_in_nonbootstrap_connections"] = 10
        cfg["network"]["routable_ip"] = srv["ip"]
        cfg["logging"]["level"] = 2

        cfg["bootstrap"]["bootstrap_list"] = [
            [srv_v["ip"] + ":31245", srv_v["node_pubkey"]]
            for (srv_n, srv_v) in srvs.items() if srv_v["bootstrap_server"] is True and srv_n != srv_name
        ]
        if srv["bootstrap_server"] is False:
            del cfg["bootstrap"]["bind"]

        with open(CONFIG_PATH, "w") as toml_file:
            toml.dump(cfg, toml_file)

        # release channels (based on build flavors)
        cargo_options = "--release"
        if "--beta" in sys.argv:
            cargo_options += " --features beta"

        # upload to server
        host = f'{testnet_user}@{srv["ip"]}'
        os.system(f'rsync -azP --delete {ROOT_PATH} {host}:~')

        from fabric import Connection
        c = Connection(host=host, connect_kwargs={"password": testnet_pwd})
        c.run('pkill -f massa-node')
        c.run(f'source ~/.cargo/env && cd ~/massa/massa-node && nohup cargo run {cargo_options} > logs.txt 2>&1 &')

        time.sleep(300)

    print("done 🎉")
