# Generated by Django 5.0.3 on 2025-02-07 23:22

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Наименование кафедры')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='department/photo/%Y/%m/%d/', verbose_name='Фотография')),
            ],
            options={
                'verbose_name': 'Кафедра',
                'verbose_name_plural': 'Кафедры',
            },
        ),
        migrations.CreateModel(
            name='Faculty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Наименование факультета')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='faculty/photo/%Y/%m/%d/', verbose_name='Фотография')),
            ],
            options={
                'verbose_name': 'Факультет',
                'verbose_name_plural': 'Факультеты',
            },
        ),
        migrations.CreateModel(
            name='FormOfStudy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Наименование формы обучения')),
            ],
            options={
                'verbose_name': 'Форма обучения',
                'verbose_name_plural': 'Формы обучения',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Название заказа')),
                ('type_order', models.CharField(choices=[('Лекция', 'Лекция'), ('Практика', 'Практика'), ('Лабораторная', 'Лабораторная'), ('Курсовой', 'Курсовой'), ('Диплом', 'Диплом'), ('Другое', 'Другое')], max_length=40, verbose_name='Тип заказа')),
                ('description', models.TextField(verbose_name='Описание заказа')),
                ('cost', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Стоимость')),
                ('status', models.CharField(choices=[('в разработке', 'В разработке'), ('на согласовании', 'На согласовании'), ('отправлен на доработку', 'Отправлен на доработку'), ('завершен', 'Завершен'), ('отклонен', 'Отклонен')], default='на согласовании', max_length=30, verbose_name='Статус заказа')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('last_modified_at', models.DateTimeField(auto_now=True, verbose_name='Дата последнего изменения')),
                ('deadlines', models.DateTimeField(verbose_name='Дедлайн')),
                ('warranty_period_until', models.DateTimeField(blank=True, null=True, verbose_name='Гарантийный период до')),
            ],
            options={
                'verbose_name': 'Заказ',
                'verbose_name_plural': 'Заказы',
            },
        ),
        migrations.CreateModel(
            name='Rank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank_name', models.CharField(max_length=255, verbose_name='Название ранга')),
                ('rank_type', models.CharField(choices=[('customer', 'Заказчик'), ('executor', 'Исполнитель')], max_length=10, verbose_name='Тип ранга')),
                ('rank_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена ранга')),
                ('rank_image_url', models.ImageField(blank=True, null=True, upload_to='rank/photo/%Y/%m/%d/', verbose_name='Фотография')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
            ],
            options={
                'verbose_name': 'Ранг',
                'verbose_name_plural': 'Ранги',
            },
        ),
        migrations.CreateModel(
            name='ReferralSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('customer', 'Заказчик'), ('executor', 'Исполнитель')], max_length=20, verbose_name='Роль')),
                ('level', models.PositiveIntegerField(verbose_name='Уровень')),
                ('bonus_ref_user', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Зачисление реф бонусов')),
                ('bonus', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Зачисление бонусов')),
                ('required_orders', models.PositiveIntegerField(blank=True, null=True, verbose_name='Требуемое количество заказов (для заказчиков)')),
                ('required_earnings', models.PositiveIntegerField(blank=True, null=True, verbose_name='Требуемый заработок (для исполнителей)')),
                ('min_order_value', models.PositiveIntegerField(blank=True, null=True, verbose_name='Минимальная сумма заказа (для заказчиков)')),
                ('min_earning', models.PositiveIntegerField(blank=True, null=True, verbose_name='Минимальный заработок (для исполнителей)')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата последнего обновления')),
            ],
            options={
                'verbose_name': 'Настройка реферальной программы',
                'verbose_name_plural': 'Настройки реферальных программ',
            },
        ),
        migrations.CreateModel(
            name='University',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Наименование университета')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='university/photo/%Y/%m/%d/', verbose_name='Фотография')),
            ],
            options={
                'verbose_name': 'Университет',
                'verbose_name_plural': 'Университеты',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('first_name', models.CharField(default='Админ', max_length=100, verbose_name='Имя')),
                ('last_name', models.CharField(default='Админ', max_length=100, verbose_name='Фамилия')),
                ('middle_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Отчество')),
                ('role', models.CharField(choices=[('заказчик', 'Заказчик'), ('исполнитель', 'Исполнитель'), ('проверяющий', 'Проверяющий'), ('администратор', 'Администратор')], default='администратор', max_length=20, verbose_name='Роль пользователя')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('last_activity', models.DateTimeField(auto_now=True, verbose_name='Дата последней активности')),
                ('is_verification', models.BooleanField(default=False, verbose_name='Верификация')),
                ('referral_code', models.CharField(blank=True, max_length=20, null=True, unique=True, verbose_name='Реферальный код')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Пользователь',
                'verbose_name_plural': 'Пользователи',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Discipline',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Наименование дисциплины')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='discipline/photo/%Y/%m/%d/', verbose_name='Фотография')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='server.department', verbose_name='Кафедра')),
            ],
            options={
                'verbose_name': 'Дисциплина',
                'verbose_name_plural': 'Дисциплины',
            },
        ),
        migrations.AddField(
            model_name='department',
            name='faculty',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='server.faculty', verbose_name='Факультет'),
        ),
        migrations.CreateModel(
            name='FailedLoginAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('session_key', models.CharField(blank=True, max_length=40, null=True)),
                ('attempts', models.IntegerField(default=0)),
                ('last_attempt_time', models.DateTimeField(blank=True, null=True)),
                ('block_until', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OrderStatusLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('в разработке', 'В разработке'), ('на согласовании', 'На согласовании'), ('отправлен на доработку', 'Отправлен на доработку'), ('завершен', 'Завершен'), ('отклонен', 'Отклонен')], max_length=50, verbose_name='Статус')),
                ('date_changed', models.DateTimeField(auto_now_add=True, verbose_name='Дата изменения')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Комментарий')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_logs', to='server.order', verbose_name='Заказ')),
            ],
            options={
                'verbose_name': 'Лог статуса заказа',
                'verbose_name_plural': 'Логи статусов заказов',
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='user_profile_photo/%Y/%m/%d/', verbose_name='Фотография')),
                ('vk_profile', models.CharField(blank=True, max_length=100, null=True, unique=True, verbose_name='Ссылка на ВКонтакте')),
                ('telegram_username', models.CharField(blank=True, max_length=100, null=True, unique=True, verbose_name='Телеграмм')),
                ('department', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='server.department', verbose_name='Кафедра')),
                ('disciplines', models.ManyToManyField(blank=True, null=True, to='server.discipline', verbose_name='Дисциплины')),
                ('faculty', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='server.faculty', verbose_name='Факультет')),
                ('form_of_study', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='server.formofstudy', verbose_name='Форма обучения')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
                ('rank', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='server.rank', verbose_name='Ранг')),
                ('university', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='server.university', verbose_name='Университет')),
            ],
            options={
                'verbose_name': 'Профиль пользователя',
                'verbose_name_plural': 'Профили пользователей',
            },
        ),
        migrations.AddField(
            model_name='order',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='server.profile', verbose_name='Заказчик'),
        ),
        migrations.AddField(
            model_name='order',
            name='performer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_orders', to='server.profile', verbose_name='Исполнитель'),
        ),
        migrations.CreateModel(
            name='RankDescription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description_text', models.TextField(verbose_name='Описание привилегии')),
                ('privilege_type', models.CharField(choices=[('quantitative', 'Количественный'), ('unique', 'Уникальный')], max_length=15, verbose_name='Тип привилегии')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('rank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='descriptions', to='server.rank', verbose_name='Ранг')),
            ],
            options={
                'verbose_name': 'Описание ранга',
                'verbose_name_plural': 'Описания рангов',
            },
        ),
        migrations.CreateModel(
            name='Referral',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации реферала')),
                ('referred', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='referral', to=settings.AUTH_USER_MODEL, verbose_name='Приглашенный')),
                ('referrer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referrals', to=settings.AUTH_USER_MODEL, verbose_name='Пригласивший')),
            ],
            options={
                'verbose_name': 'Реферальная связь',
                'verbose_name_plural': 'Реферальные связи',
            },
        ),
        migrations.CreateModel(
            name='ReferralActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed_orders', models.PositiveIntegerField(default=0, verbose_name='Завершённые заказы')),
                ('total_earnings', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Общий заработок')),
                ('is_bonus_available', models.BooleanField(default=False, verbose_name='Бонус доступен для вывода')),
                ('bonus_earned', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Полученные бонусы')),
                ('is_bonus_claimed', models.BooleanField(default=False, verbose_name='Бонус за уровень получен')),
                ('activity_date', models.DateTimeField(auto_now_add=True, verbose_name='Дата активности')),
                ('referral', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='server.referral', verbose_name='Реферальная связь')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referral_activities', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Активность реферала',
                'verbose_name_plural': 'Активности рефералов',
                'unique_together': {('user', 'referral')},
            },
        ),
        migrations.CreateModel(
            name='ReferralBonus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Сумма бонуса')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата начисления')),
                ('referral_activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bonuses', to='server.referralactivity', verbose_name='Активность реферала')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referral_bonuses', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
                ('referral_settings', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bonuses', to='server.referralsettings', verbose_name='Настройки уровня')),
            ],
            options={
                'verbose_name': 'Реферальный бонус',
                'verbose_name_plural': 'Реферальные бонусы',
            },
        ),
        migrations.CreateModel(
            name='StudentCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_card_number', models.CharField(max_length=100, null=True, verbose_name='Номер студенческого билета')),
                ('photo', models.ImageField(upload_to='student_cards/%Y/%m/%d/', verbose_name='Фотография студенческого билета')),
                ('about_self', models.TextField(blank=True, null=True, verbose_name='О себе')),
                ('status', models.CharField(choices=[('На проверке', 'На проверке'), ('Отклонена верификация по СБ', 'Отклонена верификация по СБ'), ('Отклонена анкета исполнителя', 'Отклонена анкета исполнителя'), ('Отправлен на доработку', 'Отправлен на доработку'), ('Принят', 'Принят')], default='На проверке', max_length=60, verbose_name='Статус верификации')),
                ('profile', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='server.profile', verbose_name='Пользователь')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Верификация аккаунта',
                'verbose_name_plural': 'Верификация аккаунтов',
            },
        ),
        migrations.CreateModel(
            name='Portfolio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.FileField(upload_to='student_cards/portfolio/%Y/%m/%d/', verbose_name='Файл')),
                ('student_card', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='server.studentcard', verbose_name='Заявка на верификацию')),
            ],
            options={
                'verbose_name': 'Портфолио исполнителя (верификация)',
                'verbose_name_plural': 'Портфолио исполнителей (верификация)',
            },
        ),
        migrations.CreateModel(
            name='CustomerFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.FileField(upload_to='student_cards/customer_feedback/%Y/%m/%d/', verbose_name='Файл')),
                ('student_card', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='server.studentcard', verbose_name='Заявка на верификацию')),
            ],
            options={
                'verbose_name': 'Обратная связь от заказчика (верификация)',
                'verbose_name_plural': 'Обратные связи от заказчика (верификация)',
            },
        ),
        migrations.CreateModel(
            name='StudentCardComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(verbose_name='Комментарий')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Автор комментария')),
                ('student_card', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='server.studentcard', verbose_name='Студенческий билет')),
            ],
            options={
                'verbose_name': 'Комментарий к верификации аккаунта',
                'verbose_name_plural': 'Комментарии к верификации аккаунтов',
            },
        ),
        migrations.AddField(
            model_name='faculty',
            name='university',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='server.university', verbose_name='Университет'),
        ),
    ]
