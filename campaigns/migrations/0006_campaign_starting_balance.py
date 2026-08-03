from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("campaigns", "0005_matchplayerstat_team"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="starting_balance",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="campaignmembership",
            name="starting_balance",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ]