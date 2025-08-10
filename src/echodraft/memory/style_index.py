# Placeholder for style-transfer via embeddings/RAG.
# API will be: add_samples(texts: list[str]), retrieve_hints(prompt: str) -> list[str]
class StyleIndex:
    def __init__(self):
        self.samples = []

    def add_samples(self, texts):
        self.samples.extend(texts)

    def retrieve_hints(self, prompt: str):
        # Return simple n-gram hints for now
        return [s[:120] for s in self.samples[:3]]
