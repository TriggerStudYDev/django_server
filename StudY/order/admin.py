from django.contrib import admin
from .models import *

admin.site.register(Order)
admin.site.register(OrderStatusLog)
admin.site.register(OrderResult)
admin.site.register(OrderResultFile)
admin.site.register(OrderComment)
admin.site.register(OrderRating)
admin.site.register(OrderRatingCriteria)
admin.site.register(ExecutorDiscipline)

# Register your models here.
