# Generated by Django 3.2.16 on 2023-01-20 22:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0003_city'),
    ]

    operations = [
        migrations.AddField(
            model_name='city',
            name='wiki_link',
            field=models.URLField(default=''),
        ),
        migrations.AlterField(
            model_name='city',
            name='latitude',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='city',
            name='longitude',
            field=models.FloatField(),
        ),
    ]
