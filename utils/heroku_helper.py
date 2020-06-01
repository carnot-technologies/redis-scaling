from django.conf import settings
import requests
import heroku3
import json

# Reference: https://devcenter.heroku.com/articles/platform-api-reference#add-on
heroku_base_url = 'https://api.heroku.com'


class HerokuInterface(object):
    instance = None
    request_header = {}

    def __init__(self):
        if HerokuInterface.instance is not None:
            return
        if not settings.HEROKU_API_KEY:
            print("Please specify HEROKU_API_KEY in the environment")

        HerokuInterface.instance = heroku3.from_key(settings.HEROKU_API_KEY)
        HerokuInterface.request_header = {
            "Accept": "application/vnd.heroku+json; version=3",
            "Authorization": "Bearer " + str(settings.HEROKU_API_KEY),
            "Content-Type": "application/json"
        }

        print("Heroku interface initiated ...")
        return

    def get_instance(self):
        if HerokuInterface.instance is None:
            HerokuInterface.instance = HerokuInterface()
        return HerokuInterface.instance

    def get_app(self, app_name):
        return self.instance.apps()[app_name]

    def get_env_var_value(self, app_name, var_name):
        return self.get_app(app_name).config().dict()[var_name]

    def get_addon_info(self, app_name, config_name):
        addon_id = None
        addon_name = None
        addon_plan = None
        addon_service = None
        url = heroku_base_url + '/apps/' + app_name + '/addons'
        res = requests.get(url, headers=HerokuInterface.request_header)
        if res.status_code == 200:
            resp = res.json()
            for each_addon in resp:
                if each_addon.get("config_vars")[0] != config_name:
                    continue
                addon_id = each_addon.get("id")
                addon_name = each_addon.get("addon_service").get("name")
                addon_plan = each_addon.get("plan").get("name")
                addon_service = each_addon.get("addon_service").get("name")
                break
        addon_info = {'addon_id': addon_id, 'addon_name': addon_name,
                      'addon_plan': addon_plan, 'addon_service': addon_service}
        return addon_info

    def change_addon_plan(self, app_name, addon_id, plan):
        url = heroku_base_url + '/apps/' + app_name + '/addons/' + addon_id
        payload = {"plan": plan}
        res = requests.patch(url, headers=HerokuInterface.request_header,
                             data=json.dumps(payload))
        new_id = None
        if res.status_code == 201:
            new_id = res.json().get("plan").get("id")
        return new_id
