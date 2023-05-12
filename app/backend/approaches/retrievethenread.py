import openai
from approaches.approach import Approach
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType
from text import nonewlines

# Simple retrieve-then-read implementation, using the Cognitive Search and OpenAI APIs directly. It first retrieves
# top documents from search, then constructs a prompt with them, and then uses OpenAI to generate an completion
# (answer) with that prompt.


class RetrieveThenReadApproach(Approach):

    template = \
        "You are an intelligent assistant helping Corteva customers answer questions about which Corteva product is appropriate for their use case. " + \
        "Use 'you' to refer to the individual asking the questions even if they ask with 'I'. " + \
        "Answer the following question using only the data provided in the sources below. " + \
        "For tabular information return it as an html table. Do not return markdown format. " + \
        "Each source has a name followed by colon and the actual information, always include the source name for each fact you use in the response. " + \
        "If you cannot answer using the sources below, say you don't know. " + \
        """

###
Question: 'I see brown lesions on my soybean roots, what should I do?'

Sources:
DF-C-1019FI-Featuring-Lumisena-Training-Deck-16.pdf: is characterized by a shrunken, reddish-brown lesion on the hypocotyl at or near the soil line. Infection may be superficial, causing no noticeable damage, or may girdle the stem and kill or stunt plants Fusarium C-1019FI offers two modes of action
DF-Seed-Treatment-3rd-Party-Sell-Sheet-XYZ-0.pdf: A YIELD ADVANTAGE Potential yield benefit in field areas with higher Phytophthora susceptibility using Lumisena fungicide seed treatment. A YIELD ADVANTAGE Potential yield benefit across the farm using Lumisena fungicide seed treatment. LUMISENA FUNGICIDE INDUSTRY - STANDARD SEED TREATMENT SEED TREATMENT *Versus the existing industry-standard seed treatment.

Answer:
It's possible that your soybean roots are affected by Fusarium or Phytophthora, which are two diseases that can cause brown lesions on roots. If you have Lumisena fungicide seed treatment, it may help protect your soybean plants against these diseases. However, it's best to consult with an agricultural expert or plant pathologist for a proper diagnosis and treatment plan.

###
Question: '{q}'?

Sources:
{retrieved}

Answer:
"""

    def __init__(self, search_client: SearchClient, openai_deployment: str, sourcepage_field: str, content_field: str):
        self.search_client = search_client
        self.openai_deployment = openai_deployment
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field

    def run(self, q: str, overrides: dict) -> any:
        use_semantic_captions = True if overrides.get(
            "semantic_captions") else False
        top = overrides.get("top") or 3
        exclude_category = overrides.get("exclude_category") or None
        filter = "category ne '{}'".format(
            exclude_category.replace("'", "''")) if exclude_category else None

        if overrides.get("semantic_ranker"):
            r = self.search_client.search(q,
                                          filter=filter,
                                          query_type=QueryType.SEMANTIC,
                                          query_language="en-us",
                                          query_speller="lexicon",
                                          semantic_configuration_name="default",
                                          top=top,
                                          query_caption="extractive|highlight-false" if use_semantic_captions else None)
        else:
            r = self.search_client.search(q, filter=filter, top=top)
        if use_semantic_captions:
            results = [doc[self.sourcepage_field] + ": " + nonewlines(
                " . ".join([c.text for c in doc['@search.captions']])) for doc in r]
        else:
            results = [doc[self.sourcepage_field] + ": " +
                       nonewlines(doc[self.content_field]) for doc in r]
        content = "\n".join(results)

        prompt = (overrides.get("prompt_template")
                  or self.template).format(q=q, retrieved=content)
        completion = openai.Completion.create(
            engine=self.openai_deployment,
            prompt=prompt,
            temperature=overrides.get("temperature") or 0.3,
            max_tokens=1024,
            n=1,
            stop=["\n"])

        return {"data_points": results, "answer": completion.choices[0].text, "thoughts": f"Question:<br>{q}<br><br>Prompt:<br>" + prompt.replace('\n', '<br>')}
