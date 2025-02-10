from django.contrib import admin
from .models import *

admin.site.register(Balance)
admin.site.register(WithdrawalRequest)
admin.site.register(Transaction)
