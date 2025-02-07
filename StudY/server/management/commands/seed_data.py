from django.core.management.base import BaseCommand

from server.models import *


class Command(BaseCommand):
    help = "Заполняет базу данных начальными данными"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Начало заполнения базы данных..."))

        # Университеты
        university = University.objects.create(name="МГУ имени М.В. Ломоносова")
        self.stdout.write(self.style.SUCCESS(f"Создан университет: {university.name}"))

        # Факультеты
        faculty = Faculty.objects.create(university=university, name="Факультет вычислительной математики и кибернетики")
        self.stdout.write(self.style.SUCCESS(f"Создан факультет: {faculty.name}"))

        # Кафедры
        department = Department.objects.create(faculty=faculty, name="Кафедра математической кибернетики")
        self.stdout.write(self.style.SUCCESS(f"Создана кафедра: {department.name}"))

        # Дисциплины
        discipline = Discipline.objects.create(department=department, name="Машинное обучение")
        self.stdout.write(self.style.SUCCESS(f"Создана дисциплина: {discipline.name}"))

        # Формы обучения
        FormOfStudy.objects.create(name="Бакалавр")
        FormOfStudy.objects.create(name="Магистр")
        FormOfStudy.objects.create(name="Специалитет")
        FormOfStudy.objects.create(name="Аспирантура")
        self.stdout.write(self.style.SUCCESS("Созданы формы обучения"))

        # Настройки реферальной программы
        ReferralSettings.objects.create(role="customer", level=1, bonus_ref_user=300, bonus=5.00, required_orders=10, min_order_value=500)
        ReferralSettings.objects.create(role="executor", level=1, bonus_ref_user=300, bonus=7.50, required_earnings=2000, min_earning=300)

        rank_customer_1 = Rank.objects.create(
            rank_name="Студент",
            rank_type="customer",
            rank_price=0,
        )
        RankDescription.objects.create(
            rank=rank_customer_1,
            description_text="Нет привилегий",
            privilege_type="quantitative"
        )
        self.stdout.write(self.style.SUCCESS(f"Создан ранга: {rank_customer_1.rank_name}"))

        rank_customer_2 = Rank.objects.create(
            rank_name="Исследователь",
            rank_type="customer",
            rank_price=1500,
        )
        RankDescription.objects.create(
            rank=rank_customer_2,
            description_text="Скидка на заказы: 2%<br>Скидка на внутренние покупки: 5%<br>Бонусная программа: 5% для меня, 10% для привлечённых",
            privilege_type="quantitative"
        )
        RankDescription.objects.create(
            rank=rank_customer_2,
            description_text="Доступ к статистике рыночных цен",
            privilege_type="unique"
        )
        self.stdout.write(self.style.SUCCESS(f"Создан ранга: {rank_customer_2.rank_name}"))

        rank_customer_3 = Rank.objects.create(
            rank_name="Эксперт",
            rank_type="customer",
            rank_price=5000,
        )
        RankDescription.objects.create(
            rank=rank_customer_3,
            description_text="Скидка на заказы: 5%<br>Скидка на внутренние покупки: 10%<br>Бонусная программа: 10% для меня, 15% для привлечённых",
            privilege_type="quantitative"
        )
        RankDescription.objects.create(
            rank=rank_customer_3,
            description_text="Доступ к статистике рыночных цен и истории цен",
            privilege_type="unique"
        )
        self.stdout.write(self.style.SUCCESS(f"Создан ранга: {rank_customer_3.rank_name}"))

        rank_customer_4 = Rank.objects.create(
            rank_name="Магистр",
            rank_type="customer",
            rank_price=8000,
        )
        RankDescription.objects.create(
            rank=rank_customer_4,
            description_text="Скидка на заказы: 7%<br>Скидка на внутренние покупки: 15%<br>Бонусная программа: 15% для меня, 20% для привлечённых",
            privilege_type="quantitative"
        )
        RankDescription.objects.create(
            rank=rank_customer_4,
            description_text="Доступ к статистике рыночных цен, истории цен и прогнозам",
            privilege_type="unique"
        )
        self.stdout.write(self.style.SUCCESS(f"Создан ранга: {rank_customer_4.rank_name}"))

        rank_customer_5 = Rank.objects.create(
            rank_name="Профессор",
            rank_type="customer",
            rank_price=15000,
        )
        RankDescription.objects.create(
            rank=rank_customer_5,
            description_text="Скидка на заказы: 10%<br>Скидка на внутренние покупки: 20%<br>Бонусная программа: 20% для меня, 30% для привлечённых",
            privilege_type="quantitative"
        )
        RankDescription.objects.create(
            rank=rank_customer_5,
            description_text="Доступ к статистике рыночных цен, истории цен, прогнозам и аналитическим отчетам",
            privilege_type="unique"
        )
        self.stdout.write(self.style.SUCCESS(f"Создан ранга: {rank_customer_5.rank_name}"))

        # Создание рангов для исполнителей
        rank_executor_1 = Rank.objects.create(
            rank_name="Ассистент",
            rank_type="executor",
            rank_price=0,
        )
        RankDescription.objects.create(
            rank=rank_executor_1,
            description_text="Нет привилегий",
            privilege_type="quantitative"
        )
        self.stdout.write(self.style.SUCCESS(f"Создан ранга: {rank_executor_1.rank_name}"))

        rank_executor_2 = Rank.objects.create(
            rank_name="Специалист",
            rank_type="executor",
            rank_price=2500,
        )
        RankDescription.objects.create(
            rank=rank_executor_2,
            description_text="Комиссия платформы: 6%<br>Скидка на внутренние покупки: 5%<br>Бонусная программа: 5% для меня, 10% для привлечённых",
            privilege_type="quantitative"
        )
        RankDescription.objects.create(
            rank=rank_executor_2,
            description_text="Участие в ежемесячных конкурсах",
            privilege_type="unique"
        )
        self.stdout.write(self.style.SUCCESS(f"Создан ранга: {rank_executor_2.rank_name}"))

        rank_executor_3 = Rank.objects.create(
            rank_name="Наставник",
            rank_type="executor",
            rank_price=5000,
        )
        RankDescription.objects.create(
            rank=rank_executor_3,
            description_text="Комиссия платформы: 4%<br>Скидка на внутренние покупки: 10%<br>Бонусная программа: 10% для меня, 20% для привлечённых",
            privilege_type="quantitative"
        )
        RankDescription.objects.create(
            rank=rank_executor_3,
            description_text="Доступ к созданию внутренних курсов и монетизации статей",
            privilege_type="unique"
        )
        self.stdout.write(self.style.SUCCESS(f"Создан ранга: {rank_executor_3.rank_name}"))

        rank_executor_4 = Rank.objects.create(
            rank_name="Профи",
            rank_type="executor",
            rank_price=8000,
        )
        RankDescription.objects.create(
            rank=rank_executor_4,
            description_text="Комиссия платформы: 2%<br>Скидка на внутренние покупки: 15%<br>Бонусная программа: 15% для меня, 25% для привлечённых",
            privilege_type="quantitative"
        )
        RankDescription.objects.create(
            rank=rank_executor_4,
            description_text="Доступ к созданию внутренних курсов и публикации статей с монетизацией",
            privilege_type="unique"
        )
        self.stdout.write(self.style.SUCCESS(f"Создан ранга: {rank_executor_4.rank_name}"))

        rank_executor_5 = Rank.objects.create(
            rank_name="Мастер",
            rank_type="executor",
            rank_price=12000,
        )
        RankDescription.objects.create(
            rank=rank_executor_5,
            description_text="Комиссия платформы: 0%<br>Скидка на внутренние покупки: 20%<br>Бонусная программа: 20% для меня, 30% для привлечённых",
            privilege_type="quantitative"
        )
        RankDescription.objects.create(
            rank=rank_executor_5,
            description_text="Доступ к созданию внутренних курсов, публикации статей, монетизация и публикации успешных работ",
            privilege_type="unique"
        )
        self.stdout.write(self.style.SUCCESS(f"Создан ранга: {rank_executor_5.rank_name}"))

        rank_executor_6 = Rank.objects.create(
            rank_name="Гуру",
            rank_type="executor",
            rank_price=15000,
        )
        RankDescription.objects.create(
            rank=rank_executor_6,
            description_text="Комиссия платформы: 0%<br>Скидка на внутренние покупки: 25%<br>Бонусная программа: 30% для меня, 40% для привлечённых",
            privilege_type="quantitative"
        )
        RankDescription.objects.create(
            rank=rank_executor_6,
            description_text="Доступ к созданию внутренних курсов, публикации статей, монетизация и публикации успешных работ. Возможность снимающей бонусы с фиатного счета без ограничений.",
            privilege_type="unique"
        )
        self.stdout.write(self.style.SUCCESS(f"Создан ранга: {rank_executor_6.rank_name}"))

        self.stdout.write(self.style.SUCCESS("Созданы настройки реферальной программы"))

        self.stdout.write(self.style.SUCCESS("Заполнение базы данных завершено!"))