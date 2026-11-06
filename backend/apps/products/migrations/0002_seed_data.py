"""
Idempotent demo data seed: a demo user (demo@example.com / demo12345) and a
18-row product catalog across 4 categories (electronics, home goods, outdoor
gear, books), with each product's embedding computed and stored at seed
time via the same apps.common.ai.get_embedding() used everywhere else.

Without OPENAI_API_KEY configured (the default for this environment), these
embeddings are the deterministic stub described in apps/common/ai.py - fine
for exercising the full pipeline, but not semantically meaningful.

Safe to run repeatedly: get_or_create() on the user's email and an
existence check per (user, name) product pair mean re-running `migrate`
never creates duplicates.
"""
from django.contrib.auth.hashers import make_password
from django.db import migrations

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo12345"

PRODUCTS = [
    # --- electronics ---
    {
        "name": "Wireless Noise-Cancelling Headphones",
        "description": (
            "Over-ear headphones with active noise cancellation and 30-hour battery life. "
            "Built-in microphone and touch controls make it easy to take calls and skip "
            "tracks without reaching for your phone."
        ),
        "category": "electronics",
        "price": "249.99",
    },
    {
        "name": "Smart Fitness Watch",
        "description": (
            "Track heart rate, sleep, and workouts with this lightweight fitness watch. "
            "Syncs with your phone to show notifications and has a battery that lasts up "
            "to seven days."
        ),
        "category": "electronics",
        "price": "179.99",
    },
    {
        "name": "Portable Bluetooth Speaker",
        "description": (
            "Compact speaker with surprisingly deep bass and a rugged, waterproof shell. "
            "Pair two together for stereo sound at your next outdoor gathering."
        ),
        "category": "electronics",
        "price": "59.99",
    },
    {
        "name": "4K Streaming Media Player",
        "description": (
            "Stream your favorite shows in crisp 4K HDR with this plug-and-play media "
            "player. Comes with a voice remote and supports all the major streaming apps."
        ),
        "category": "electronics",
        "price": "49.99",
    },
    {
        "name": "Mechanical Gaming Keyboard",
        "description": (
            "Tactile mechanical switches and per-key RGB lighting make this keyboard a "
            "favorite for gamers and typists alike. Durable aluminum frame is built to "
            "withstand years of daily use."
        ),
        "category": "electronics",
        "price": "89.99",
    },
    # --- home goods ---
    {
        "name": "Ceramic Nonstick Cookware Set",
        "description": (
            "A 10-piece cookware set with a ceramic nonstick coating that's free of PFOA "
            "and PTFE. Oven-safe up to 500 degrees and compatible with all stovetops "
            "including induction."
        ),
        "category": "home goods",
        "price": "129.99",
    },
    {
        "name": "Memory Foam Pillow",
        "description": (
            "Contoured memory foam pillow that cradles your neck and shoulders for better "
            "spinal alignment. The breathable cover keeps you cool through the night and "
            "is machine washable."
        ),
        "category": "home goods",
        "price": "39.99",
    },
    {
        "name": "Automatic Drip Coffee Maker",
        "description": (
            "Brew a full pot of coffee with a built-in grinder and programmable timer, so "
            "it's ready the moment you wake up. The thermal carafe keeps coffee hot for "
            "hours without a hot plate."
        ),
        "category": "home goods",
        "price": "69.99",
    },
    {
        "name": "Bamboo Cutting Board Set",
        "description": (
            "Three sustainably sourced bamboo cutting boards in graduated sizes, perfect "
            "for meal prep and serving. Naturally antimicrobial and gentle on knife edges."
        ),
        "category": "home goods",
        "price": "34.99",
    },
    # --- outdoor gear ---
    {
        "name": "2-Person Backpacking Tent",
        "description": (
            "Lightweight, weatherproof tent that sets up in under five minutes and packs "
            "down small enough for any backpack. Double-wall construction keeps "
            "condensation out even in heavy rain."
        ),
        "category": "outdoor gear",
        "price": "189.99",
    },
    {
        "name": "Insulated Stainless Steel Water Bottle",
        "description": (
            "Double-wall vacuum insulation keeps drinks cold for 24 hours or hot for 12. "
            "The wide mouth makes it easy to add ice cubes or clean with a bottle brush."
        ),
        "category": "outdoor gear",
        "price": "24.99",
    },
    {
        "name": "Trail Running Hydration Vest",
        "description": (
            "A snug-fitting vest with multiple pockets for water bottles, snacks, and a "
            "phone, designed to stay put even on technical trails. Reflective trim adds "
            "visibility for early morning or evening runs."
        ),
        "category": "outdoor gear",
        "price": "74.99",
    },
    {
        "name": "Compact Camping Hammock",
        "description": (
            "Ripstop nylon hammock that packs into its own stuff sack, light enough to "
            "bring on any backpacking trip. Rated to hold up to 400 pounds and includes "
            "tree-friendly straps."
        ),
        "category": "outdoor gear",
        "price": "44.99",
    },
    {
        "name": "Rechargeable Camping Lantern",
        "description": (
            "A collapsible lantern that puts out 360 degrees of warm light and recharges "
            "via USB, with a battery that lasts up to 48 hours on low. Doubles as a power "
            "bank for your phone in a pinch."
        ),
        "category": "outdoor gear",
        "price": "29.99",
    },
    # --- books ---
    {
        "name": "The Pragmatic Programmer",
        "description": (
            "A classic guide to software craftsmanship, covering everything from version "
            "control habits to debugging mindset. Still relevant decades after its first "
            "printing, it's often recommended for new and experienced developers alike."
        ),
        "category": "books",
        "price": "34.99",
    },
    {
        "name": "Atomic Habits",
        "description": (
            "A practical framework for building good habits and breaking bad ones, built "
            "around small, consistent changes. Draws on psychology and real-world case "
            "studies to make the advice stick."
        ),
        "category": "books",
        "price": "16.99",
    },
    {
        "name": "A Brief History of Time",
        "description": (
            "Stephen Hawking's accessible explanation of cosmology, from the Big Bang to "
            "black holes. Written for a general audience, it remains one of the "
            "best-selling science books of all time."
        ),
        "category": "books",
        "price": "18.99",
    },
    {
        "name": "The Silent Patient",
        "description": (
            "A psychological thriller about a woman who stops speaking after a shocking "
            "act of violence, and the therapist determined to understand why. Twists keep "
            "readers guessing until the final pages."
        ),
        "category": "books",
        "price": "14.99",
    },
]


def seed_demo_data(apps, schema_editor):
    # Imported here (not via the historical model, which has no custom
    # save()/business logic) so seeding goes through the exact same
    # embedding function used by the live app.
    from apps.common.ai import get_embedding

    User = apps.get_model("accounts", "User")
    Product = apps.get_model("products", "Product")

    user, created = User.objects.get_or_create(
        email=DEMO_EMAIL,
        defaults={"password": make_password(DEMO_PASSWORD), "is_active": True},
    )
    if created is False and not user.password:
        user.password = make_password(DEMO_PASSWORD)
        user.save(update_fields=["password"])

    for item in PRODUCTS:
        if Product.objects.filter(user=user, name=item["name"]).exists():
            continue
        text = f"{item['name']}\n{item['description']}"
        Product.objects.create(
            user=user,
            name=item["name"],
            description=item["description"],
            category=item["category"],
            price=item["price"],
            embedding=get_embedding(text),
        )


def reverse_noop(apps, schema_editor):
    # Deliberately not reversible: deleting demo data on migrate-back could
    # silently destroy seed data a developer has since built on top of.
    pass


class Migration(migrations.Migration):
    dependencies = [("products", "0001_initial")]

    operations = [
        migrations.RunPython(seed_demo_data, reverse_noop),
    ]
