import llm_defender.core.miner as LLMDefenderCore

engine = LLMDefenderCore.TokenClassificationEngine()
engine.prepare()
model, tokenizer = engine.initialize()

samples = [
    '374245455400126'
]
for sample in samples:
    engine = LLMDefenderCore.TokenClassificationEngine(prompts=[sample])
    engine.execute(model=model, tokenizer=tokenizer)
    print(engine.get_response().get_dict())
