from django.conf import settings
import requests
import json
import redis
import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.redis import RedisManagementClient
from azure.mgmt.redis.models import Sku, RedisUpdateParameters,RedisProperties
from redisscale.models import RedisSetting

HOST_TEMPLATE = "{}.redis.cache.windows.net"
SSL_PORT = 6380
NON_SSL_PORT = 6379

class AzureInterface(object):
    instance = None
    request_header = {}

    def __init__(self):
        if AzureInterface.instance is not None:
            return
        AzureInterface.instance = RedisManagementClient(
                                    DefaultAzureCredential(),
                                    settings.SUBSCRIPTION_ID
                                )
        return

    def get_instance(self):
        if AzureInterface.instance is None:
            AzureInterface.instance = AzureInterface()
        return AzureInterface.instance
    
    def get_app_details(self,redissetting_instance):
        '''
        This function will return a dict that can be used for redis instance initiation
        Note: RedisSetting table's redis_heroku_name column will contain the comma-separated password for primary and replica redis instance
        '''
        return {"host":HOST_TEMPLATE.format(redissetting_instance.redis_name),
                "port":NON_SSL_PORT,
                "password":rs.redis_heroku_name.split(",")[0]}

    def get_redis_configuration(self,redis_name):
        instance = self.get_instance()
        data = instance.redis.get(settings.GROUP_NAME,redis_name).as_dict()
        return {"addon_service":"Azure",
                "addon_plan":"{}-{}-{}".format(data['sku']['name'],data['sku']['family'],data['sku']['capacity'])
                "addon_id":data['id']}
    
    def update_redis_plan(self,redis_name,redis_plan_string):
        try:
            #redis_plan_string will be of format Name-Family-Capacity (Standard-C-1)
            name,family,capacity = redis_plan_string.split("-")
            instance = self.get_instance()
            instance.redis.update(settings.GROUP_NAME,
                                  redis_name,
                                  RedisUpdateParameters(sku=Sku(name=name.capitalize(),family=family.upper(),capacity=str(capacity))))
            return True
        except Exception as e:
            print("Error while redis plan update",e)
            return False