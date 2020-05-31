import django
django.setup()
import datetime
import sys
import traceback
from apscheduler.schedulers.blocking import BlockingScheduler
from django.utils.timezone import now
from django.conf import settings
from logs.models import RedisSetting, RedisMetric
from utils.mail_helper import mail_admins
from utils.redis_scaling import redis_auto_scale
from utils.redis_scaling import check_frequency, collect_metrics, check_alarm

scheduler = BlockingScheduler()


@scheduler.scheduled_job('cron', second='0,30')
def check_scaling_metrics():
    print("Collecting redis metrics and checking for scaling...", now())
    cur_time = now()
    rss = RedisSetting.objects.all()
    for rs in rss:
        try:
            collect_valid = check_frequency(rs.metric_rate, cur_time)
            if collect_valid:
                collect_metrics(rs)
                check_alarm(rs)
        except Exception as e:
            print(e)
            mail_admins('Exception in collecting redis metrics',
                        'Could not collect metrics for redis ' + str(rs.redis_name) +
                        '\n' + str(traceback.format_exc()))

        try:
            scale_valid = check_frequency(rs.scaling_rate, cur_time, rs.enable_scaling)
            if scale_valid:
                redis_auto_scale(rs)
        except Exception as e:
            print(e)
            mail_admins('Exception in redis auto scaling',
                        'Could not perform scaling action for redis '
                        + str(rs.redis_name) + '\n' + str(traceback.format_exc()))

    return True


@scheduler.scheduled_job('cron', hour='*/2')
def clean_db_logs():
    print("Checking logs to clean..", file=sys.stderr)
    try:
        ft = now() - datetime.timedelta(days=settings.N_RETENTION_DAYS)
        rms = RedisMetric.objects.filter(sts__lte=ft)
        rms.delete()
    except Exception as e:
        print(e, file=sys.stderr)
        mail_admins("Exception in clean_db_logs cron", traceback.format_exc())


def main():
    try:
        print("Starting the blocking scheduler")
        scheduler.start()
    except KeyboardInterrupt:
        print('\nExiting by user request.\n', file=sys.stderr)
    except Exception:
        traceback.print_exc(file=sys.stdout)

    sys.exit(0)


if __name__ == '__main__':
    main()