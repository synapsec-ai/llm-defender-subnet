import llm_defender as LLMDefender

engine = LLMDefender.TokenClassificationEngine()
engine.prepare()
model, tokenizer = engine.initialize()

samples = [
    '374245455400126'
]
for sample in samples:
    engine = LLMDefender.TokenClassificationEngine(prompts=[sample])
    engine.execute(model=model, tokenizer=tokenizer)
    print(engine.get_response().get_dict())
