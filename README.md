# FinQAExperiments


FinQA: https://github.com/czyssrs/finqa


Initial experiments with FinQA.

| Model | Method |Pormpt Choice | Program Accuracy | Execution accuracy |
|---|---|---|---|---|
| gpt-3.5-turbo | One-shot + Prompt | Choice 1 |  22.14% | 26.24% |
| gpt-3.5-turbo | One-shot + Prompt (not strict) | Choice 1 | 24.06% | 57.45% |
| gpt-4 | One-shot + Prompt (not strict, GPT3.5 wrong examples) | Choice 1 | 36.88% | **75.68%** |
|---|---|---|---|---|
| gpt-3 davinci | One-shot + Prompt (not strict) | Choice 1 | 13.16% | 15.87% |
| gpt-3 davinci | Finetune + Prompt (not strict) | Finetune + Choice 1 | 51.09% | 57.98% |
|---|---|---|---|---|
| llama-7b | One-shot + Prompt (not strict) | Choice 1 | 7.15% | 8.63% |
| Koala-7b | One-shot + Prompt (not strict) | Choice 1 | 6.45% | 5.23% |
| Vicuna-7b | One-shot + Prompt (not strict) | Choice 1 | 6.10% | 7.59% |
| Vicuna-7b | One-shot + Prompt (not strict) | Choice 1 + Vicuna 1.1 | 5.93% | 7.24% |
| llama-13b | One-shot + Prompt (not strict) | Choice 1 | 9.68% | 12.03% |
| llama-65b | One-shot + Prompt (not strict) | Choice 1 | 15.71% | 19.09% |
|---|---|---|---|---|
| FinQA (roberta-large) | Finetune + Retriever (not strict) | --- | 58.86% | 61.24% | 
| Human Expert | Expert + Retriever (not strict) | --- | 87.49% | 91.16% | 