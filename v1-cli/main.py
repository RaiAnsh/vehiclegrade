"""FlipIQ V1 - marketplace intelligence for used iPhone listings.

Run with: python main.py
"""

from src.analysis import load_listings, average_price_by_model, cheapest_listing
from src.filters import filter_by_budget
from src.scoring import score_listing, classify_deal, suggest_offer

DATA_PATH = "data/listings.json"


def format_listing(listing):
    """Return a one-line summary of a listing."""
    lock_status = "unlocked" if listing["unlocked"] else "locked"
    return (
        f"[#{listing['id']}] {listing['model']} {listing['storage']}GB - "
        f"${listing['price']} | battery {listing['battery_health']}% | "
        f"{listing['condition']} | {lock_status} | {listing['location']} | "
        f"seller {listing['seller_rating']} | {listing['days_listed']} days listed"
    )


def show_all_listings(listings):
    print(f"\nAll listings ({len(listings)}):")
    for listing in listings:
        print("  " + format_listing(listing))


def show_listings_under_budget(listings):
    try:
        budget = float(input("Enter your budget: $"))
    except ValueError:
        print("Please enter a number.")
        return

    matches = filter_by_budget(listings, budget)
    if not matches:
        print(f"No listings found under ${budget:.0f}.")
        return

    print(f"\nListings under ${budget:.0f} ({len(matches)}):")
    for listing in matches:
        print("  " + format_listing(listing))


def show_average_prices(listings):
    print("\nAverage price by model:")
    for model, average in sorted(average_price_by_model(listings).items()):
        print(f"  {model}: ${average:.2f}")


def show_cheapest(listings):
    print("\nCheapest listing:")
    print("  " + format_listing(cheapest_listing(listings)))


def show_deal_analysis(listings):
    """Score every listing and print them from best deal to worst."""
    averages = average_price_by_model(listings)

    scored = []
    for listing in listings:
        score, reasons = score_listing(listing, averages)
        scored.append((score, listing, reasons))

    scored.sort(key=lambda item: item[0], reverse=True)

    print("\nDeal analysis (best first):")
    for score, listing, reasons in scored:
        verdict = classify_deal(score)
        offer = suggest_offer(listing, averages)

        print("\n" + "-" * 70)
        print(f"  {format_listing(listing)}")
        print(f"  Deal score: {score}/100  ->  {verdict}")
        print(f"  Suggested offer: ${offer}")
        print("  Why:")
        for reason in reasons:
            print(f"    - {reason}")


def main():
    listings = load_listings(DATA_PATH)

    menu = (
        "\n=== FlipIQ - iPhone Deal Finder ===\n"
        "1. Show all listings\n"
        "2. Show listings under my budget\n"
        "3. Show average price by model\n"
        "4. Show the cheapest listing\n"
        "5. Analyze deals (scores, offers, explanations)\n"
        "6. Quit"
    )

    while True:
        print(menu)
        choice = input("Choose an option: ").strip()

        if choice == "1":
            show_all_listings(listings)
        elif choice == "2":
            show_listings_under_budget(listings)
        elif choice == "3":
            show_average_prices(listings)
        elif choice == "4":
            show_cheapest(listings)
        elif choice == "5":
            show_deal_analysis(listings)
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("Invalid option, please choose 1-6.")


if __name__ == "__main__":
    main()
