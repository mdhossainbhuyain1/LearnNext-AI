from rouge_score import rouge_scorer

def rouge(reference: str, candidate: str):
    s = rouge_scorer.RougeScorer(['rouge1','rougeL'], use_stemmer=True)
    scores = s.score(reference, candidate)
    return {k: round(v.fmeasure, 4) for k, v in scores.items()}

def quiz_score(answers_user, answers_true):
    correct = sum(1 for a,b in zip(answers_user, answers_true) if a == b)
    total = len(answers_true)
    return {"correct": correct, "total": total, "accuracy": round(correct/total if total else 0, 3)}
