from llm_defender.core.miners.analyzers.sensitive_information.token_classification import TokenClassificationEngine

engine = TokenClassificationEngine()
engine.prepare()
model, tokenizer = engine.initialize()

samples = [
    '374245455400126'
]
for sample in samples:
    engine = TokenClassificationEngine(prompt=sample)
    engine.execute(model=model, tokenizer=tokenizer)
    print(engine.get_response().get_dict())
