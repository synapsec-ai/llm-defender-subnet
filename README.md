# Bittensor Prompt Defender Subnet
This repository contains the source code for the Prompt Defender subnet running on top of [Bittensor network](https://github.com/opentensor/bittensor). The Prompt Defender subnet provides Large Language Model (LLM) developers a way to decentralize the computing required to detect and prevent various attacks and exploits against LLM applications. 

## Summary
There are different and constantly evolving ways to attack LLMs, and to efficiently protect against such attacks, it is necessary to layer up several defensive methods to prevent the attacks from affecting the LLM or the application relying on the model.

The subnet is being built with the concept of defense-in-depth in mind. The subnet aims to provide several **capabilities** each consisting of multiple **engines** to create a modular and high-performing capability for detecting attacks against LLMs. 

The ultimate goal is to enable LLM developers to harness the decentralized intelligence provided by the subnet and combine it with their local defensive capabilities to truly embrace the concept of defense-in-depth.

The subnet is working such that the engines are providing a **confidence** score depicting how confident they are that a given input is an attack against an LLM. The summarized confidence score is used to reach a verdict on whether a given prompt is an attack against LLM or not. 

Due to the nature of the Bittensor network, the confidence score is a result of combined intelligence of hundreds of different endpoints providing LLM developers with unprecedented potential to secure their applications and solutions.

## Quickstart

This repository requires python3.10 or higher.

Installation:
```
$ git clone https://github.com/ceterum1/prompt-defender-subnet.git
$ cd prompt-defender-subnet
$ python -m venv .venv
$ source .venv/bin/activate
$ sudo apt update && sudo apt install jq && sudo apt install npm && sudo npm install pm2 -g && pm2 update
```

Run miner:
```
pm2 start scripts/run.sh -- --netuid X --profile miner --wallet.name <your validator wallet> --wallet.hotkey <your validator hotkey> [--subtensor.network test --subtensor.chain_endpoint ws://127.0.0.1:9946] --logging.<log-level>
```

Run validator:
```
pm2 start scripts/run.sh --netuid X --profile validator --wallet.name <your validator wallet> --wallet.hotkey <your validator hotkey> [--subtensor.network test --subtensor.chain_endpoint ws://127.0.0.1:9946] --logging.<log-level>
```
## Capabilities
The subnet contains the following capabilities and engines
- [Prompt Injection](https://llmtop10.com/llm01/)
    - Text classification
    - Heuristics (multiple methods including YARA)
    - Vector analysis

The current capabilities focus on analyzing the initial input prompt but the short-term target is to expand the capabilities in such a way that analyzing complex multi-stage injections becomes possible.

Further capabilities and engines will be added to the subnet in the future to expand the capabilities to cover functional use cases other than prompt injection. Our mission is to be the enabler for secure AI applications.

## FAQ
```
Q: Why are there multiple engines?
A: A single engine can be prone for false-positives and in order to reach a definite conclusion about the legitimacy of an input we need to take into account input from multiple different engines. 

Q: I have already deployed <insert local solution here>, how do I benefit from this solution?
A: As per the defense-in-depth concept, the fundamental idea is to layer up defenses for your LLM application. This solution is not meant to replace your local defenses but rather offload some of the computing-heavy analysis to be performed by the decentralized machine-learning network. 

The incentive mechanism that is built-in to Bittensor will ensure the intelligence of the network will grow as time goes on and in the long-run the solution is expected to outperform any local defensive measures you have deployed.
```

## Fine-tuning and Development
Fine-tuning and development have been described in their respective guides:
- [Developer Guide](./docs/developer-guide.md)
- [Fine-tuning Guide](./docs/fine-tuning-guide.md)
