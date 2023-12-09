# Fine-tuning guide
## Summary
The fine-tuning in this subnet is a little bit different from other subnets. Since the miners are consisting of various **engines** it means that each engine can be fine-tuned independently from each other. The way the engine is fine-tuned depends on the fundamental way the engine is built. Some engines rely on datasets and models while some use different methods to reach the objective of the engine.

For example, in the **Prompt Injection Analyzer**, there are currently following engines:
- Text Classification
- Heuristics
- Vector Search

The **Text Classification** engine by default uses [deepset/prompt-injections](https://huggingface.co/datasets/deepset/prompt-injections) to classify the given prompt either as malicious (injection) or non-malicious (non-injection). The engine can be fine-tuned either by changing the parameters in the engine code, tuning the existing model or creating entirely a new model that implements the same functionality.

The **Heuristics** engine consists (or, to be exact, will consists) of multiple **sub-engines** executing a very specific task. Currently the only supported sub-engine is YARA (https://virustotal.github.io/yara/), which is typically used for identifying malware. This is where the first non-traditional approach for fine-tuning comes. The engine is fine-tuned by creating new YARA rules to detect prompt injection attacks.

YARA is fundamentally a pattern matching tool based on set of strings and boolean expression, which makes it extremely effective on detecting prompt injections that follow a pre-determined syntax.

The **Vector Search** engine uses vector embeddings and calculates the distance of the given prompt against the vector embeddings stored in a local ChromaDB instance. This engine is fine-tuned by improving the vector embeddings stored inside ChromaDB, essentially by using more diverse dataset during the initialization of the engine. The engine can also be fine-tuned by adjusting the logic on how the data is queried and compared against the given prompt. 

## Technical HOWTO
Our objective is to provide engines that are more or less "static" once they reach sufficient maturity (at the moment, none of the engines are sufficiently mature). Once there are no longer constant changes to the engines, the fine-tuning can be achieved by simply creating a new git branch locally and run the miner from that specific branch by adjusting the --branch flag in the launch script. Within the local branch, you can make whatever changes you want to the engines including changes to code, models they use or practically anything else.

We are highly recommending to not changing anything but the engines to keep rest of the codebase up-to-date. You'll need to merge the changes from the main branch to your local branch whenever there are changes, but as the objective is to keep the changes to the engine code to the minimum, this merging can for the most parts be done automatically. In a long run, any changes to the engines considered to be stable are considered as breaking changes and they will be announced in advance.

You can obviously also do the fine-tuning with some other way, but this way you can quite easily keep rest of the code up-to-date with the main branch but still be able to fine-tune the miner code. This is also the way to do it if you want to get support from the subnet developers to help you get started with the fine-tuning process.

## Technical requirements
As our objective is to enable miner fine-tuners to potentially even completely rewrite the engines as they best see fit, we have implemented some technical requirements the engines must conform to. 

1. They must inherit the BaseEngine class can implement all of the abstract methods 
    - The abstract methods ensure the engine can be easily integrated into the miner and that it has the fundamental functionality used by the rest of the code
    - The abstract classes have built-in validators to ensure the user-controlled parameters stay within the expected ranges. Do not modify these as out-of-bound responses from miners will be considered to be invalid and thus given 0.0 weight.
2. The confidence score must be in range [0.0, 1.0].
    - In practise, this means that with value 1.0 the engine is absolutely sure the prompt is malicious and with score 0.0 it is absolutely sure it is not malicious. 
    - Your objective is to produce a confidence score based on what the prompt is about. If it's malicious (i.e., a prompt injection), your aim is to provide a confidence score closer to 1.0 and if it is not, the confidence score should be closer to 0.0.
    - If you classify a malicious prompt as non-malicious (i.e., confidence is less than 0.5) you lose scores, and if you classify it as malicious (i.e., confidence is more than 0.5), you can score.
    - The total score is calculated based on the distance to the "correct answer" (among other things such as speed of the reply)

Apart from these requirements, you are free to experiment with the fine-tuning as you best see fit. 

## Example walkthrough
