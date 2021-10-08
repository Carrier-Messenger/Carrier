from django.contrib import admin
from .models import CustomUser, AuthCode, EmailRenewCode


admin.site.register(CustomUser)
admin.site.register(AuthCode)
admin.site.register(EmailRenewCode)
