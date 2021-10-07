from django.contrib import admin
from .models import CustomUser, AuthCode


admin.site.register(CustomUser)
admin.site.register(AuthCode)
