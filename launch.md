# TL;DR
- **Github repository**: https://github.com/ceterum1/llm-defender-subnet
- **Summary**: The LLM Defender Subnet aims to provide LLM developers means to protect their applications against different types of attacks. This includes both applications outside of Bittensor ecosystem as well as other Bittensor subnets that could benefit from the safeguards against prompt-based attacks, such as prompt injection and jailbreaking, among others.
- **Running Miner or validator**: Follow the instructions at: https://github.com/ceterum1/llm-defender-subnet#quickstart. The run script included in the repository installs, prepares and runs the neurons depending on the configuration parameters. You can also keep the neurons (miners & validators) up-to-date by launching the updater script. PM2 is supported and recommended to be used.
- **Fine-tuning**: Fine-tuning will be described in the fine-tuning guide at: https://github.com/ceterum1/llm-defender-subnet/blob/main/docs/fine-tuning-guide.md (to be released in a few days!)
- **Test period**: For the next two weeks we are running a public testing phase during which we'll be collecting feedback from the community, locking in the development priorities and providing emergency hotfixes on a short notice. During this period it is highly recommended to keep the neurons up-to-date as it is likely we have forced to implement breaking changes 
- **Resource requirements**: The exact resource requirements will be locked in once the subnet has matured. The miners or validators do not at the moment require GPU and we have been running tests successfully with 16 GB of RAM 8, vCPU (3,8 GHz) and 100 GB SSD. With this setup we've been running both validator and miner. It is recommended you experiment with the resources and monitor the resource usage. 
- **Contacts**: ceterum_ (technical), Cradow (all other things) 


# LLM Defender Subnet

## Subnet goal and problem statement
There are different and constantly evolving ways to attack LLMs, and to efficiently protect against such attacks, it is necessary to layer up several defensive methods to prevent the attacks from affecting the LLM or the application relying on the model.

The ultimate goal is to enable LLM developers to harness the decentralized intelligence provided by the subnet and combine it with their local defensive capabilities to truly embrace the concept of defense-in-depth.

Given the current capabilities to detect such attacks, most if not all solutions suffer from the same fundamental problems:
- Lack of proper datasets and models to detect attacks (overfitting is a huge issue)
- High-computing requirements to run the solutions locally
- Specialized competence required to efficiently operate the local solutions
- Rapidly evolving threat landscape without established detection methods

Our objective is to utilize the Bittensor ecosystem to provide LLM developers within and outside of the Bittensor ecosystem methods to protect their applications against the attacks. We do not prevent the attacks, but provide the application developers highly sophisticated analysis based on which they can make a decision whether the prompt discarded or not for being malicious.

## Description
As the subnet is being built with the concept of defense-in-depth in mind. The subnet aims to provide several capabilities each consisting of multiple engines to create a modular and high-performing capability for detecting attacks against LLMs. An engine can consist of a single analyzer or multiple subengines working towards a common goal.

The subnet is working such that the engines are providing a confidence score depicting how confident they are that a given input is an attack against an LLM. The summarized confidence score is used to reach a verdict on whether a given prompt is an attack against LLM or not.

Due to the nature of the Bittensor network, the confidence score is a result of combined intelligence of hundreds of different endpoints providing LLM developers with unprecedented potential to secure their applications and solutions.

### Miner logic
The logic for the miners is described in detail in the GitHub repository, but here is a brief summary of what they are doing:
- Each miner executes different **engines** that implement capabilities to detect different types of attacks against LLMs
- For example, in order to properly detect **prompt injection**, we need to execute multiple different detection methods. 
    - A single method may be prone to false-positives or may not work with certain types of prompts.
    - By combining the intelligence produced by multiple engines we can increase the confidence of the detection and cover multiple different types of prompt injection attacks
- Fine-tuning is done by improving the engines
    - Some engines use text classification or other machine-learning based models
    - Engines may also use different methods such as vector search or pattern matching to detect prompt injection

### Validator logic
The logic for the validators is described in detail in the GitHub repository, but here is a brief summary of what they are doing:
- General purpose validators (i.e., those that are not connected to other subnets and/or third party applications) are sending synthetic prompts to the miners to be analyzed by the engines. 
    - The synthetic prompts are used to rank the miners.
    - Ranking is based on three criteria: (1) Accuracy of the analysis, (2) Speed of the analysis and (3) Number of engines used.
- Dedicated validators (i.e., those that are connected to other subnets and/or third party applications) are sending real prompts to the miners to be analyzed. 
    - The selection criteria has not been implemented yet, but the idea is that the best miners are chosen to handle real prompts originating from third party applications (through the subnet API) or from other Bittensor subnets (through a subnet-owner controlled validator) to ensure the best results are received for real prompts


## Development roadmap
We are keeping the development roadmap up-to-date in the GitHub repository, but here are some rough ideas where we are heading to:
- Version 1.0 launch in late Q1/2024 or early Q2/2024.
- The development objectives for version 1.0 are the following:
    - Demo application and publicly available API for the subnet
    - Prompt API for generating synthetic prompts that are resilient against manipulation
    - A total of four different analyzers aligned with OWASP Top 10 for LLM applications (https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-2023-v1_1.pdf)
    - Multiple engines for each analyzer to increase the level of confidence of the replies received from the miners
    - Comprehensive documentation both for fine-tuning and development
    - Neuron monitoring capabilities (wandb or similar)
    - Proper datasets and models for the engines
    - Resilient scoring algorithm for scoring the miners to ensure the integrity of the subnet
    - \+ Potentially other features originating from the community

## How to contribute 
Easiest way to contribute is to run miners and start to fine-tune the miners, as the default parameters will not be sufficient for high-quality detection of attacks against LLMs.

If you want to get involved in the development process, reach out to the subnet contacts. Alternatively, you can create pull requests in GitHub for new features and/or bug fixes to existing codebase.

Additionally, we are looking forward to hear about the needs of the community. So for all subnet owners out there, if you think our solution could help your subnet in some way, feel free to reach out to us. Our aim is bring value to existing Bittensor ecosystem and thus we feel it is important to steer the development based on the needs of the community.



--


4 0.99998
5 0.91514
19 0.31740
62 0.68280

