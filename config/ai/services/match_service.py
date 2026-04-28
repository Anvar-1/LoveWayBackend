def calculate_match_score(user, candidate) -> dict:
    score = 0
    reasons = []

    if user.city == candidate.city:
        score += 20
        reasons.append("bir xil hudud")

    common_interests = set(user.interests.values_list("name", flat=True)) & set(
        candidate.interests.values_list("name", flat=True)
    )
    if common_interests:
        score += min(len(common_interests) * 10, 40)
        reasons.append("o'xshash qiziqishlar")

    age_diff = abs(user.age - candidate.age)
    if age_diff <= 3:
        score += 20
        reasons.append("yosh yaqin")

    score = min(score, 100)

    return {
        "score": score,
        "reasons": reasons
    }