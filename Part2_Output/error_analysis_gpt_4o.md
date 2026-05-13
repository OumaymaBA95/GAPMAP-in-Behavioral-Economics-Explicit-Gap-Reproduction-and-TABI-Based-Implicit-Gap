# Error Analysis: False Positives and False Negatives

Model: gpt_4o
ROUGE-L threshold: 0.55

## Cross-model FP/FN summary

| Model | False positives | False negatives |
| --- | ---: | ---: |
| gpt4o_mini | 148 | 18 |
| gpt_4o | 33 | 18 |
| ollama | 148 | 20 |

## Summary

- **False positives:** 33
- **False negatives:** 18

## False Positive Examples (sample of 15)

- **Chunk 21:** "The mechanism remains unclear."
- **Chunk 21:** "Further research is needed to replicate these findings."
- **Chunk 88:** "In addition, more research is needed to overcome the limitation of the existing literature."
- **Chunk 177:** "Future research should replicate these findings using a broader sampling approach for the experimental manipulation."
- **Chunk 177:** "Future research should take these factors, such as prior financial behaviour, into account in order to disentangle the effects of gender from other aspects related to individual differences."
- **Chunk 177:** "Additionally, future research should aim to analyse behavioural changes over time to determine whether these effects are sustainable in the long term."
- **Chunk 236:** "Although more research is needed to understand which mechanisms explain the effectiveness of this type of social information, we consider that our findings can inspire further research on the design o..."
- **Chunk 361:** "However, evidence regarding the role of sustainability in online shopping is scarce and inconclusive."
- **Chunk 363:** "In our experiment, it remains unclear whether individuals experience cognitive dissonance as a result of the treatments."
- **Chunk 432:** "In countries where tax compliance is low and tax evasion is widespread, the specific compliance behavior of micro-business owners remains poorly understood."
- **Chunk 434:** "The mechanism remains unclear."
- **Chunk 446:** "The mechanism remains unclear."
- **Chunk 446:** "Further research is needed to replicate these findings."
- **Chunk 446:** "Little is known about long-term effects."
- **Chunk 452:** "It is an open question whether and to what extent the biases for the real variables of interest are influenced by the assumptions of linear probability weighting, risk neutrality, and no asset integra..."

## False Negative Examples (sample of 15)

- **Chunk 197:** "Baillon et al., 2020"
- **Chunk 197:** "Baucells et al., 2011)."
- **Chunk 331:** "[Open Question] (For the answers 
given, see online data set.)"
- **Chunk 335:** "Since interventions in different 
countries have yielded varying results (Blair et al., 2020"
- **Chunk 432:** "Gangl et al., 2015"
- **Chunk 432:** "Kogler et al., 2013 ) — 
micro-business owners remain an understudied yet policy-relevant 
group."
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
- **Chunk 1290:** "This includes permitting subjects to modify the
decisions produced by an algorithm or to select which information the
algorithm processes (Dietvorst et al., 2018"
- **Chunk 1290:** "Jung & Seiter, 2021"

## Failure Mode Patterns (FP)

FP predictions grouped by opening words (most common first):

- `The mechanism remains unclear....` -- 8 occurrences
- `Further research is needed to...` -- 6 occurrences
- `Little is known about long-term...` -- 3 occurrences
- `In addition, more research is...` -- 1 occurrences
- `Future research should replicate these...` -- 1 occurrences
- `Future research should take these...` -- 1 occurrences
- `Additionally, future research should aim...` -- 1 occurrences
- `Although more research is needed...` -- 1 occurrences
- `However, evidence regarding the role...` -- 1 occurrences
- `In our experiment, it remains...` -- 1 occurrences
