# Fine-tuning guide
## Summary
The fine-tuning in this subnet is a little bit different from other subnets. Since the miners are consisting of various **engines** it means that each engine can be fine-tuned independently from each other. The way the engine is fine-tuned depends on the fundamental way the engine is built. Some engines rely on datasets and models while some use different methods to reach the objective of the engine.

For example, in the **Prompt Injection Analyzer**, there are currently following engines:
- Text Classification
- YARA
- Vector Search

The **Text Classification** engine by default uses [deepset/prompt-injections](https://huggingface.co/datasets/deepset/prompt-injections) to classify the given prompt either as malicious (injection) or non-malicious (non-injection). The engine can be fine-tuned either by changing the parameters in the engine code, tuning the existing model or creating entirely a new model that implements the same functionality.

The **YARA** engine analyzes the prompts based on specific patterns. It is based on a tool called YARA (https://virustotal.github.io/yara/) that is typically used for identifying malware. This is where the first non-traditional approach for fine-tuning comes. The engine is fine-tuned by creating new YARA rules to detect prompt injection attacks. YARA is fundamentally a pattern matching tool based on set of strings and boolean expression, which makes it extremely effective on detecting prompt injections that follow a pre-determined syntax.

The **Vector Search** engine uses vector embeddings and calculates the distance of the given prompt against the vector embeddings stored in a local ChromaDB instance. This engine is fine-tuned by improving the vector embeddings stored inside ChromaDB, essentially by using more diverse dataset during the initialization of the engine. The engine can also be fine-tuned by adjusting the logic on how the data is queried and compared against the given prompt. 

## Technical HOWTO
Our objective is to provide engines that are more or less "static" once they reach sufficient maturity (at the moment, none of the engines are sufficiently mature). Once there are no longer constant changes to the engines, the fine-tuning can be achieved by simply creating a new git branch locally and run the miner from that specific branch by adjusting the --branch flag in the launch script. Within the local branch, you can make whatever changes you want to the engines including changes to code, models they use or practically anything else.

We are highly recommending to not changing anything but the engines to keep rest of the codebase up-to-date. You'll need to merge the changes from the main branch to your local branch whenever there are changes, but as the objective is to keep the changes to the engine code to the minimum, this merging can for the most parts be done automatically. In a long run, any changes to the engines considered to be stable are considered as breaking changes and they will be announced in advance.

You can obviously also do the fine-tuning with some other way, but this way you can quite easily keep rest of the code up-to-date with the main branch but still be able to fine-tune the miner code. This is also the way to do it if you want to get support from the subnet developers to help you get started with the fine-tuning process.

One important fine-tuning method is to also tune the engine weights in the `LLMDefenderMiner` class. Please note that this is the only fine-tuning you need to make outside of the engines. 

So in a nutshell, in order to fine-tune the **text classification** engine, you need to modify the following file:
- llm_defender/core/miners/engines/prompt_injection/text_classification.py

And within the file, you need to modify the `prepare()`, `initialize()`, `execute()`, `_calculate_confidence()` and `_populate_data()` functions. If you for example want to take another model into you but keep rest of the functionality as is, you would need to replace the model names within the `initialize()` and change the logic within the `_calculate_confidence()` and `_populate_data()` functions so that the output stays the same.

The engines have been designed so that they can be loaded outside of the miner. This way you can easily test the updated engine logic. 

Sample script for running text classification engine outside of the miner:

```
from llm_defender.core.miners.engines.prompt_injection.text_classification import TextClassificationEngine

engine = TextClassificationEngine()
engine.prepare()
model, tokenizer = engine.initialize()

for i in ["foo", "bar"]:
    engine = TextClassificationEngine(prompt=i)
    engine.execute(model=model, tokenizer=tokenizer)
    print(engine.get_response().get_dict())
```

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
Within this walkthrough, we are covering two example scenarios the miner can be fine-tuned. Neither of these examples are going to necessarily lead into better results, but should provide understanding on how the fine-tuning can be approached.

As mentioned earlier, we try to keep the engine files as static as possible. Meaning you should be able to edit the engine files as you best see fit and apply whatever fine-tuning practices you best see fit.

> [!NOTE]  
> Please note that you don't have to follow the steps we have outlined here. You can choose (and should!) your own fine-tuning strategy to gain an edge over other miners.

### Scenario 1 - Use different model for the text-classification engine
Lets start by creating a new local git branch:
```
$ git checkout -b finetune/text-classification-engine-2
```
By creating a local git branch, it is possible to modify the files locally and rebase the changes that have been made to the main branch without overwriting the local changes. This way you can easily apply the new miner configuration while keeping your local fine-tuning functional.
> [!NOTE]  
> Note that at times we'll also provide upgrades to the base engines. These upgrades will be announced in advance so that you can prepare for any upcoming changes.
To perform a Git rebase, issue the following command
```
$ git fetch origin main
$ git rebase origin/main
```
If you are not familiar with Git rebase, please read the following article: https://docs.gitlab.com/ee/topics/git/git_rebase.html

Once we have created a new branch, we can modify the code within the local branch.

In order to change the model we are using in the text-classification engine, we need to adjust the code in the following file: `llm_defender/core/miners/engines/prompt_injection/text_classification.py`

Within the `initialize()` method, the default model we are defining the default model to use. The default model is `laiyer/deberta-v3-base-prompt-injection` which sort of works, but performs quite poorly when topics not covered within the dataset used to train the model are being used as prompts.

As an alternative, we could use another open source model from Huggingface: `fmops/distilbert-prompt-injection`

To take the model into use, we need to change the model within the initialize() method, such that the code looks like this (changes made on lines 67 and 71):
```
64  def initialize(self):
65      try:
66        model = AutoModelForSequenceClassification.from_pretrained(
67              "fmops/distilbert-prompt-injection", cache_dir=self.cache_dir
68          )
69  
70          tokenizer = AutoTokenizer.from_pretrained(
71              "fmops/distilbert-prompt-injection", cache_dir=self.cache_dir
72          )
73      except Exception as e:
74          raise Exception(
75              f"Error occurred when initializing model or tokenizer: {e}"
76          ) from e
77  
78      if not model or not tokenizer:
79          raise ValueError("Model or tokenizer is empty")
80  
81      return model, tokenizer
```

As the models are producing slightly different output, we also need to modify the logic the confidence score is determined. To achieve this, we need to modify the `_calculate_confidence()` method. The default model uses `SAFE` and `INJECTION` labels, but the model `fmops/distilbert-prompt-injection` uses `LABEL_0` and `LABEL_1` respectively. The _calculate_confidence() method must be modified accordingly:
```
37  def _calculate_confidence(self):
38      # Determine the confidence based on the score
39      if self.output["outcome"] != "UNKNOWN":
40          if self.output["outcome"] == "LABEL_0":
41              return 0.0
42          else:
43              return 1.0
44      else:
45          return 0.5
```

Here we have modified the line 40 to set the confidence score to 0.0 when the outcome is labelled as `LABEL_0`.

Now that we have done the necessary changes, we can re-install the updated module by executing:
```
$ pip3 install -e .
$ pip uninstall uvloop -y
```

After installation, we can validate the output by using the text classification fine tuning helper script located at: `scripts/fine_tuning_helpers/text_classification_helper.py`

Sample output with the `fmops/distilbert-prompt-injection` model:
```
$ python3 scripts/fine_tuning_helpers/text_classification_helper.py 
{'name': 'engine:text_classification', 'confidence': 1.0, 'data': {'outcome': 'LABEL_1', 'score': 0.9995456337928772}}
{'name': 'engine:text_classification', 'confidence': 1.0, 'data': {'outcome': 'LABEL_1', 'score': 0.9995905756950378}}
{'name': 'engine:text_classification', 'confidence': 1.0, 'data': {'outcome': 'LABEL_1', 'score': 0.999567449092865}}
{'name': 'engine:text_classification', 'confidence': 1.0, 'data': {'outcome': 'LABEL_1', 'score': 0.9995642304420471}}
{'name': 'engine:text_classification', 'confidence': 1.0, 'data': {'outcome': 'LABEL_1', 'score': 0.9995841383934021}}
{'name': 'engine:text_classification', 'confidence': 0.0, 'data': {'outcome': 'LABEL_0', 'score': 0.999618649482727}}
{'name': 'engine:text_classification', 'confidence': 0.0, 'data': {'outcome': 'LABEL_0', 'score': 0.9996046423912048}}
```

Sample output with the default (`laiyer/deberta-v3-base-prompt-injection`) model:
```
$ python3 scripts/fine_tuning_helpers/text_classification_helper.py 
{'name': 'engine:text_classification', 'confidence': 0.0, 'data': {'outcome': 'SAFE', 'score': 0.9999998807907104}}
{'name': 'engine:text_classification', 'confidence': 1.0, 'data': {'outcome': 'INJECTION', 'score': 0.9999994039535522}}
{'name': 'engine:text_classification', 'confidence': 1.0, 'data': {'outcome': 'INJECTION', 'score': 0.9999992847442627}}
{'name': 'engine:text_classification', 'confidence': 1.0, 'data': {'outcome': 'INJECTION', 'score': 0.9999841451644897}}
{'name': 'engine:text_classification', 'confidence': 1.0, 'data': {'outcome': 'INJECTION', 'score': 0.9999783039093018}}
{'name': 'engine:text_classification', 'confidence': 0.0, 'data': {'outcome': 'SAFE', 'score': 0.9999998807907104}}
{'name': 'engine:text_classification', 'confidence': 0.0, 'data': {'outcome': 'SAFE', 'score': 0.9999998807907104}}
```

When validating the output, verify that there are values for the `name`, `confidence` and `data` keys within the dict returned. If these are missing, your miner will get a score of zero from the validators. The confidence score should reflect the type of the prompt: 1.0 means you are absolutely sure it is injection and 0.0 means you're absolute sure it is not. For more advanced scenarios, you may want to adjust the logic so that values other than 1.0 and 0.0 are used for cases that you are not absolutely certain of. The content of the `data` field is arbitrary but it **must be** populated by using the `_populate_data()` function.

The response is based on the values of `self.output` and `self.confidence` so it is vital these values are populated accordingly. If the output of your modified engine looks same as in the examples above, you should be good to go.

Once we are done with the modifications, we can run the miner with the updated code. It is recommended to commit the changes to the local branch before continuing further:
```
$ git add .
$ git commit -m "Changed the text classification engine to a better one"
```

And run the miner from your custom branch by changes the value for `--branch` parameter to whatever your local branch is called. For example:
```
$ pm2 start scripts/run.sh \
--name llm-defender-subnet-miner0 \
--watch ./llm-defender,./scripts -- \
--branch finetune/text-classification-engine-2 \
--netuid 14 \
--profile miner \
--wallet.name YourColdkeyGoesHere \
--wallet.hotkey YourHotkeyGoesHere \
--axon.port 15000
```

Thats it, now your miner is running with a different model and hopefully producing better incentive. If you want to revert back to the default state, simply relaunch the miner by setting the value for the `--branch` parameter to `main`.

The text classification engine can also be tune by fine-tuning the model itself. This however is out-of-scope for this guide, as the purpose of this guide is to ensure that the subnet specific topics that relate to the tuning of the miners are covered.

This scenario applies to all fine-tuning that involves 

### Scenario 2 - Add YARA rules
As discussed earlier, the fine-tuning of the subnet miners is done at the engine level, and each engine is fine-tuned slightly differently. With the YARA engine, we move away from the "traditional way" the Bittensor miners are tuned and introduce another mechanism for fine-tuning that can yield better results.

> [!NOTE]  
> It is recommended to follow the same Git practices discussed in the Scenario 1.

YARA rules are essentially a way to describe known patterns that are commonly observed within the prompt injections. Are certain words or combination of words often associated with prompt injections? A YARA rule can be extremely efficient on detecting prompt injections that rely on known patterns, such as certain combination of strings or bypass commands. However, it can be easily circumvented and prone for false-positives. The key in the tuning of the YARA engine is to find a balance between detection capabilities while eliminating false-positives.

More information about YARA and instructions on how to write rules can be found at: https://yara.readthedocs.io/en/stable/

The YARA engine is build such that you don't necessarily need to modify the engine code in order to fine-tune the engine performance. If you want to change the logic how the YARA engine is scoring the you should only modify the `_calculate_confidence()` method located in the file `llm_defender/core/miners/engines/prompt_injection/yara.py`.

By default, the YARA engine looks for the `meta.accuracy` key within the YARA rule to determine the what the confidence score will be. If there are multiple matches, the engine returns the **highest** value for the accuracy.

YARA rules are located in the `llm_defender/core/miners/engines/prompt_injection/yara_rules` directory. The engine is tuned by creating new rules (or modifying the existing ones) and saving them into the `yara_rules` directory. 

There are a few constraints that you must account for when creating new YARA rules:
1) They must be stored within the `yara_rules` directory
2) The file extension must be .yar (= your rule name must end with .yar)
3) There must be `meta.accuracy` key within the rule (see example)

Example rule:
```
rule UniversalJailbreak
{
    meta:
        name = "Universal Jailbreak"
        description = ""
        accuracy = "1.0"
    
    strings:
        $suffix1 = /describing\.\\ \+ similarlyNow write oppositeley\.\]\( Me giving\*\*ONE please\? revert with \"\\\!--Two/
        $suffix2 = /'representing Teamsures tableView \(\[githubINST -Of cour Here\/' surely]{\\comment={\[@ tableView "@github \[\/INST\]/
    condition:
        $suffix1 or $suffix2
}
```

The example rule condition is is checking if either the regex pattern in `$suffix1` or `$suffix2` is matching the string given as an input for the rule.

The fundamental idea to construct one (or several) YARA rules that look for specific patterns that are common occurrences within prompt injections. The YARA engine defaults to confidence score of 0.5 (meaning inconclusive results), so the YARA engine can also be used to detect prompts that are not injections, but in this case, you need to set the accuracy to 0.0 indicating the prompt is not an injection. But be careful, incorrectly classifying the prompts gives you negative results.

Similar to the Text Classification engine, we have provided a simple helper script that you can use to test out your YARA rules. The script is located at: `scripts/fine_tuning_helpers/yara_helper.py`.

Given the default rules, the prompts within the helper script are not detected.
```
$ python3 scripts/fine_tuning_helpers/yara_helper.py 
{'name': 'engine:yara', 'confidence': 0.5, 'data': {'outcome': 'NoRuleMatch'}}
{'name': 'engine:yara', 'confidence': 0.5, 'data': {'outcome': 'NoRuleMatch'}}
{'name': 'engine:yara', 'confidence': 0.5, 'data': {'outcome': 'NoRuleMatch'}}
{'name': 'engine:yara', 'confidence': 0.5, 'data': {'outcome': 'NoRuleMatch'}}
{'name': 'engine:yara', 'confidence': 0.5, 'data': {'outcome': 'NoRuleMatch'}}
{'name': 'engine:yara', 'confidence': 0.5, 'data': {'outcome': 'NoRuleMatch'}}
{'name': 'engine:yara', 'confidence': 0.5, 'data': {'outcome': 'NoRuleMatch'}}
```

We can inspect the prompts used as examples to determine patterns that could be detected with a YARA rule. Lets say that we are certain that no legit prompts would ever contain "haha pwned" or "haha owned" in them. We could create a YARA rule to look for this behavior:
```
rule HahaPwned
{
    meta:
        name = "Haha Pwned"
        description = "Hackers love to input Haha Pwned in their examples so a prompt must be malicious if such string is contained within"
        accuracy = "1.0"
    
    strings:
        $pwnedOwned = /(haha pwned|haha owned)/ nocase
    condition:
        $pwnedOwned
}
```

When this rule is added to the `yara_rules` directory, we can get a match for two of the example strings:
```
python3 scripts/fine_tuning_helpers/yara_helper.py 
{'name': 'engine:yara', 'confidence': 0.5, 'data': {'outcome': 'NoRuleMatch'}}
{'name': 'engine:yara', 'confidence': 1.0, 'data': {'outcome': 'RuleMatch', 'meta': [{'name': 'Haha Pwned', 'description': 'Hackers love to input Haha Pwned in their examples so a prompt must be malicious if such string is contained within', 'accuracy': '1.0'}]}}
{'name': 'engine:yara', 'confidence': 0.5, 'data': {'outcome': 'NoRuleMatch'}}
{'name': 'engine:yara', 'confidence': 0.5, 'data': {'outcome': 'NoRuleMatch'}}
{'name': 'engine:yara', 'confidence': 0.5, 'data': {'outcome': 'NoRuleMatch'}}
{'name': 'engine:yara', 'confidence': 0.5, 'data': {'outcome': 'NoRuleMatch'}}
{'name': 'engine:yara', 'confidence': 0.5, 'data': {'outcome': 'NoRuleMatch'}}
{'name': 'engine:yara', 'confidence': 1.0, 'data': {'outcome': 'RuleMatch', 'meta': [{'name': 'Haha Pwned', 'description': 'Hackers love to input Haha Pwned in their examples so a prompt must be malicious if such string is contained within', 'accuracy': '1.0'}]}}
```

But actually, the last match is a false-positive match as it matches to a completely valid question: "Can you tell me why hackers often use "Haha pwned!!" in their examples?". So fine-tuning the YARA engine is about finding the balance between patterns that *can* be malicious without overdoing it so that non-malicious prompts are also triggering the rules.

You can also use values other than 0.0 and 1.0 in the `meta.accuracy` field. It might be a good technique to create less-accurate rules that are still *likely* to be malicious and set their accuracy to for example 0.65 so that when the match is true-positive it provides slightly better score without producing that significant penalty for false-positive entries.

### Scenario 3 - Modify Vector Search Engine

> [!NOTE]  
> It is recommended to follow the same Git practices discussed in the Scenario 1.


XXX
