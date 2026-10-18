from django.db.models.signals import post_save
from django.dispatch import receiver

from courses.models import Packet, Session


@receiver(post_save, sender=Packet)
def sync_packet_to_catalog(sender, instance, **kwargs):
    from catalog.services.sync import sync_course_packet
    sync_course_packet(instance)


@receiver(post_save, sender=Session)
def sync_packet_videos_to_catalog(sender, instance, **kwargs):
    if not instance.packet_id:
        return
    from catalog.services.sync import sync_course_packet
    sync_course_packet(instance.packet)
