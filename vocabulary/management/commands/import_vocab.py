import csv
import os
from django.core.management.base import BaseCommand
from vocabulary.models import Vocabulary, WrongAnswer
from django.conf import settings

class Command(BaseCommand):
    help = 'Import vocabulary from CSV file'

    def handle(self, *args, **options):
        # Clear old data
        self.stdout.write('Clearing old vocabulary and wrong answers...')
        WrongAnswer.objects.all().delete()
        Vocabulary.objects.all().delete()

        csv_path = os.path.join(settings.BASE_DIR, 'vocabulary', 'data', 'vocabulary_1000.csv')
        
        self.stdout.write(f'Importing from {csv_path}...')
        count = 0
        with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # Skip header
            
            vocab_list = []
            for row in reader:
                if len(row) >= 6:
                    vocab_list.append(
                        Vocabulary(
                            english=row[1].strip(),
                            part_of_speech=row[2].strip(),
                            chinese=row[3].strip(),
                            example=row[4].strip(),
                            example_translation=row[5].strip()
                        )
                    )
                    count += 1

            Vocabulary.objects.bulk_create(vocab_list, batch_size=100)

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} words!'))
