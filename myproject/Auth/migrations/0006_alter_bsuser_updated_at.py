# Generated by Django 5.0.4 on 2024-04-22 18:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Auth', '0005_alter_bsuser_updated_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bsuser',
            name='updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]