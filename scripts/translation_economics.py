"""Token-based API list-price equivalents, never an assertion about a paid bill."""
from __future__ import annotations


def usage_cost(usage, rate, *, cold=False):
    incoming = usage['input_tokens']; cached = usage.get('cached_input_tokens', 0)
    writes = usage.get('cache_write_input_tokens', 0); outgoing = usage['output_tokens']
    assert all(type(n) is int and n >= 0 for n in [incoming, cached, writes, outgoing])
    assert cached <= incoming
    # Reasoning is already contained in output_tokens; adding it again overcharges.
    if writes:
        raise ValueError('Review nonzero cache-write accounting before quoting a total')
    if cold:
        cached = 0
    long_context = incoming > 272000
    input_multiplier = 2 if long_context else 1
    output_multiplier = 1.5 if long_context else 1
    return ((incoming-cached)*rate['input']*input_multiplier
            + cached*rate['cached_input']*input_multiplier
            + outgoing*rate['output']*output_multiplier)/1000000


def manifest_cost(manifest, pricing, *, cold=False):
    return sum(usage_cost(u, pricing['rates'][manifest['model']], cold=cold) for u in manifest['usage'])


def per_thousand(cost, source_words):
    return cost*1000/source_words if source_words else None


def pipeline_cost(*, planner, translator, audits, escalations, accepted_words, requested_words):
    total = planner+translator+sum(audits)+sum(escalations)
    return {'usd_equivalent': total, 'usd_per_1000_requested_words': per_thousand(total, requested_words),
            'usd_per_1000_model_accepted_words': per_thousand(total, accepted_words),
            'planner': planner, 'translator': translator, 'audits': sum(audits),
            'escalations': sum(escalations), 'accepted_words': accepted_words, 'requested_words': requested_words}
