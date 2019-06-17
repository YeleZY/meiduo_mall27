from celery import Celery
import os

# 因为发邮件函数中使用了Django的配置文件,所以要提前告知celery将来如果需要用Django配置文件,去那里找
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")

# 1.创建celery客户端对象
celery_app = Celery('meiduo')

# 2.加载celery的配置, 让生产者知道自己生产的任务存放到哪?
celery_app.config_from_object('celery_tasks.config')

# 3.自动注册任务(告诉生产者,它能生产什么亲的任务)
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email'])
