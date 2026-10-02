from flask import Flask, render_template, request, jsonify
import time, random

app = Flask(__name__)

# ── Static demo data ──────────────────────────────────────────────────────────
CANDIDATES = {
    "A": {"name": "FreshMart Weekly Bundle", "base_score": 89},
    "B": {"name": "NutriBasket Family Pack", "base_score": 76},
    "C": {"name": "GreenGrocer Essentials",  "base_score": 71},
}

REQUIREMENTS = ["budget", "family_size", "healthy", "low_sugar"]

# Relationships: candidate → requirement → initial state + resolution data
RELATIONSHIPS = {
    "A": {
        "budget":      {"state": "verified",  "value": True,              "resolver": "automation", "confidence": 97, "transition": False},
        "family_size": {"state": "verified",  "value": True,              "resolver": "automation", "confidence": 95, "transition": False},
        "healthy":     {"state": "verified",  "value": True,              "resolver": "automation", "confidence": 91, "transition": False},
        "low_sugar":   {"state": "uncertain", "value": None,              "resolver": None,         "confidence": 0,  "transition": True},
    },
    "B": {
        "budget":      {"state": "verified",  "value": True,  "resolver": "automation", "confidence": 93, "transition": False},
        "family_size": {"state": "verified",  "value": True,  "resolver": "automation", "confidence": 90, "transition": False},
        "healthy":     {"state": "verified",  "value": True,  "resolver": "automation", "confidence": 88, "transition": False},
        "low_sugar":   {"state": "verified",  "value": True,  "resolver": "automation", "confidence": 85, "transition": False},
    },
    "C": {
        "budget":      {"state": "verified",  "value": True,  "resolver": "automation", "confidence": 80, "transition": False},
        "family_size": {"state": "verified",  "value": True,  "resolver": "automation", "confidence": 82, "transition": False},
        "healthy":     {"state": "uncertain", "value": None,  "resolver": None,         "confidence": 0,  "transition": True},
        "low_sugar":   {"state": "uncertain", "value": None,  "resolver": None,         "confidence": 0,  "transition": True},
    },
}

def score_candidate(cid, rels):
    rel = rels[cid]
    verified = sum(1 for r in rel.values() if r["state"] == "verified" and r["value"])
    total = len(rel)
    base = CANDIDATES[cid]["base_score"]
    return round(base * (verified / total), 1)

def build_decision_graph(rels):
    graph = {"requirements": REQUIREMENTS, "candidates": [], "relationships": []}
    for cid, cdata in CANDIDATES.items():
        score = score_candidate(cid, rels)
        graph["candidates"].append({"id": cid, "name": cdata["name"], "score": score})
    graph["candidates"].sort(key=lambda x: x["score"], reverse=True)
    for cid, reqs in rels.items():
        for req, rdata in reqs.items():
            graph["relationships"].append({
                "id": f"rel-{cid}-{req}",
                "candidate": cid,
                "requirement": req,
                "state": rdata["state"],
                "value": rdata["value"],
                "resolver": rdata["resolver"],
                "confidence": rdata["confidence"],
                "transition": rdata["transition"],
            })
    return graph

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search", methods=["POST"])
def search():
    data = request.json
    query = data.get("query", "")
    chips = data.get("chips", [])

    import copy
    rels = copy.deepcopy(RELATIONSHIPS)

    # Before resolution rankings
    before = [{"id": c, "name": CANDIDATES[c]["name"], "score": score_candidate(c, rels)}
              for c in CANDIDATES]
    before.sort(key=lambda x: x["score"], reverse=True)

    # Detect uncertainties
    uncertainties = []
    for cid, reqs in rels.items():
        for req, rdata in reqs.items():
            if rdata["state"] == "uncertain":
                impact = round(random.uniform(0.7, 1.0), 2)
                criticality = round(random.uniform(0.85, 0.95), 2)
                uncertainties.append({
                    "rel_id": f"rel-{cid}-{req}",
                    "candidate": cid,
                    "requirement": req,
                    "impact": impact,
                    "criticality": criticality,
                })

    # Resolve uncertainties (automation for low_sugar, AI for healthy)
    resolution_steps = []
    for u in uncertainties:
        cid, req = u["candidate"], u["requirement"]
        if req == "low_sugar":
            resolver, method = "automation", "product_specification_check"
            evidence = "sugar 2.1 g per 100 g"
            confidence = 94
            value = True
        else:
            resolver, method = "AI", "description_analysis"
            evidence = "product description analysis"
            confidence = 82
            value = True

        rels[cid][req]["state"] = "verified"
        rels[cid][req]["value"] = value
        rels[cid][req]["resolver"] = resolver
        rels[cid][req]["confidence"] = confidence

        resolution_steps.append({
            "rel_id": u["rel_id"],
            "candidate": cid,
            "requirement": req,
            "resolver": resolver,
            "method": method,
            "evidence": evidence,
            "confidence": confidence,
            "impact": u["impact"],
            "criticality": u["criticality"],
            "from_state": "uncertain",
            "to_state": "verified",
        })

    # After resolution rankings
    after = [{"id": c, "name": CANDIDATES[c]["name"], "score": score_candidate(c, rels)}
             for c in CANDIDATES]
    after.sort(key=lambda x: x["score"], reverse=True)

    graph = build_decision_graph(rels)

    basket = [
        {"group": "Weekly groceries (healthy essentials)", "items": 8,  "qty": 1},
        {"group": "Low-sugar products (verified preference match)", "items": 6, "qty": 1},
        {"group": "Family staples (suitable for 4 people)", "items": 5,  "qty": 1},
    ]

    winner = after[0]
    total = 2816
    saving = 316

    return jsonify({
        "query": query,
        "chips": chips,
        "before_ranking": before,
        "after_ranking": after,
        "resolution_steps": resolution_steps,
        "decision_graph": graph,
        "basket": basket,
        "winner": winner,
        "total": total,
        "saving": saving,
        "match_score": 100,
        "checks": [
            "Fits your stated budget",
            "Matches your preferences",
            "Availability checked",
            "Important information verified",
        ],
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
