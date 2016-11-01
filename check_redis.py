import redis
redis_con = redis.Redis(host='redis', port=6379, db=0)
print("user_queue length:"+str(redis_con.llen('user_queue')))
print("already_get_user length:"+str(redis_con.hlen("already_get_user")))
