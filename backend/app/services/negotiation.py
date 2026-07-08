"""Negotiation Assistant: a suggested opening offer, the reasoning behind it,
and a ready-to-send message - all built from templates, not a live LLM call.
Keeps the "zero ML, fully explainable" identity of the rest of the engine.
"""

from app.services.deal_engine import suggest_offer


def build_negotiation(listing, market_value):
    offer = suggest_offer(listing, market_value)

    if listing.price <= market_value:
        reasoning = (
            f"This listing is already priced at or below its estimated market value of "
            f"${market_value:,.0f}, so a modest discount is a reasonable opening offer."
        )
    else:
        overage = listing.price - market_value
        reasoning = (
            f"This listing is priced ${overage:,.0f} above its estimated market value of "
            f"${market_value:,.0f}. Anchoring the offer back toward market value gives room "
            f"to negotiate."
        )

    pickup_clause = ", if I can arrange pickup this week" if listing.days_listed > 3 else ""
    make = listing.generation.model.make.name
    model_name = listing.generation.model.name
    message = (
        f"Hi! I'm interested in the {listing.year} {make} {model_name}. Based on its mileage "
        f"({listing.mileage_km:,} km) and current market pricing, I'd like to offer ${offer:,}"
        f"{pickup_clause}. Let me know if that works!"
    )

    return {
        "suggested_offer": offer,
        "reasoning": reasoning,
        "message": message,
    }
