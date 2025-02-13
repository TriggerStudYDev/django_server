from django.core.management.base import BaseCommand

from server.models import *
from rank.models import *


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


        self.stdout.write(self.style.SUCCESS("Созданы настройки реферальной программы"))

        self.stdout.write(self.style.SUCCESS("Заполнение базы данных завершено!"))