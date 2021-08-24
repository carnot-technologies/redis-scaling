import pandas as pd
from logs.models import RedisSetting, RedisPlan, NotificationPolicy


def static_settings():
    # Add redis plans
    df = pd.read_csv('utils/redis_plans.csv')
    for index, row in df.iterrows():
        rp, created = RedisPlan.objects.get_or_create(
            service_name=row['service_name'], plan_name=row['plan_name']
        )
        rp.mem_limit = row['mem_limit']
        rp.conn_limit = row['conn_limit']
        rp.cost = row['cost']
        rp.save()
    # Add notification policies
    np, created = NotificationPolicy.objects.get_or_create(notification_rule='on_alarm')
    np, created = NotificationPolicy.objects.get_or_create(notification_rule='on_success')
    np, created = NotificationPolicy.objects.get_or_create(notification_rule='on_failure')


def add_redis_settings():
    redis_provider = input("Select Redis provider: \t Valid values->Azure,Other")
    if redis_provider.lower() not in ['azure','other']:
        print("Invalid redis provider value")
        return
    
    redis_name = input("Provide a unique name to your redis instance: ")
    heroku_app = input("Enter the name of {} app to which redis is attached: ".format("Azure" if redis_provider.lower()=="azure" else "Heroku"))
    if redis_provider.lower()!="azure":
        redis_heroku_name = input("Enter the redis attachement url name provided by Heroku: ")
    else:
        redis_heroku_name = "Azure,{}".format(heroku_app)
    print("\nMetrics Configuration:")
    metric_rate = input("Select rate of metric collection (30 sec / 1 min / 5 min): ")
    if metric_rate not in ['30 sec', '1 min', '5 min']:
        print("Input rate of metric collection from given options")
        return

    avg_conn_percent = input("Enter the average connection percentage to be maintained: ")
    avg_mem_percent = input("Enter the average memory percentage to be maintained: ")
    scaling_enable = input("Enable redis auto-scaling? (y/n): ")
    scaling_enable = int(scaling_enable == 'y')
    print("\nNotification Configuratin")
    alarm_notif = input("Select notification rule:\n" +
                        "1. On threshold breach [y/n]: ")
    alarm_notif = int(alarm_notif == 'y')
    success_notif = failure_notif = 0
    if scaling_enable:
        success_notif = input("2. On scaling success [y/n]: ")
        failure_notif = input("3. On scaling failure [y/n]: ")
        success_notif = int(success_notif == 'y')
        failure_notif = int(failure_notif == 'y')
    print("\nScaling Configuration")

    rs, created = RedisSetting.objects.get_or_create(redis_name=redis_name)
    rs.app_name = heroku_app
    rs.redis_heroku_name = redis_heroku_name
    rs.metric_rate = metric_rate
    rs.avg_connection_percent = avg_conn_percent
    rs.avg_memory_percent = avg_mem_percent
    rs.enable_scaling = scaling_enable

    if not scaling_enable:
        rs.save()
        if alarm_notif:
            rs.notification_policies.add(NotificationPolicy.objects.get(notification_rule='on_alarm'))
        return

    scaling_rate = input("Select rate of scaling check (1 min / 5 min / 10 min): ")
    if scaling_rate not in ['1 min', '5 min', '10 min']:
        print("Input rate of scaling from given options")
        return
    min_plan = input("Input min plan threshold for scaling. Example  {}".format("rediscloud:30." if redis_provider.lower()=="other" else "Standard-C-1"))
    max_plan = input("Input max plan threshold for scaling. Example {}".format("heroku-redis:premium-5." if redis_provider.lower()=="other" else "Premium-P-5"))
    
    rs.scaling_rate = scaling_rate
    print("\n")
    rps = RedisPlan.objects.filter(plan_name=min_plan).order_by('mem_limit')
    if not rps:
        rps = RedisPlan.objects.filter(plan_name__contains=min_plan).order_by('mem_limit')
    if rps:
        rs.min_plan = rps[0]
        print(str(rps[0].plan_name) + " is set as the minimum allowed plan")
    rps = RedisPlan.objects.filter(plan_name=max_plan).order_by('-mem_limit')
    if not rps:
        rps = RedisPlan.objects.filter(plan_name__contains=max_plan).order_by('-mem_limit')
    if rps:
        rs.max_plan = rps[0]
        print(str(rps[0].plan_name) + " is set as the maximum allowed plan")
    rs.save()
    if alarm_notif:
        rs.notification_policies.add(NotificationPolicy.objects.get(notification_rule='on_alarm'))
    if success_notif:
        rs.notification_policies.add(NotificationPolicy.objects.get(notification_rule='on_success'))
    if failure_notif:
        rs.notification_policies.add(NotificationPolicy.objects.get(notification_rule='on_failure'))
    