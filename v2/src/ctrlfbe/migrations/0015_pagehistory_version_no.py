# Generated by Django 3.2.4 on 2021-12-17 06:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ctrlfbe", "0014_pagehistory"),
    ]

    operations = [
        migrations.AddField(
            model_name="pagehistory",
            name="version_no",
            field=models.IntegerField(default=1),
        ),
    ]
