from django.contrib import admin
from logs.models import RedisMetric, RedisSetting, RedisPlan, NotificationPolicy


class RedisSettingAdmin(admin.ModelAdmin):
    list_display = [field.name for field in RedisSetting._meta.get_fields() if field.auto_created==False and field.get_internal_type() != 'ManyToManyField']


class RedisMetricAdmin(admin.ModelAdmin):
    list_display = [field.name for field in RedisMetric._meta.get_fields()  if field.auto_created==False]


class NotificationPolicyAdmin(admin.ModelAdmin):
    list_display = [field.name for field in NotificationPolicy._meta.get_fields() if field.auto_created==False]


class RedisPlanAdmin(admin.ModelAdmin):
    list_display = [field.name for field in RedisPlan._meta.get_fields() if field.auto_created==False]


# Register your models here.
admin.site.register(NotificationPolicy, NotificationPolicyAdmin)
admin.site.register(RedisSetting, RedisSettingAdmin)
admin.site.register(RedisMetric, RedisMetricAdmin)
admin.site.register(RedisPlan, RedisPlanAdmin)
