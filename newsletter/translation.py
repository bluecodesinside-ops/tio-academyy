from modeltranslation.translator import translator, TranslationOptions
from .models import NewsletterSubscription

# NewsletterSubscription doesn't need translation since it contains user data
# (email, names) rather than content that needs to be translated
# But we can add it if needed in the future

