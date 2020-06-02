# Redis-scaling  <img src="https://upload.wikimedia.org/wikipedia/en/thumb/6/6b/Redis_Logo.svg/1200px-Redis_Logo.svg.png" width="125" height="50" align="right">   <img src="https://img.stackshare.io/service/4601/original.png" width="75" height="50" align="right">   
   
[![HitCount](http://hits.dwyl.com/carnot-technologies/redis-scaling.svg)](http://hits.dwyl.com/carnot-technologies/redis-scaling)
[![PyPI version](https://badge.fury.io/py/heroku3.svg)](https://badge.fury.io/py/heroku3)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![GitHub Issues](https://img.shields.io/github/issues/carnot-technologies/redis-scaling)](https://github.com/carnot-technologies/redis-scaling/issues)
[![GitHub PRs](https://img.shields.io/github/issues-pr/carnot-technologies/redis-scaling)](https://github.com/carnot-technologies/redis-scaling/pulls)

:star: Star us on GitHub — it helps!  

This is a python project to auto scale the redis resources on Heroku platform.

![](https://miro.medium.com/max/656/1*W0hyXlN4H0x0BNK4NwYPTw.gif)

## Table of content

- [Purpose](#purpose)
- [How it works](#how-it-works)
- [Set it up](#setup-guide)
  - [Heroku Application](#heroku-application)
  - [Initialization](#initialize)
  - [Redis Configuration](#redis-configuration)

## Purpose
[![start with why](https://img.shields.io/badge/start%20with-why%3F-brightgreen.svg?style=flat)](http://www.ted.com/talks/simon_sinek_how_great_leaders_inspire_action)   

Having redis auto scaling would avoid many SOS situations that usually arise during peak traffic while giving you complete control over the way you want to scale.   

Top reasons for why you must have auto scaling on your redis instances:
- **Dynamic Load Management** - Helps to cater to the dynamic load on your application. Scales in accordance to the load & demand.
- **Avoid Data Drop** - Helps to ensure timely scaling to avoid redis data drop. Scales prematurely by monitoring key metrics and mitigates data drop of new incoming information 
- **Avoid Downtime** - Helps to avoid downtime on your application. Monitors key metrics to ensure your redis is always accessible.
- **Cost Saving** - Finally, saves cost by scaling down in low-load scenarios

## How It Works!
1. Once any redis instance is configured, a scheduled cron collects the key metrics periodically.
2. If any metric breaches the preset threshold, a next plan is fetched from the list of all plans. Current redis plan is changed to that plan
3. If all metrics are below the respective thresholds, it is evaluated if a lower plan can be selected while still satisfying all the thresholds. If yes, only then the current redis plan is changed to a lower one
4. All metrics and scaling actions are logged to a database for review / reference
5. Periodic data cleaning is done to avoid exceeding DB plan

## Setup Guide
Follow below guidelines to quickly setup this project on your heroku account.

### Heroku application
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/carnot-technologies/redis-scaling/tree/master)

<details><summary>Environment Configuration</summary>  
  
- `HEROKU_API_KEY`: API key for your heroku account
- `EMAIL_HOST`: Host name for your email 
- `EMAIL_PORT`: Port for your email
- `EMAIL_HOST_PASSWORD`: Host password
- `EMAIL_HOST_USER`: Host username
- `SERVER_EMAIL`: Server email
- `RECIPIENTS`: Comma separated emails of notification recipients
- `ENABLE_EMAILS`: A global flag to enable / disable all types of mails
- `EMAIL_PREFIX`: Email subject prefix for possible filter addition
- `N_RETENTION_DAYS`: Number of days to retain metrics logs
</details>

### Initialize
Post deployment `initialize.sh` is run from console.
This does 3 things:
1. Applies all DB migrations
2. Creates superuser for django admin panel
3. Adds static info to database

### Redis Configuration
Run `python add_redis_mon.py` from console
This will prompt you for all information related to redis instance for which auto scaling needs to be enabled.

![Add Redis Instance to Auto Scaling](http://g.recordit.co/48cmiDjNm7.gif)

<details><summary>General Configuration</summary>  
  
- `Name`: An identifier name for your redis insatnce. Can be alphanumeric  
- `Heroku App Name`: This is the name of heroku application to which your redis instance is attached  
- `Redis Heroku Name`: This is the URL name by which your heroku application identifies the redis. (Example: REDISCLOUD_ORANGE_URL or HEROKU_REDIS_BLANK_URL)   
</details>

<details><summary>Metrics Configuration</summary>  
  
- `Metric Rate`: Choose rate of metrics collection from given options. Select a faster rate only if your application demands a quick action.   
- `Avg memory percentage`: Choose the avg memory usage percentage you wish to maintain for you redis instance  
- `Avg connection percentage`: Choose the avg number of client connections you wish to maintain with the redis instance
</details>

<details><summary>Scaling Configuration</summary>  
  
- `Scaling Enable` - If set, auto scaling action would be taken to maintain the avg metric percentages  
- `Min Plan` - Choose lower plan limit for scaling. If not set, lowest available plan will be selected   
- `Max Plan` - Choose upper plan limit for scaling. If not set, highest available plan will be selected   
- `Scaling Rate` - Choose rate at which scaling check should be performed  
</details>

<details><summary>Notification Configuration</summary>  
  
- `Threshold Breach` - Email notification to configured recipients whenever any threshold is crossed   
- `Scaling Success` - Email notification whenever a successful scaling action is performed   
- `Scaling Failure` - Email notification whenever there is a failure in scaling action   
</details>
