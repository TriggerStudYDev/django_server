# Generated by Django 5.0.3 on 2025-02-12 20:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rank', '0001_initial'),
        ('server', '0003_ranksettings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='rank',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='rank.rank', verbose_name='Ранг'),
        ),
        migrations.RemoveField(
            model_name='rankdescription',
            name='rank',
        ),
        migrations.DeleteModel(
            name='RankSettings',
        ),
        migrations.DeleteModel(
            name='Rank',
        ),
        migrations.DeleteModel(
            name='RankDescription',
        ),
    ]
