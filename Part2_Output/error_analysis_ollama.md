# Error Analysis: False Positives and False Negatives

Model: ollama
ROUGE-L threshold: 0.55

## Cross-model FP/FN summary

| Model | False positives | False negatives |
| --- | ---: | ---: |
| gpt4o_mini | 148 | 18 |
| gpt_4o | 33 | 18 |
| ollama | 148 | 20 |

## Summary

- **False positives:** 148
- **False negatives:** 20

## False Positive Examples (sample of 15)

- **Chunk 21:** "The mechanism remains unclear."
- **Chunk 21:** "Future work should address the influence of language on task performance and how it can be leveraged for more effective management."
- **Chunk 43:** "The mechanism remains unclear."
- **Chunk 43:** "Future work should also investigate how the switching of rolls being rated less negatively than outright lying relates to Justified Dishonesty."
- **Chunk 43:** "Little is known about the specific mechanism of Justified Dishonesty, i.e. that subjects ‘‘shuffle’’ rolls when it pays to do so."
- **Chunk 43:** "Future work should also investigate how Justified Dishonesty explains behaviour, particularly in cases where it does not hold."
- **Chunk 43:** "Inconclusive results suggest that there may be an alternative explanation for the observed effects."
- **Chunk 50:** "Further research is needed."
- **Chunk 50:** "Future work should"
- **Chunk 50:** "Note: These sentences are extracted based on the phrases "remains unknown", "remains unclear", "further research is needed", "limited evidence", "no study has", "future work should", "little is known"..."
- **Chunk 88:** "In addition, more research is needed to overcome the limitation of the existing literature (Kidman et al., 2024; Liang et al., 2021)."
- **Chunk 153:** "The mechanism remains unclear."
- **Chunk 177:** "Future research should replicate these findings using a broader sampling approach for the experimental manipulation (Wells & Windschitl, 1999)."
- **Chunk 177:** "Future research should take these factors, such as prior financial behaviour, into account in order to disentangle the effects of gender from other aspects related to individual differences."
- **Chunk 177:** "Additionally, future research should aim to analyse behavioural changes over time to determine whether these effects are sustainable in the long term."

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
- **Chunk 680:** "Proestakis, Marandola, Lourenço, & van Bavel, 2024"
- **Chunk 680:** "Sconti, Caserta, & Ferrante, 2024)."
- **Chunk 959:** "As such, theoretical and empirical evidence on how both 
sets of norms influence behavior and attitudes remains inconclusive 
( D ´ Adda et al., 2016"
- **Chunk 959:** "Bic -
chieri et al., 2023 )."
- **Chunk 1034:** "Informal risk 
sharing has been documented in the field ( Fafchamps & Lund, 2003"
- **Chunk 1034:** "De 
Weerdt & Dercon, 2006 ) and in controlled experiments ( Barr & Genicot, 
2008"
- **Chunk 1034:** "Charness & Genicot, 2009 ), but little is known about its possible 
influence on cooperation."
- **Chunk 1181:** "Frank et al."
- **Chunk 1193:** "however,
the evidence on the nature of that impact is inconclusive and appears to
be situationally dependent."

## Failure Mode Patterns (FP)

FP predictions grouped by opening words (most common first):

- `Little is known about the...` -- 16 occurrences
- `Little is known about long-term...` -- 9 occurrences
- `The mechanism remains unclear....` -- 8 occurrences
- `Further research is needed to...` -- 8 occurrences
- `Future work should focus on...` -- 7 occurrences
- `Future work should investigate the...` -- 4 occurrences
- `Future work should investigate how...` -- 4 occurrences
- `Little is known about how...` -- 3 occurrences
- `Future work should also investigate...` -- 2 occurrences
- `Future work should aim to...` -- 2 occurrences
