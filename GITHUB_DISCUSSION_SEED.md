# Design Trade-offs: Determinism vs LLM Routing

One of the core architectural decisions in this project is how to balance **deterministic routing** with **LLM-assisted classification**.

## The Trade-off

### Pure Deterministic Routing
**Pros:**
- Predictable behavior
- Zero LLM cost for routing
- Fast response times
- Easy to debug and test

**Cons:**
- Brittle keyword matching
- Poor handling of natural language variations
- Requires constant rule updates

### Pure LLM Routing
**Pros:**
- Handles natural language well
- Adapts to variations automatically
- No manual rule maintenance

**Cons:**
- Adds latency to every request
- Increases cost significantly
- Non-deterministic behavior
- Harder to debug failures

## Our Hybrid Approach

This project uses a **two-tier system**:

1. **Fast deterministic check first** - Keyword matching for obvious cases
2. **LLM classification as fallback** - For ambiguous or complex queries

See [`core/intent_classifier.py`](core/intent_classifier.py) for implementation.

### Why This Works

- **Cost optimization**: ~70% of queries hit deterministic rules (zero LLM cost)
- **Quality**: Complex queries still get intelligent routing
- **Observability**: Clear logs show which path was taken
- **Tunable**: Can adjust the balance based on production metrics

## Open Questions

1. **Should we add a confidence threshold?**  
   Currently, if deterministic matching fails, we always call the LLM. Should we have a "confidence score" that triggers human review for ambiguous cases?

2. **Should routing be cached?**  
   Similar queries could reuse previous routing decisions. Trade-off: memory vs cost.

3. **Should we support multi-intent queries?**  
   Currently, we route to a single agent. Should we support queries that need multiple agents?

## Your Thoughts?

What trade-offs have you encountered in agent routing? How would you approach this differently?

---

**Related Documentation:**
- [Intent Classification](docs/CONTEXT_FOR_AI.md#intent-classification)
- [Agent Router](core/agent_router.py)
- [Multi-LLM Strategy](docs/MULTI_LLM_STRATEGY.md)
