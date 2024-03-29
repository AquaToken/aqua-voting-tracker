# Generated by Django 3.2.9 on 2021-12-15 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0003_vote_claimed_back_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='votingsnapshot',
            name='downvote_value',
            field=models.DecimalField(decimal_places=7, default=0, max_digits=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='votingsnapshot',
            name='upvote_value',
            field=models.DecimalField(decimal_places=7, default=0, max_digits=20),
            preserve_default=False,
        ),
    ]
