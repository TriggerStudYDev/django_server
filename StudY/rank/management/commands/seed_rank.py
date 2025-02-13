from django.core.management.base import BaseCommand

from rank.models import *


class Command(BaseCommand):
    help = "Заполняет базу данных рангами"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Начало заполнения базы данных..."))

        rank_customer_0 = Rank.objects.create(
            rank_name="Абитуриент",
            rank_type="customer",
            rank_price=0,
        )
        RankSettings.objects.create(
            rank=rank_customer_0,
            type_role="customer",
            discount_internal_purchases=0,
            referral_bonus_self=0,
            referral_bonus_invited=0,
            discount_orders=0,
            commission_reduction=0,
            notifications_to_executor=False,
            market_price_stats=False,
            extra_discount_per_order=False,
            visibility_other_universities=False,
            bonus_to_fiat_transfer=False,
        )
        self.stdout.write(self.style.SUCCESS(f"Создана настройка для ранга: {rank_customer_0.rank_name}"))

        RankDescription.objects.create(
            rank=rank_customer_0,
            description_text="Нет привилегий",
            privilege_type="quantitative"
        )

        rank_customer_1 = Rank.objects.create(
            rank_name="Студент",
            rank_type="customer",
            rank_price=1000,
        )
        RankSettings.objects.create(
            rank=rank_customer_1,
            type_role="customer",
            discount_internal_purchases=5,
            referral_bonus_self=20,
            referral_bonus_invited=15,
            discount_orders=2,
            commission_reduction=0,
            notifications_to_executor=True,
            market_price_stats=False,
            extra_discount_per_order=False,
            visibility_other_universities=False,
            bonus_to_fiat_transfer=False,
        )
        self.stdout.write(self.style.SUCCESS(f"Создана настройка для ранга: {rank_customer_1.rank_name}"))

        RankDescription.objects.create(
            rank=rank_customer_1,
            description_text="Нет привилегий",
            privilege_type="quantitative"
        )

        rank_customer_2 = Rank.objects.create(
            rank_name="Исследователь",
            rank_type="customer",
            rank_price=2000,
        )
        RankSettings.objects.create(
            rank=rank_customer_2,
            type_role="customer",
            discount_internal_purchases=8,
            referral_bonus_self=28,
            referral_bonus_invited=25,
            discount_orders=5,
            commission_reduction=0,
            notifications_to_executor=True,
            market_price_stats=True,
            extra_discount_per_order=False,
            visibility_other_universities=False,
            bonus_to_fiat_transfer=False,
        )
        self.stdout.write(self.style.SUCCESS(f"Создана настройка для ранга: {rank_customer_2.rank_name}"))

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
            rank_price=3000,
        )
        RankSettings.objects.create(
            rank=rank_customer_3,
            type_role="customer",
            discount_internal_purchases=15,
            referral_bonus_self=35,
            referral_bonus_invited=30,
            discount_orders=8,
            commission_reduction=0,
            notifications_to_executor=True,
            market_price_stats=True,
            extra_discount_per_order=True,
            visibility_other_universities=False,
            bonus_to_fiat_transfer=False,
        )
        self.stdout.write(self.style.SUCCESS(f"Создана настройка для ранга: {rank_customer_3.rank_name}"))

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

        rank_customer_4 = Rank.objects.create(
            rank_name="Магистр",
            rank_type="customer",
            rank_price=5000,
        )
        RankSettings.objects.create(
            rank=rank_customer_4,
            type_role="customer",
            discount_internal_purchases=30,
            referral_bonus_self=40,
            referral_bonus_invited=50,
            discount_orders=10,
            commission_reduction=0,
            notifications_to_executor=True,
            market_price_stats=True,
            extra_discount_per_order=True,
            visibility_other_universities=True,
            bonus_to_fiat_transfer=False,
        )
        self.stdout.write(self.style.SUCCESS(f"Создана настройка для ранга: {rank_customer_4.rank_name}"))

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

        rank_customer_5 = Rank.objects.create(
            rank_name="Профессор",
            rank_type="customer",
            rank_price=10000,
        )
        RankSettings.objects.create(
            rank=rank_customer_5,
            type_role="customer",
            discount_internal_purchases=50,
            referral_bonus_self=50,
            referral_bonus_invited=100,
            discount_orders=13,
            commission_reduction=0,
            notifications_to_executor=True,
            market_price_stats=True,
            extra_discount_per_order=True,
            visibility_other_universities=True,
            bonus_to_fiat_transfer=True,
        )
        self.stdout.write(self.style.SUCCESS(f"Создана настройка для ранга: {rank_customer_5.rank_name}"))

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


        # # Создание рангов для исполнителей
        rank_assistant = Rank.objects.create(
            rank_name="Ассистент",
            rank_type="executer",
            rank_price=0,
        )
        RankSettings.objects.create(
            rank=rank_assistant,
            type_role="executer",
            discount_internal_purchases=0,
            referral_bonus_self=0,
            referral_bonus_invited=0,
            discount_orders=0,
            commission_reduction=0,
            notifications_to_executor=False,
            market_price_stats=False,
            extra_discount_per_order=False,
            visibility_other_universities=False,
            bonus_to_fiat_transfer=False,
            monthly_contests=False,
            create_internal_courses=False,
            publish_articles=False,
            upload_work_to_study=False,
            mandatory_review=False,
            unlimited_fiat_withdrawals=False,
        )
        self.stdout.write(self.style.SUCCESS(f"Создана настройка для ранга: {rank_assistant.rank_name}"))

        RankDescription.objects.create(
            rank=rank_assistant,
            description_text="Нет привилегий",
            privilege_type="quantitative"
        )

        # Специалист
        rank_specialist = Rank.objects.create(
            rank_name="Специалист",
            rank_type="executer",
            rank_price=1000,
        )
        RankSettings.objects.create(
            rank=rank_specialist,
            type_role="executer",
            discount_internal_purchases=5,
            referral_bonus_self=20,
            referral_bonus_invited=15,
            commission_reduction=2,
            notifications_to_executor=False,
            market_price_stats=False,
            extra_discount_per_order=False,
            visibility_other_universities=False,
            bonus_to_fiat_transfer=False,
            monthly_contests=True,
            create_internal_courses=False,
            publish_articles=False,
            upload_work_to_study=False,
            mandatory_review=False,
            unlimited_fiat_withdrawals=False,
        )
        self.stdout.write(self.style.SUCCESS(f"Создана настройка для ранга: {rank_specialist.rank_name}"))

        RankDescription.objects.create(
            rank=rank_specialist,
            description_text="Комиссия платформы: 6%<br>Скидка на внутренние покупки: 5%<br>Бонусная программа: 5% для меня, 10% для привлечённых",
            privilege_type="quantitative"
        )
        RankDescription.objects.create(
            rank=rank_specialist,
            description_text="Участие в ежемесячных конкурсах",
            privilege_type="unique"
        )

        # Наставник
        rank_mentor = Rank.objects.create(
            rank_name="Наставник",
            rank_type="executer",
            rank_price=2000,
        )
        RankSettings.objects.create(
            rank=rank_mentor,
            type_role="executer",
            discount_internal_purchases=8,
            referral_bonus_self=28,
            referral_bonus_invited=25,
            commission_reduction=4,
            notifications_to_executor=False,
            market_price_stats=False,
            extra_discount_per_order=False,
            visibility_other_universities=False,
            bonus_to_fiat_transfer=False,
            monthly_contests=True,
            create_internal_courses=True,
            publish_articles=True,
            upload_work_to_study=False,
            mandatory_review=False,
            unlimited_fiat_withdrawals=False,
        )
        self.stdout.write(self.style.SUCCESS(f"Создана настройка для ранга: {rank_mentor.rank_name}"))

        RankDescription.objects.create(
            rank=rank_mentor,
            description_text="Комиссия платформы: 4%<br>Скидка на внутренние покупки: 10%<br>Бонусная программа: 10% для меня, 20% для привлечённых",
            privilege_type="quantitative"
        )
        RankDescription.objects.create(
            rank=rank_mentor,
            description_text="Доступ к созданию внутренних курсов и монетизации статей",
            privilege_type="unique"
        )

        # Профи
        rank_pro = Rank.objects.create(
            rank_name="Профи",
            rank_type="executer",
            rank_price=3000,
        )
        RankSettings.objects.create(
            rank=rank_pro,
            type_role="executer",
            discount_internal_purchases=15,
            referral_bonus_self=38,
            referral_bonus_invited=40,
            commission_reduction=5,
            notifications_to_executor=False,
            market_price_stats=False,
            extra_discount_per_order=False,
            visibility_other_universities=False,
            bonus_to_fiat_transfer=False,
            monthly_contests=True,
            create_internal_courses=True,
            publish_articles=True,
            upload_work_to_study=False,
            mandatory_review=True,
            unlimited_fiat_withdrawals=False,
        )
        self.stdout.write(self.style.SUCCESS(f"Создана настройка для ранга: {rank_pro.rank_name}"))

        RankDescription.objects.create(
            rank=rank_pro,
            description_text="Комиссия платформы: 2%<br>Скидка на внутренние покупки: 15%<br>Бонусная программа: 15% для меня, 25% для привлечённых",
            privilege_type="quantitative"
        )
        RankDescription.objects.create(
            rank=rank_pro,
            description_text="Доступ к созданию внутренних курсов и публикации статей с монетизацией",
            privilege_type="unique"
        )

        # Мастер
        rank_master = Rank.objects.create(
            rank_name="Мастер",
            rank_type="executer",
            rank_price=5000,
        )
        RankSettings.objects.create(
            rank=rank_master,
            type_role="executer",
            discount_internal_purchases=30,
            referral_bonus_self=45,
            referral_bonus_invited=50,
            commission_reduction=8,
            notifications_to_executor=False,
            market_price_stats=False,
            extra_discount_per_order=False,
            visibility_other_universities=False,
            bonus_to_fiat_transfer=False,
            monthly_contests=True,
            create_internal_courses=True,
            publish_articles=True,
            upload_work_to_study=False,
            mandatory_review=True,
            unlimited_fiat_withdrawals=False,
        )
        self.stdout.write(self.style.SUCCESS(f"Создана настройка для ранга: {rank_master.rank_name}"))

        rank_master.objects.create(
            rank=rank_master,
            description_text="Комиссия платформы: 0%<br>Скидка на внутренние покупки: 20%<br>Бонусная программа: 20% для меня, 30% для привлечённых",
            privilege_type="quantitative"
        )
        rank_master.objects.create(
            rank=rank_master,
            description_text="Доступ к созданию внутренних курсов, публикации статей, монетизация и публикации успешных работ",
            privilege_type="unique"
        )

        rank_guru = Rank.objects.create(
            rank_name="Гуру",
            rank_type="executer",
            rank_price=10000,
        )
        RankSettings.objects.create(
            rank=rank_guru,
            type_role="executer",
            discount_internal_purchases=50,
            referral_bonus_self=70,
            referral_bonus_invited=100,
            commission_reduction=10,
            notifications_to_executor=False,
            market_price_stats=False,
            extra_discount_per_order=False,
            visibility_other_universities=False,
            bonus_to_fiat_transfer=False,
            monthly_contests=True,
            create_internal_courses=True,
            publish_articles=True,
            upload_work_to_study=False,
            mandatory_review=True,
            unlimited_fiat_withdrawals=True,
        )
        self.stdout.write(self.style.SUCCESS(f"Создана настройка для ранга: {rank_guru.rank_name}"))

        RankDescription.objects.create(
            rank=rank_guru,
            description_text="Комиссия платформы: 0%<br>Скидка на внутренние покупки: 25%<br>Бонусная программа: 30% для меня, 40% для привлечённых",
            privilege_type="quantitative"
        )
        RankDescription.objects.create(
            rank=rank_guru,
            description_text="Доступ к созданию внутренних курсов, публикации статей, монетизация и публикации успешных работ. Возможность снимающей бонусы с фиатного счета без ограничений.",
            privilege_type="unique"
        )


        self.stdout.write(self.style.SUCCESS("Созданы настройки реферальной программы"))

        self.stdout.write(self.style.SUCCESS("Заполнение базы данных завершено!"))