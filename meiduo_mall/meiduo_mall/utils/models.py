from django.db import models

class BaseModel(models.Model):
    #为模型类增加字段
    create_time = models.DateField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateField(auto_now=True, verbose_name='更新时间')

    class Meta:
        abstract = True  #表明是抽象模型类，用于继承，不会迁移表