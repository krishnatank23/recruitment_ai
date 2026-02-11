def ranking_agent(state):
    accepted = [
        c for c in state["job_fit_results"]
        if c["decision"] == "ACCEPT"
    ]

    accepted.sort(key=lambda x: x["final_score"], reverse=True)

    for i, c in enumerate(accepted, start=1):
        c["rank"] = i

    state["ranking"] = accepted
    return state
