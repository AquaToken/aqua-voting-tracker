# Generated by Django 3.2.13 on 2022-07-26 12:37
from django.db import migrations, models
from stellar_sdk import Asset

from aqua_voting_tracker.utils.stellar.asset import get_asset_string


class Migration(migrations.Migration):

    default_asset = get_asset_string(Asset('AQUA', 'GBNZILSTVQZ4R7IKQDGHYGY2QXL5QOFJYQMXPKWRRM5PAV7Y4M67AQUA'))

    dependencies = [
        ('voting', '0006_votingsnapshot_adjusted_votes_value'),
    ]

    operations = [
        migrations.AddField(
            model_name='vote',
            name='asset',
            field=models.CharField(default=default_asset, max_length=69),
            preserve_default=False,
        ),
    ]
