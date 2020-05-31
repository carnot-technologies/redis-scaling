from django.db import models
from django.utils.timezone import now


# Create your models here.
class RedisPlan(models.Model):
    service_name = models.CharField(blank=False, null=False, max_length=50)
    plan_name = models.CharField(blank=False, null=False, max_length=50)
    mem_limit = models.FloatField(blank=False, null=False, default=10)
    conn_limit = models.IntegerField(blank=False, null=False, default=1)
    cost = models.IntegerField(blank=False, null=False, default=0)

    class Meta:
        verbose_name = ('Redis Plan')
        verbose_name_plural = ('Redis Plans')

    # Override unicode to return something meaningful
    def __str__(self):
        return self.plan_name


class NotificationPolicy(models.Model):
    notification_rule = models.CharField(blank=False, null=False, max_length=50)

    class Meta:
        verbose_name = ('Notiication Policy')
        verbose_name_plural = ('Notification Policies')

    # Override unicode to return something meaningful
    def __str__(self):
        return self.notification_rule


class RedisSetting(models.Model):
    metric_rate_options = (
        ('30 sec', '30 sec'),
        ('1 min', '1 min'),
        ('5 min', '5 min')
    )
    scaling_rate_options = (
        ('1 min', '1 min'),
        ('5 min', '5 min'),
        ('10 min', '10 min')
    )

    redis_name = models.CharField(blank=False, null=False, max_length=256, unique=True)
    app_name = models.CharField(blank=False, null=False, max_length=256)
    redis_heroku_name = models.CharField(blank=False, null=False, max_length=256)

    metric_rate = models.CharField(choices=metric_rate_options, max_length=16, default='1 min')
    current_plan = models.ForeignKey(RedisPlan, on_delete=models.CASCADE, null=True, blank=True)
    enable_scaling = models.BooleanField(blank=True, null=True, default=False)
    scaling_rate = models.CharField(choices=scaling_rate_options, max_length=16, default='5 min', null=True, blank=True)
    min_plan = models.ForeignKey(RedisPlan, on_delete=models.CASCADE, related_name='min_plan', null=True, blank=True)
    max_plan = models.ForeignKey(RedisPlan, on_delete=models.CASCADE, related_name='max_plan', null=True, blank=True)
    avg_connection_percent = models.IntegerField(blank=False, null=False, default=80)
    avg_memory_percent = models.IntegerField(blank=False, null=False, default=80)
    notification_policies = models.ManyToManyField(NotificationPolicy, blank=True, null=True, default=None)

    class Meta:
        verbose_name = ('Redis Setting')
        verbose_name_plural = ('Redis Settings')

    # Override unicode to return something meaningful
    def __str__(self):
        return self.redis_name


class RedisMetric(models.Model):
    action_choices = (
        ('No Action', 'No Action'),
        ('Upgrade', 'Upgrade'),
        ('Downgrade', 'Downgrade'),
    )

    redis_fk = models.ForeignKey(RedisSetting, on_delete=models.CASCADE)
    used_memory = models.BigIntegerField(blank=True, null=True, default=0)
    n_connections = models.IntegerField(blank=True, null=True, default=0)

    existing_plan = models.ForeignKey(RedisPlan, on_delete=models.CASCADE)
    percentage_memory = models.FloatField(blank=True, null=True)
    percentage_connections = models.FloatField(blank=True, null=True)
    action_performed = models.CharField(choices=action_choices, max_length=32, default='No Action')
    sts = models.DateTimeField(blank=True, null=True, default=now)

    class Meta:
        verbose_name = ('Redis Metric')
        verbose_name_plural = ('Redis Metrics')

    # Override unicode to return something meaningful
    def __str__(self):
        return str(self.redis_fk)
