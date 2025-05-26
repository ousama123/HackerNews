import math
import re
from collections import Counter

import pandas as pd

from src.rag import run_rag


def cosine_similarity(text1, text2):
    """Calculate cosine similarity between two texts"""
    text1, text2 = [re.sub(r"[^\w\s]", "", t.lower()).split() for t in [text1, text2]]
    if not text1 or not text2:
        return 0.0

    all_words = set(text1 + text2)
    freq1, freq2 = Counter(text1), Counter(text2)
    vector1 = [freq1.get(word, 0) for word in all_words]
    vector2 = [freq2.get(word, 0) for word in all_words]

    dot_product = sum(a * b for a, b in zip(vector1, vector2))
    magnitude1 = math.sqrt(sum(a * a for a in vector1))
    magnitude2 = math.sqrt(sum(b * b for b in vector2))

    return 0.0 if magnitude1 == 0 or magnitude2 == 0 else dot_product / (magnitude1 * magnitude2)


df = pd.read_csv("src/data/evaluate.csv")

for i, row in df.iterrows():
    question = row["Question"]
    rag_answer = run_rag(question)
    df.at[i, "rag_answer"] = rag_answer
    df.at[i, "score"] = round(cosine_similarity(row["Answer"], rag_answer), 4)
    print(f"Processed {i + 1}/{len(df)}: {question[:50]}...")

df.to_csv("src/data/evaluate_results.csv", index=False)
print("Done! Results saved to src/data/evaluate_results.csv")
