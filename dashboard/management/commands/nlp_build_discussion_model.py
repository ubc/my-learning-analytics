from django.core.management.base import BaseCommand
from dashboard.nlp.build_models import build_discussion_model

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--model_id', dest='model_id', type=int, required=True)

    def handle(self, *args, **options):
        model_id = options.get('model_id')
        build_discussion_model(model_id)