from django.db import migrations


POPULLORE_SLUG = "popullore"
VALLJE_SLUG = "vallje"
FIZIOTERAPI_SLUG = "fizioterapi"
MILITARY_SLUG = "military-workout"

VALLJA_COURSE_TITLES = ["vallja kukesit", "vallja napoleonit", "vallja pogonishtes"]
STRAY_FIZIOTERAPI_TITLE = "fizioterapi"


def forwards(apps, schema_editor):
    try:
        Category = apps.get_model("courses", "Category")
    except LookupError:
        return
    Course = apps.get_model("courses", "Course")

    popullore = Category.objects.filter(slug=POPULLORE_SLUG).first()
    if popullore:
        popullore.name = "Vallje"
        popullore.slug = VALLJE_SLUG
        popullore.save()
        vallje = popullore
    else:
        vallje, _ = Category.objects.get_or_create(
            slug=VALLJE_SLUG, defaults={"name": "Vallje"}
        )

    fizioterapi = Category.objects.filter(slug=FIZIOTERAPI_SLUG).first()

    for title in VALLJA_COURSE_TITLES:
        Course.objects.filter(title__iexact=title, category__isnull=True).update(
            category=vallje
        )

    if fizioterapi:
        Course.objects.filter(
            title__iexact=STRAY_FIZIOTERAPI_TITLE, category__isnull=True
        ).update(category=fizioterapi)

    Category.objects.get_or_create(
        slug=MILITARY_SLUG,
        defaults={"name": "Military Workout", "is_active": False},
    )


def backwards(apps, schema_editor):
    try:
        Category = apps.get_model("courses", "Category")
    except LookupError:
        return
    Course = apps.get_model("courses", "Course")

    Category.objects.filter(slug=MILITARY_SLUG).delete()

    vallje = Category.objects.filter(slug=VALLJE_SLUG).first()
    if vallje:
        for title in VALLJA_COURSE_TITLES:
            Course.objects.filter(title__iexact=title, category=vallje).update(
                category=None
            )
        vallje.name = "Popullore"
        vallje.slug = POPULLORE_SLUG
        vallje.save()

    fizioterapi = Category.objects.filter(slug=FIZIOTERAPI_SLUG).first()
    if fizioterapi:
        Course.objects.filter(
            title__iexact=STRAY_FIZIOTERAPI_TITLE, category=fizioterapi
        ).update(category=None)


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0004_course_description_en_course_description_sq_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
