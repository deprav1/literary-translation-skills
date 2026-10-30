"""Development-only economic gate, fixed before observing model output."""
from __future__ import annotations

from collections import Counter


def gate(*, calibration_pass, route, anchor_route, prose_losses, corpus_items):
    requested = route['accounting']['cold']['requested_words']
    cost = route['accounting']['cold']['usd_equivalent']
    anchor_cost = anchor_route['accounting']['cold']['usd_equivalent']
    complete = not route['unresolved_flags'] and all(r['model_accepted'] for r in route['final_items'])
    # Every raw major/critical is escalated or remains an unresolved flag. The
    # final receipt therefore cannot silently accept an item with an open major.
    conditions = {'calibrated': calibration_pass, 'no_unresolved_production_flags': complete,
        'major_density_margin': complete and not anchor_route['unresolved_flags'],
        'prose_loss_bound': prose_losses/corpus_items <= .10,
        'cold_cost_saving': cost <= .8*anchor_cost,
        'positive_denominator': requested > 0 and route['accounting']['cold']['accepted_words'] > 0}
    return {'development_economic_gate': all(conditions.values()), 'conditions': conditions,
            'cold_saving_fraction': 1-cost/anchor_cost if anchor_cost else None,
            'prose_losses': prose_losses, 'corpus_items': corpus_items,
            'claim': 'Observed model-audited development pipeline only; no automatic deployment or human certification.'}
