from django.core.management.base import BaseCommand
from django.utils import translation

from courses.models import Course, Packet, Session


COURSE_TITLES = {
    'traditional-dancing': {
        'en': 'Albanian Traditional Dances',
        'sq': 'PROGRAME PER VALLET SHQIPTARE',
    },
    'fizioterapi': {
        'en': 'Movement and Wellness Programs',
        'sq': 'PROGRAME PER LEVIZJE DHE MIREQENIE',
    },
    'military': {
        'en': 'Military Calisthenics — 28 Days',
        'sq': 'Kalistenikë ushtarake — 28 ditë',
    },
}

PACKET_TITLES = {
    1: ('Restoration of cervical lordosis', 'Rikthimi i lordozes se qafes'),
    2: ('Cervical disc hernia', 'Hernia diskale e qafes'),
    3: ('Neck without stiffness', 'Qafa pa ngurtesim'),
    4: ('Cervical vertebra displacement (spondylolisthesis)', 'Spostimi i vertebrave te qafes Sponditioleza'),
    5: ('Kyphosis — restoring a straight back', 'Kifoza - rikthimi i shpines se drejte'),
    6: ('Scoliosis — restoring spinal balance', 'Skolioza - rikthim i balances se shtylles kurrizore'),
    7: ('Lumbar disc hernia (restoring waist mobility)', 'HERNIA DISKALE LUMBARE (Rikthimi i Lëvizshmërisë s Mesit)'),
    8: ('Restoring shoulder mobility — exercises and tests', 'RIKTHIMI I LËVIZSHMËRISË SË SHPATULLËS Ushtrime dhe testime për levizjen e shpatulles.'),
    9: ('Knee joints', 'ARTIKULACIONET E GJURIT'),
    10: ('Restoring balance (program for seniors)', 'RIKTHIMI I EKUILIBRIT (Program për Moshën e Tretë)'),
    11: ('Dizziness (restoring balance)', 'MARRAMENDJA(Rikthimi i Balancës)'),
    12: ('Pelvic floor muscles', 'DOBËSIMI I  MUSKUJVE PELVIKË'),
    13: ('Tinnitus (noise in the ear)', 'ZHURMA NE VESH'),
    14: ('Body map in the hands and feet', 'HARTA E TRUPIT NË DUAR DHE KËMBË'),
    15: ('Pressure points for daily relief', 'PIKAT E PRESIONIT PËR LEHTËSIM TË PËRDITSHËM'),
}

DANCE_TITLES = {
    138: ('Kukës Dance', 'vallja e kukesit'),
    139: ("Napoleon's Dance", 'vallja e napoleonit'),
    140: ('Katyushka Dance', 'vallja e katjushkes'),
    141: ('Bagpipe Dance (Gajde)', 'vallja e gajdes'),
    178: ('Rrajcë Dance', 'vallja e rrajces'),
    179: ('Pogonishte Dance', 'vallja e pogonishtes'),
}

SESSION_TITLES = {
    219: (
        'Exercise to restore cervical lordosis with the head hanging off the bed',
        '“Ushtrim për Rikthimin e Lordozës Cervikale me Kokën e Varur në Krevat',
    ),
    220: (
        'Head-hanging bed exercise for cervical disc hernia',
        'Ushtrim me Kokën e Varur nga Shtrati për Hernien Diskale të Qafës',
    ),
    256: ('Digestive problems', 'Probleme me tretjen'),
    257: ('Bringing energy into the body', 'Futja e energjise ne trup.'),
    274: ('Stomach pain or burning', 'Dhimbje ose djegie te stomakut.'),
    276: ('Stomach pain or burning', 'Dhimbje ose djegie te stomakut.'),
    275: ('Support for kidney function', 'Ndihma per funksionimin e veshkave'),
    277: ('Support for kidney function', 'Ndihma per funksionimin e veshkave'),
}


def _set_bilingual(obj, en, sq):
    obj.title_en = en
    obj.title_sq = sq
    obj.title = en
    obj.save()


class Command(BaseCommand):
    help = 'Fill English and Albanian titles for courses, packets, and dance/physio videos.'

    def handle(self, *args, **options):
        translation.activate('en')
        updated = 0

        for slug, titles in COURSE_TITLES.items():
            course = Course.objects.filter(slug=slug).first()
            if not course:
                continue
            _set_bilingual(course, titles['en'], titles['sq'])
            updated += 1
            self.stdout.write('Course %s: %s / %s' % (slug, titles['en'], titles['sq']))

        for packet_id, (en, sq) in PACKET_TITLES.items():
            packet = Packet.objects.filter(pk=packet_id).first()
            if not packet:
                continue
            _set_bilingual(packet, en, sq)
            updated += 1
            self.stdout.write('Packet %s: %s' % (packet_id, en))

        for session_id, (en, sq) in {**DANCE_TITLES, **SESSION_TITLES}.items():
            session = Session.objects.filter(pk=session_id).first()
            if not session:
                continue
            _set_bilingual(session, en, sq)
            updated += 1

        for session in Session.objects.filter(course__slug='fizioterapi', is_active=True):
            raw = (session.title_en or session.title or '').strip()
            upper = raw.upper()
            if upper.startswith('VIDEO '):
                number = raw.split(None, 1)[-1]
                _set_bilingual(session, 'Video %s' % number, 'VIDEO %s' % number)
                updated += 1
            elif upper.startswith('DITA '):
                number = raw.split(None, 1)[-1]
                _set_bilingual(session, 'Day %s' % number, 'DITA %s' % number)
                updated += 1

        self.stdout.write(self.style.SUCCESS('Updated %s records.' % updated))
