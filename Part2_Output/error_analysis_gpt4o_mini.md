# Error Analysis: False Positives and False Negatives

Model: gpt4o_mini
ROUGE-L threshold: 0.55

## Cross-model FP/FN summary

| Model | False positives | False negatives |
| --- | ---: | ---: |
| gpt4o_mini | 148 | 18 |
| gpt_4o | 33 | 18 |
| ollama | 148 | 20 |

## Summary

- **False positives:** 148
- **False negatives:** 18

## False Positive Examples (sample of 15)

- **Chunk 50:** "Further research is needed to replicate these findings."
- **Chunk 88:** "In addition, more research is needed to overcome the limitation of the existing literature."
- **Chunk 177:** "Future research should replicate these findings using a broader sampling approach for the experimental manipulation."
- **Chunk 177:** "Future research should take these factors, such as prior financial behaviour, into account in order to disentangle the effects of gender from other aspects related to individual differences."
- **Chunk 177:** "Additionally, future research should aim to analyse behavioural changes over time to determine whether these effects are sustainable in the long term."
- **Chunk 236:** "Further research is needed in this respect."
- **Chunk 236:** "Although more research is needed to understand which mechanisms explain the effectiveness of this type of social information."
- **Chunk 361:** "Evidence regarding the role of sustainability in online shopping is scarce and inconclusive."
- **Chunk 363:** "It remains unclear whether individuals experience cognitive dissonance as a result of the treatments."
- **Chunk 432:** "The specific compliance behavior of micro-business owners remains poorly understood."
- **Chunk 479:** "Future research should further investigate these mechanisms using additional measures and larger samples, with particular attention to the attitude – behaviour gap between intervention acceptability a..."
- **Chunk 517:** "Future work should study not only the willingness to compete in a single competition, but also how this willingness evolves in response to winning and losing in repeated competitions."
- **Chunk 517:** "Little is known about how the decision to compete is influenced by repeated competition outcomes."
- **Chunk 549:** "Little is known about non-economic motivations behind return intent of war refugees."
- **Chunk 630:** "Further research is needed to replicate these findings."

## False Negative Examples (sample of 15)

- **Chunk 197:** "Baillon et al., 2020"
- **Chunk 197:** "Baucells et al., 2011)."
- **Chunk 331:** "[Open Question] (For the answers 
given, see online data set.)"
- **Chunk 335:** "Since interventions in different 
countries have yielded varying results (Blair et al., 2020"
- **Chunk 432:** "Gangl et al., 2015"
- **Chunk 538:** "for a comprehensive review see Villeval (2020) ."
- **Chunk 680:** "Proestakis, Marandola, Lourenço, & van Bavel, 2024"
- **Chunk 680:** "Sconti, Caserta, & Ferrante, 2024)."
- **Chunk 959:** "Bic -
chieri et al., 2023 )."
- **Chunk 1034:** "Informal risk 
sharing has been documented in the field ( Fafchamps & Lund, 2003"
- **Chunk 1034:** "De 
Weerdt & Dercon, 2006 ) and in controlled experiments ( Barr & Genicot, 
2008"
- **Chunk 1181:** "Frank et al."
- **Chunk 1193:** "however,
the evidence on the nature of that impact is inconclusive and appears to
be situationally dependent."
- **Chunk 1290:** "This includes permitting subjects to modify the
decisions produced by an algorithm or to select which information the
algorithm processes (Dietvorst et al., 2018"
- **Chunk 1290:** "Jung & Seiter, 2021"

## Failure Mode Patterns (FP)

FP predictions grouped by opening words (most common first):

- `Further research is needed to...` -- 24 occurrences
- `Little is known about the...` -- 16 occurrences
- `Limited evidence exists on the...` -- 11 occurrences
- `Future work should investigate the...` -- 9 occurrences
- `Scarce evidence is available on...` -- 6 occurrences
- `Open questions remain about the...` -- 6 occurrences
- `Future work should explore the...` -- 5 occurrences
- `Future research should explore the...` -- 5 occurrences
- `Mixed evidence exists on the...` -- 4 occurrences
- `The relationship between nudging and...` -- 4 occurrences
