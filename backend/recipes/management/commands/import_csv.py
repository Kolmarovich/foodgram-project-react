import csv
import os
from django.core.management.base import BaseCommand
from recipes.models import Ingredient
from django.conf import settings


class Command(BaseCommand):
    """Загрузка ингредиентов из csv в БД."""
    def handle(self, *args, **options):
        Ingredient.objects.all().delete()
        file_path = os.path.join(
            settings.BASE_DIR, '..', 'data', 'ingredients.csv'
            )
        with open(file_path, encoding='UTF-8') as file:
            reader = csv.reader(file)
            for row in reader:
                ingredient = Ingredient(
                    name=row[0],
                    measurement_unit=row[1],
                )
                ingredient.save()