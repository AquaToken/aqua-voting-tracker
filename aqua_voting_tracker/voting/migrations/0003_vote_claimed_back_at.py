# Generated by Django 3.2.9 on 2021-12-06 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0002_votingsnapshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='vote',
            name='claimed_back_at',
            field=models.DateTimeField(null=True),
        ),
    ]
