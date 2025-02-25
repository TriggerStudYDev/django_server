# Generated by Django 5.1.4 on 2025-02-24 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_order_subject_alter_order_discipline'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='is_urgently',
            field=models.BooleanField(default=False, verbose_name='Срочный заказ?'),
        ),
        migrations.AlterField(
            model_name='orderstatuslog',
            name='status',
            field=models.CharField(choices=[('under_review', 'На рассмотрении'), ('not_accepted_executor', 'Не принят исполнителем'), ('not_accepted_customer', 'Не принят заказчиком'), ('in_progress', 'В работе'), ('sent_for_revision', 'Отправлен на доработку'), ('guaranteed_flight', 'Гарантированный переиод'), ('completed', 'Завершен'), ('rejected_executor', 'Отклонен исполнителем'), ('rejected_customer', 'Отклонен заказчиком')], max_length=50, verbose_name='Статус'),
        ),
    ]
