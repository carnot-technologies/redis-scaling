import datetime
import redis
import traceback
from logs.models import RedisMetric, RedisSetting, RedisPlan
from utils.heroku_helper import HerokuInterface
from utils.azure_helper import AzureInterface
from utils.mail_helper import mail_admins, send_email
from django.utils.timezone import now
from django.db.models import Q, Avg
from urllib import parse

hi = HerokuInterface()
az = AzureInterface()

REDIS_INST_DICT = {}


def get_redis_instances(REDIS_INST_DICT):
    rss = RedisSetting.objects.all()
    for rs in rss:
        try:
            if not rs.current_plan:
                redis_provider = rs.redis_heroku_name.split(",")[0] #Azure/RedisCloud
                redis_info = hi.get_addon_info(rs.app_name, rs.redis_heroku_name) if redis_provider!="Azure" else az.get_redis_configuration(rs.redis_name)
                rs.current_plan = RedisPlan.objects.get(
                    service_name=redis_info['addon_service'],
                    plan_name=redis_info['addon_plan'])
                rs.save()
            if rs.current_plan.service_name!="Azure":
                url = hi.get_env_var_value(rs.app_name, rs.redis_heroku_name)
                url_res = parse.urlparse(url)
                REDIS_INST_DICT[rs.redis_name] = redis.Redis(host=url_res.hostname,
                                                            port=url_res.port, password=url_res.password)
            else:
                REDIS_INST_DICT[rs.redis_name] = redis.Redis(**az.get_app_details(rs))
        except Exception as e:
            print(e)
            mail_admins('Exception in connecting to redis instance',
                        'Redis name = ' + str(rs.redis_name) + "\n" + str(traceback.format_exc()))


# Load redis instances globally
get_redis_instances(REDIS_INST_DICT)


def check_frequency(freq, cur_time, enable=True):
    if not enable:
        return False
    if freq == '30 sec':
        return True
    if freq == '1 min' and cur_time.second < 30:
        return True
    if freq == '5 min' and cur_time.minute % 5 == 0 and cur_time.second < 30:
        return True
    if freq == '10 min' and cur_time.minute % 10 == 0 and cur_time.second < 30:
        return True
    return False


def collect_metrics(redissetting_object, redis_inst_dict=REDIS_INST_DICT):
    try:
        rso = redissetting_object
        redis_name = rso.redis_name
        current_plan = rso.current_plan
        redis_provider = rso.redis_heroku_name.split(",")[0] #Azure/RedisCloud

        # get instance from dictionary. Do not create new instance each time
        if (not redis_inst_dict) or (redis_name not in redis_inst_dict) or (not redis_inst_dict.get(redis_name)):
            # Reload instance dict if instance not found
            get_redis_instances(REDIS_INST_DICT)
            return


        if not current_plan:
            redis_info = hi.get_addon_info(rso.app_name, rso.redis_heroku_name) if redis_provider!="Azure" else az.get_redis_configuration(rso.redis_name)
            rso.current_plan = RedisPlan.objects.get(
                service_name=redis_info['addon_service'],
                plan_name=redis_info['addon_plan'])
            rso.save()
            current_plan = rso.current_plan
        r = redis_inst_dict.get(redis_name)

        # Get plan's limits
        max_mem = current_plan.mem_limit * 1000000
        max_conn = current_plan.conn_limit

        # Get consumption data
        redis_info = r.info()
        used_memory = redis_info.get('used_memory') if redis_info.get('used_memory') else 0
        n_clients_connected = redis_info.get('connected_clients') if redis_info.get('connected_clients') else 0

        # Get percentage
        mem_percent = float(used_memory / max_mem) * 100
        conn_percent = float(n_clients_connected / max_conn) * 100 if max_conn > 0 else 0

        # Save to table
        redis_metric = RedisMetric(
            redis_fk=rso,
            used_memory=used_memory,
            n_connections=n_clients_connected,
            existing_plan=current_plan,
            percentage_memory=mem_percent,
            percentage_connections=conn_percent
        )
        redis_metric.save()
    except Exception as e:
        get_redis_instances(REDIS_INST_DICT)
        print(e)
        mail_admins("Exception in Redis Health Check schedular", traceback.format_exc())
    return


def check_alarm(redissetting_object):
    rso = redissetting_object
    if not rso.notification_policies.filter(notification_rule='on_alarm'):
        return
    ft = now() - datetime.timedelta(minutes=5)
    rms = RedisMetric.objects.filter(redis_fk=rso, sts__gte=ft)
    avg_mem = rms.aggregate(Avg('percentage_memory'))['percentage_memory__avg']
    avg_conn = rms.aggregate(Avg('percentage_connections'))['percentage_connections__avg']
    if avg_mem and avg_mem > rso.avg_memory_percent:
        send_email("ALARM: Redis memory exceeded threshold for " + str(rso.redis_name),
                   "Average redis memory usage over last 5 minutes has exceeded your set threshold.\n" +
                   "Average memory usage = " + str(avg_mem) + " %\n" +
                   "Set threshold for alarm = " + str(rso.avg_memory_percent) + "%")
    if avg_conn and avg_conn > rso.avg_connection_percent:
        send_email("ALARM: Redis connection exceeded threshold for " + str(rso.redis_name),
                   "Average redis connections over last 5 minutes has exceeded your set threshold.\n" +
                   "Average connections = " + str(avg_conn) + " %\n" +
                   "Set threshold for alarm = " + str(rso.avg_connection_percent) + "%")
    return


def get_next_plan_for_scale(rp, scale, source=None):
    '''
    :param rp:
        :type: django object
        RedisPlan fk indicating current plan from which upgrade is required
    :param scale:
        :type: bool
        1 for upgrade; 0 for downgrade
    :param source:
        :type: str
        'mem' for memory; 'conn' for connection
    :return:
        This function will return next plan for specified addon_name.
    '''
    next_plan = None
    if not rp:
        return next_plan
    if scale:
        filt = Q(service_name=rp.service_name, mem_limit__gt=rp.mem_limit) \
            if source == 'mem' else \
            Q(service_name=rp.service_name, conn_limit__gt=rp.conn_limit)
        next_plans = RedisPlan.objects.filter(filt).order_by(str(source) + '_limit')
    else:
        next_plans = RedisPlan.objects.filter(service_name=rp.service_name,
                                              mem_limit__lt=rp.mem_limit
                                              ).order_by('-mem_limit')
    if next_plans:
        next_plan = next_plans[0]
    return next_plan


def check_downgrade_allowed(avg_conn, avg_mem, down_plan, curr_plan,
                            avg_connection_percent, avg_memory_percent):
    if avg_conn * curr_plan.conn_limit / down_plan.conn_limit > avg_connection_percent:
        return False
    return avg_mem * curr_plan.mem_limit / down_plan.mem_limit < avg_memory_percent


def redis_auto_scale(redissetting_object):
    rso = redissetting_object
    redis_provider = "Azure" if rso.redis_heroku_name.split(',')[0].capitalize()=="Azure" else "Heroku"

    redis_info = hi.get_addon_info(rso.app_name, rso.redis_heroku_name) if redis_provider!="Azure" else az.get_redis_configuration(rso.redis_name)
    addon_id = redis_info['addon_id']

    if rso.current_plan.plan_name != redis_info['addon_plan']:
        rso.current_plan = RedisPlan.objects.get(
                service_name=redis_info['addon_service'],
                plan_name=redis_info['addon_plan'])
        rso.save()

    ft = now() - datetime.timedelta(minutes=int(rso.scaling_rate.split()[0])*2)
    rms = RedisMetric.objects.filter(redis_fk=rso, sts__gte=ft).order_by('-sts')
    avg_mem = rms.aggregate(Avg('percentage_memory'))['percentage_memory__avg']
    avg_conn = rms.aggregate(Avg('percentage_connections'))['percentage_connections__avg']

    if rms.exclude(action_performed='No Action'):
        print('Auto scaling action was taken recently. Giving buffer time before retrying.')
        return

    mem_upgrade_reqd = (avg_mem and avg_mem > rso.avg_memory_percent)
    conn_upgrade_reqd = (avg_conn and avg_conn > rso.avg_connection_percent)

    if mem_upgrade_reqd or conn_upgrade_reqd:
        print("Redis upgrade is required.")
        if rso.current_plan == rso.max_plan:
            sub = 'SOS ' + str(rso.app_name) + ': Redis Upgrade required'
            msg = "Upgrade is required for {0} in {1}. But redis plan is already at the max plan limit".format(
                    rso.redis_name, rso.app_name)
            print(msg)
            mail_admins(sub, msg)
            return

        source = 'mem' if mem_upgrade_reqd else 'conn'
        new_plan = get_next_plan_for_scale(rso.current_plan, scale=1, source=source)

        result = hi.change_addon_plan(rso.app_name, addon_id, new_plan.plan_name) if redis_provider!="Azure" else az.update_redis_plan(rso.redis_name,new_plan.plan_name)
        if (not result)  and (rso.notification_policies.filter(notification_rule='on_failure')):
            sub = "FAILURE: Redis Autoscaling"
            msg = "Upgrade is required for {0} in {1}. But could not be done through heroku API. Heroku API limit might have reached. Please upgrade manually.".format(
                    rso.redis_name, rso.app_name)
            print(msg)
            send_email(sub, msg)
            return

        # Store action to latest log and send mail
        print(rso.app_name, rso.redis_name, "Upgraded from ", str(rso.current_plan),
              "to", str(new_plan))
        print(mem_upgrade_reqd, conn_upgrade_reqd)
        rm = rms[0]
        rm.action_performed = 'Upgrade'
        rm.save()
        rso.current_plan = new_plan
        rso.save()
        if rso.notification_policies.filter(notification_rule='on_success'):
            msg = "In {0} app, Redis plan for {1} is Upgraded to '{2}'." .format(
                          rso.app_name, rso.redis_name, new_plan.plan_name)
            send_email("SUCCESS: Redis Autoscaling", msg)
        return

    # Check if we can downgrade
    if rso.current_plan == rso.min_plan:
        sub = 'Redis downgrade possible'
        msg = "Redis {0} in {1} can be downgraded to a lower plan. But redis plan is already at the min plan limit. Reduce the min plan if you want to save further cost".format(
                rso.redis_name, rso.app_name)
        print(msg)
        mail_admins(sub, msg)
        return

    # Check if mem & conn would be within limits if we downgrade
    down_plan = get_next_plan_for_scale(rso.current_plan, scale=0, source=None)
    if not down_plan:
        return
    downgrade_allowed = check_downgrade_allowed(avg_conn, avg_mem, down_plan, rso.current_plan,
                                                rso.avg_connection_percent, rso.avg_memory_percent)
    if not downgrade_allowed:
        print('If we downgrade, either connection limit or memory limit would be exceeded.')
        return

    # Scale down redis
    result = hi.change_addon_plan(rso.app_name, addon_id, down_plan.plan_name) if redis_provider!="Azure" else az.update_redis_plan(rso.redis_name,down_plan.plan_name)
    if (not result) and (rso.notification_policies.filter(notification_rule='on_failure')):
        sub = "FAILURE: Redis Autoscaling"
        msg = "Downgrade is required for {0} in {1}. But could not be done through heroku API. Heroku API limit might have reached. Please downgrade manually.".format(
                rso.redis_name, rso.app_name)
        send_email(sub, msg)
        print(msg)
        return

    # Store action to latest log and send mail
    print(rso.app_name, rso.redis_name, "Downgraded from ", str(rso.current_plan),
      "to", str(down_plan))
    rm = rms[0]
    rm.action_performed = 'Downgrade'
    rm.save()
    rso.current_plan = down_plan
    rso.save()
    if rso.notification_policies.filter(notification_rule='on_success'):
        msg = "In {0} app, Redis plan for {1} is downgraded to '{2}'." .format(
                      rso.app_name, rso.redis_name, down_plan.plan_name)
        send_email("SUCCESS: Redis Autoscaling", msg)
    return
