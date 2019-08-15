from django.core.management.base import BaseCommand
from dashboard.common.db_util import canvas_id_to_incremented_id
from dashboard.nlp.course_discussions import process_course_discussions

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--course_id', dest='course_id', type=int, required=True)

    def handle(self, *args, **options):
        course_id = options.get('course_id')
        prefixed_course_id = canvas_id_to_incremented_id(course_id)
        process_course_discussions(prefixed_course_id)