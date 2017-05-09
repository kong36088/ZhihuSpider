import configparser

import redis

config = configparser.ConfigParser()
config.read("config.ini")

redis_host = config.get("redis", "host")
redis_port = config.get("redis", "port")

redis_con = redis.Redis(host=redis_host, port=redis_port, db=0)
print("user_queue length:"+str(redis_con.llen('user_queue')))
print("already_get_user length:"+str(redis_con.hlen("already_get_user")))
