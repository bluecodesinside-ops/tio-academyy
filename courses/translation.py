from modeltranslation.translator import translator, TranslationOptions
from .models import Course, Level, Packet, Session


class CourseTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


class LevelTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


class SessionTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


class PacketTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


translator.register(Course, CourseTranslationOptions)
translator.register(Level, LevelTranslationOptions)
translator.register(Session, SessionTranslationOptions)
translator.register(Packet, PacketTranslationOptions)
