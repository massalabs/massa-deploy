import copy
import json
import subprocess
import sys
import toml

# this script should be run inside massa git repository
CONFIG_PATH = "massa-node/base_config/config.toml"
PEERS_PATH = "massa-node/storage/peers.json"
WALLET_PATH = "massa-client/wallet.dat"
STAKING_KEYS_PATH = "massa-node/config/staking_keys.json"
NODE_PRIVKEY_PATH = "massa-node/config/node_privkey.key"


def deploy(servers):
    # load config files
    print("loading config file...")
    config_data = toml.load(CONFIG_PATH)
    with open(PEERS_PATH) as json_file:
        peers = json.load(json_file)

    secrets = json.load(open('secrets.json'))
    testnet_user = secrets['testnet_user']
    testnet_pwd = secrets['testnet_pwd']
    srvs = secrets['srvs']

    print("preparing launch script...")
    with open("massa/massa-node/launch.sh", "w") as outf:
        outf.write("nohup cargo run --release > logs.txt 2>&1 &\n")

    for srv_name, srv in srvs.items():
        if srv_name not in servers:
            continue
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

        # upload to server
        host = f'{testnet_user}@{srv["ip"]}'
        subprocess.run(f'rsync -azP --delete . {host}:~')

        from fabric import Connection
        c = Connection(host=host, connect_kwargs={"password": testnet_pwd})
        c.run('pkill -f massa-node')
        c.run('source ~/.cargo/env && cd ~/massa/massa-node && nohup cargo run --release > logs.txt 2>&1 &')

    print("done 🎉")


# take as input the list of servers on which you want to deploy
if __name__ == "__main__":
    deploy(sys.argv[1:])
