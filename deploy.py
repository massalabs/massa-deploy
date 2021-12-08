import subprocess
import toml
import copy
import json
import os
import sys


def run_cmd(cmd, ignore_err=False):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    process.communicate()
    if process.returncode != 0 and ignore_err == False:
        raise Exception("process failed")


def deploy(tag, servers):
    # git clone
    print("cloning git...")
    run_cmd("rm -rf massa")
    run_cmd("git clone --depth 1 --branch " + tag +
            " https://github.com/massalabs/massa")

    # load config files
    print("loading config file...")
    config_path = "massa/massa-node/base_config/config.toml"
    peers_path = "massa/massa-node/storage/peers.json"
    wallet_path = "massa/massa-client/wallet.dat"
    staking_keys_path = "massa/massa-node/config/staking_keys.json"
    node_privkey_path = "massa/massa-node/config/node_privkey.key"
    config_data = toml.load(config_path)
    with open(peers_path) as json_file:
        peers = json.load(json_file)

    testnet_user = os.environ['TESTNET_USER']
    testnet_pwd = os.environ['TESTNET_PWD']
    # Example value for $TESTNET_PWD:
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

    print("preparing launch script...")
    with open("massa/massa-node/launch.sh", "w") as outf:
        outf.write("nohup cargo run --release > logs.txt 2>&1 &\n")

    for srv_name, srv in srvs.items():
        if srv_name not in servers:
            continue
        print("distributing to", srv_name, "...")

        # setup node staking keys
        res_staking_keys = [srv["staking_privkey"], ]
        with open(staking_keys_path, "w") as json_file:
            json_file.write(json.dumps(res_staking_keys, indent=2))

        # setup peers
        res_peers = [p for p in peers if p["ip"] != srv["ip"]]
        with open(peers_path, "w") as json_file:
            json_file.write(json.dumps(res_peers, indent=2))

        # setup node privkey
        with open(node_privkey_path, "w") as outf:
            outf.write(srv["node_privkey"])

        # setup node wallet
        res_wallet = [srv["staking_privkey"]]
        with open(wallet_path, "w") as json_file:
            json_file.write(json.dumps(res_wallet, indent=2))

        # setup config
        cfg = copy.deepcopy(config_data)
        cfg["version"] = tag
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

        with open(config_path, "w") as toml_file:
            toml.dump(cfg, toml_file)

        # upload to server
        run_cmd("zip -r massa.zip massa")
        run_cmd('sshpass -p "' + testnet_pwd + '" ssh testnet@' +
                srv["ip"] + ' "pkill -f massa-node"', ignore_err=True)
        run_cmd('sshpass -p "' + testnet_pwd + '" ssh testnet@' +
                srv["ip"] + ' "rm -rf massa"', ignore_err=True)
        run_cmd('sshpass -p "' + testnet_pwd + '" scp -r -o StrictHostKeyChecking=no massa.zip testnet@' +
                srv["ip"] + ':/home/testnet/massa.zip')
        run_cmd('sshpass -p "' + testnet_pwd + '" ssh testnet@' +
                srv["ip"] + ' "source /home/testnet/.cargo/env && unzip massa.zip && rm massa.zip && cd massa/massa-node && chmod +x launch.sh && ./launch.sh"')
        run_cmd("rm massa.zip")

    run_cmd("rm -rf massa")
    print("done")


if __name__ == "__main__":
    deploy(sys.argv[1], sys.argv[2:])
