import csv
import os
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Загрузка ингредиентов из csv в БД."""
    def handle(self, *args, **options):
        Ingredient.objects.all().delete()
        file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'ingredients.csv'
        )
        with open(file_path, encoding='UTF-8') as file:
            reader = csv.reader(file)
            for name, measurement_unit in reader:
                ingredient = Ingredient(
                    name=name,
                    measurement_unit=measurement_unit,
                )
                ingredient.save()
