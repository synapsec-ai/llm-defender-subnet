<h1 align="center">LLM Defender Subnet (SN14)</h1>
<h4 align="center">| <a href="https://docs.synapsec.ai">Documentation</a> | </h4>

# Introduction
This repository contains the source code for the LLM Defender subnet running on top of [Bittensor](https://github.com/opentensor/bittensor). The LLM Defender subnet provides Large Language Model (LLM) developers a way to decentralize the computing required to detect and prevent various attacks and exploits against LLM applications. 

Check the separate <a href="https://docs.synapsec.ai">documentation page</a> for detailed information about the Subnet.

## Summary
There are different and constantly evolving ways to attack LLMs, and to efficiently protect against such attacks, it is necessary to layer up several defensive methods to prevent the attacks from affecting the LLM or the application relying on the model.

The subnet is being built with the concept of defense-in-depth in mind. The subnet aims to provide several **analyzers** each consisting of multiple **engines** to create a modular and high-performing capability for detecting attacks against LLMs.

The ultimate goal is to enable LLM developers to harness the decentralized intelligence provided by the subnet and combine it with their local defensive capabilities to truly embrace the concept of defense-in-depth.

The subnet is working such that the engines are providing a **confidence** score depicting how confident they are that a given input is an attack against an LLM. The summarized confidence score is used to reach a verdict on whether a given prompt is an attack against LLM or not. 

Due to the nature of the Bittensor network, the confidence score is a result of combined intelligence of hundreds of different endpoints providing LLM developers with unprecedented potential to secure their applications and solutions.

## Quickstart
This repository requires python3.10 or higher and Ubuntu 22.04/Debian 12. It is highly recommended to spin up a fresh Ubuntu 22.04 or Debian 12 machine for running the subnet neurons. Upgrading from python3.8 to python3.10 on Ubuntu 20.04 is known to cause issues with the installation of the python modules required by the miners.

> [!WARNING]  
> We are recommending to use python virtual environment (venv) when running either the validator or miner. Make sure the virtual environment is active prior to launching the pm2 instance.

Installation:
```
$ sudo apt update && sudo apt install jq && sudo apt install npm \
&& sudo npm install pm2 -g && pm2 update && sudo apt install git
$ git clone https://github.com/ceterum1/llm-defender-subnet
$ cd llm-defender-subnet
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install bittensor
```

> [!NOTE]  
> During installation you might get an error "The virtual environment was not created successfully because ensurepip is not available". In this case, install the python3.11-venv (or python3.10-venv) package following the instructions on screen. After this, re-execute the `python3 -m venv .venv` command.

If you are not familiar with Bittensor, you should first perform the following activities:
- [Generate a new coldkey](https://docs.bittensor.com/getting-started/wallets#step-1-generate-a-coldkey)
- [Generate a new hotkey under your new coldkey](https://docs.bittensor.com/getting-started/wallets#step-2-generate-a-hotkey)
- [Register your new hotkey on our subnet 14](https://docs.bittensor.com/subnets/register-and-participate)

> [!NOTE]  
> Validators need to establish an internet connection with the miner. This requires ensuring that the port specified in --axon.port is reachable on the virtual machine via the internet. This involves either opening the port on the firewall or configuring port forwarding.

Run miner (if you run multiple miners, make sure the name and axon.port are unique):
```
$ cd llm-defender-subnet
$ source .venv/bin/activate
$ bash scripts/run_neuron.sh \
--name llm-defender-subnet-miner-0 \
--install_only 0 \
--max_memory_restart 10G \
--branch main \
--netuid 14 \
--profile miner \
--wallet.name YourColdkeyGoesHere \
--wallet.hotkey YourHotkeyGoesHere \
--axon.port 15000 \
```

Run validator (if you run multiple validators, make sure the name is unique):
```
$ cd llm-defender-subnet
$ source .venv/bin/activate
$ bash scripts/run_neuron.sh \
--name llm-defender-subnet-validator-0 \
--install_only 0 \
--max_memory_restart 5G \
--branch main \
--netuid 14 \
--profile validator \
--wallet.name YourColdkeyGoesHere \
--wallet.hotkey YourHotkeyGoesHere
```

Run auto-updater (only one instance needs to be running even if you have multiple PM2 instances active on the same machine):
```
$ cd llm-defender-subnet
$ source .venv/bin/activate
$ bash scripts/run_auto_updater.sh \
--update_interval 300 \
--branch main \
--pm2_instance_names llm-defender-subnet-validator-0 llm-defender-subnet-miner-0 \
--prepare_miners True
```