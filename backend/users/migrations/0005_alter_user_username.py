# Generated by Django 3.2.16 on 2024-02-02 23:15

from django.db import migrations, models
import users.validators


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_follow'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=150, unique=True, validators=[users.validators.validate_username], verbose_name='Имя пользователя'),
        ),
    ]