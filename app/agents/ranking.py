def ranking_agent(state):
    accepted = [
        c for c in state["job_fit_results"]
        if c["decision"] == "ACCEPT"
    ]

    # prefer composite_score (persona-aware) if available, else final_score
    def sort_key(x):
        return x.get("composite_score") if x.get("composite_score") is not None else x.get("final_score", 0)

    accepted.sort(key=lambda x: sort_key(x), reverse=True)

    for i, c in enumerate(accepted, start=1):
        c["rank"] = i

    state["ranking"] = accepted
    return state
