from django.db import migrations


SECTIONS = [
    dict(
        slug="hero_explore_title",
        order=1,
        title_en="Explore Our Programs",
        title_sq="Eksploro Programet Tona",
    ),
    dict(
        slug="hero_explore_subtitle",
        order=2,
        description_en=(
            "Discover our programs — dance, physiotherapy, and fitness. "
            "Choose your path and start your journey today!"
        ),
        description_sq=(
            "Zbuloni programet tona — kërcim, fizioterapi dhe fitnes. "
            "Zgjidhni rrugën tuaj dhe nisni udhëtimin tuaj sot!"
        ),
    ),
    dict(
        slug="why_choose_subtitle",
        order=3,
        description_en="Discover what makes our programs exceptional",
        description_sq="Zbuloni çfarë i bën programet tona të jashtëzakonshme",
    ),
    dict(
        slug="expert_instruction_description",
        order=4,
        description_en=(
            "Learn from internationally certified instructors with decades of "
            "professional experience across all our programs."
        ),
        description_sq=(
            "Mësoni nga instruktorë të certifikuar ndërkombëtarisht me dekada "
            "përvojë profesionale në të gjitha programet tona."
        ),
    ),
    dict(
        slug="proven_results_description",
        order=5,
        description_en=(
            "98% student satisfaction rate, with graduates achieving real "
            "results across every program we offer."
        ),
        description_sq=(
            "Shkalla e kënaqësisë së studentëve është 98%, me të diplomuar që "
            "arrijnë rezultate reale në çdo program që ofrojmë."
        ),
    ),
]


def forwards(apps, schema_editor):
    SiteSection = apps.get_model("courses", "SiteSection")
    for data in SECTIONS:
        SiteSection.objects.get_or_create(slug=data["slug"], defaults=data)


def backwards(apps, schema_editor):
    SiteSection = apps.get_model("courses", "SiteSection")
    SiteSection.objects.filter(
        slug__in=[d["slug"] for d in SECTIONS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0011_add_sitesection"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
