from fdfs_client.client import Fdfs_client

#创建fdfs客户端对象
client = Fdfs_client('./client.conf')
#上传
re = client.upload_appender_by_filename('/home/python/Desktop/01.jpg')
print(re)