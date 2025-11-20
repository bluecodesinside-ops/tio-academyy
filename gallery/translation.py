from modeltranslation.translator import translator, TranslationOptions
from .models import Photo, Video


class PhotoTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


class VideoTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


translator.register(Photo, PhotoTranslationOptions)
translator.register(Video, VideoTranslationOptions)
