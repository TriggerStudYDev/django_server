# Generated by Django 5.1.4 on 2025-02-23 15:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('server', '0005_remove_orderstatuslog_order_delete_order_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExecutorDiscipline',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(verbose_name='Описание')),
                ('min_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Минимальная цена')),
                ('max_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Максимальная цена')),
                ('preferred_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Желаемая цена')),
                ('avg_time', models.PositiveIntegerField(verbose_name='Средний срок выполнения (дней)')),
                ('guarantee_period', models.PositiveIntegerField(verbose_name='Гарантийный период (дней)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('discipline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='server.discipline', verbose_name='Дисциплина')),
                ('executor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='executor_disciplines', to='server.profile', verbose_name='Исполнитель')),
            ],
            options={
                'verbose_name': 'Дисциплина исполнителя',
                'verbose_name_plural': 'Дисциплины исполнителей',
                'unique_together': {('executor', 'discipline')},
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Название заказа')),
                ('type_order', models.CharField(choices=[('lecture', 'Lecture'), ('practical', 'Practical'), ('lab_work', 'Lab Work'), ('coursework', 'Coursework'), ('thesis', 'Thesis'), ('other', 'Other')], max_length=40, verbose_name='Тип заказа')),
                ('description', models.TextField(verbose_name='Описание заказа')),
                ('file', models.FileField(blank=True, null=True, upload_to='order/annex_order/%Y/%m/%d/', verbose_name='Приложение')),
                ('cost', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Стоимость')),
                ('status', models.CharField(choices=[('in_progress', 'In Progress'), ('under_review', 'Under Review'), ('sent_for_revision', 'Sent for Revision'), ('completed', 'Completed'), ('rejected', 'Rejected')], default='на согласовании', max_length=30, verbose_name='Статус заказа')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('last_modified_at', models.DateTimeField(auto_now=True, verbose_name='Дата последнего изменения')),
                ('deadlines', models.DateTimeField(verbose_name='Дедлайн')),
                ('warranty_period_until', models.DateTimeField(blank=True, null=True, verbose_name='Гарантийный период до')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='server.profile', verbose_name='Заказчик')),
                ('discipline', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='order.executordiscipline', verbose_name='Дисциплина')),
                ('performer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_orders', to='server.profile', verbose_name='Исполнитель')),
            ],
            options={
                'verbose_name': 'Заказ',
                'verbose_name_plural': 'Заказы',
            },
        ),
        migrations.CreateModel(
            name='OrderComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(verbose_name='Текст комментария')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата последнего изменения')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='order.order', verbose_name='Заказ')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='server.profile', verbose_name='Автор')),
            ],
            options={
                'verbose_name': 'Комментарий к заказу',
                'verbose_name_plural': 'Комментарии к заказам',
            },
        ),
        migrations.CreateModel(
            name='OrderRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Отзыв')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='order.order', verbose_name='Заказ')),
                ('rated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='given_ratings', to='server.profile', verbose_name='Кто оценил')),
                ('rated_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_ratings', to='server.profile', verbose_name='Кому поставлена оценка')),
            ],
            options={
                'verbose_name': 'Оценка заказа',
                'verbose_name_plural': 'Оценки заказов',
                'unique_together': {('order', 'rated_by')},
            },
        ),
        migrations.CreateModel(
            name='OrderResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='order.order', verbose_name='Заказ')),
            ],
            options={
                'verbose_name': 'Результат работы',
                'verbose_name_plural': 'Результат работ',
            },
        ),
        migrations.CreateModel(
            name='OrderResultFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='order/results/%Y/%m/%d/', verbose_name='Файл')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')),
                ('order_result', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='order.orderresult', verbose_name='Результат работы')),
            ],
            options={
                'verbose_name': 'Файл результата',
                'verbose_name_plural': 'Файлы результатов',
            },
        ),
        migrations.CreateModel(
            name='OrderStatusLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('in_progress', 'In Progress'), ('under_review', 'Under Review'), ('sent_for_revision', 'Sent for Revision'), ('completed', 'Completed'), ('rejected', 'Rejected')], max_length=50, verbose_name='Статус')),
                ('date_changed', models.DateTimeField(auto_now_add=True, verbose_name='Дата изменения')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Комментарий')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_logs', to='order.order', verbose_name='Заказ')),
            ],
            options={
                'verbose_name': 'Лог статуса заказа',
                'verbose_name_plural': 'Логи статусов заказов',
            },
        ),
        migrations.CreateModel(
            name='OrderRatingCriteria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criterion', models.CharField(choices=[('quality', 'Качество работы'), ('cost', 'Соотношение цены'), ('timing', 'Соблюдение сроков')], max_length=20, verbose_name='Критерий')),
                ('value', models.PositiveSmallIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], verbose_name='Оценка')),
                ('rating', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='criteria', to='order.orderrating', verbose_name='Оценка заказа')),
            ],
            options={
                'verbose_name': 'Критерий оценки',
                'verbose_name_plural': 'Критерии оценки',
                'unique_together': {('rating', 'criterion')},
            },
        ),
    ]
