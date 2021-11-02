import subprocess
import toml
import copy
import json
import time
import sys
import os

def run_cmd(cmd, ignore_err=False):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    res = process.communicate()
    if process.returncode != 0 and ignore_err == False:
        raise Exception("process failed")
    return res[0].decode('utf-8')

def tag(tag, genesis_timestamp, end_timestamp):
    # git clone
    print("cloning dev branch...")
    run_cmd("rm -rf massa", True)
    run_cmd("git clone https://gitlab.com/massalabs/massa")
    os.chdir("massa")
    run_cmd("git checkout dev")
    
    # update config
    print("updating config...")
    config_path = "massa-node/base_config/config.toml"
    config_data = toml.load(config_path)
    config_data["version"] = tag
    config_data["consensus"]["genesis_timestamp"] = genesis_timestamp
    config_data["consensus"]["end_timestamp"] = end_timestamp
    with open(config_path, "w") as toml_file:
        toml.dump(config_data, toml_file)
    
    # commit/push
    print("commit/push in dev...")
    run_cmd('git commit -am "temporary versioning"')
    run_cmd("git push")
    commit_id = run_cmd("git rev-parse HEAD").strip()
    
    # merge to testnet branch and tag
    print("merge into testnet...")
    run_cmd("git checkout testnet")
    run_cmd("git merge dev")
    run_cmd("git push")
    run_cmd('git tag "'+tag+'" -am "Version '+tag+'"')
    run_cmd("git push --tags")
    
    # revert in dev
    print("revert in dev...")
    run_cmd("git checkout dev");
    run_cmd("git revert --no-commit " + commit_id)
    run_cmd('git commit -am "undo temporary versioning"')
    run_cmd("git push")
    
    # cleanup
    print("cleanup...")
    os.chdir("..")
    run_cmd("rm -rf massa")
    
    print("done")

if __name__ == "__main__":
    tag(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))



