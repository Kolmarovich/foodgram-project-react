# Generated by Django 3.2.16 on 2024-02-03 17:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20240203_1954'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='no_self_follow',
        ),
        migrations.RemoveConstraint(
            model_name='follow',
            name='unique_follow',
        ),
    ]