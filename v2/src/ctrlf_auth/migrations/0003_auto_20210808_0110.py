# Generated by Django 3.2.5 on 2021-08-08 01:10

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ctrlf_auth", "0002_emailauthcode"),
    ]

    operations = [
        migrations.AddField(
            model_name="emailauthcode",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="emailauthcode",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
