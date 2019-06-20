from django.shortcuts import render
from django.views import View

from goods.models import GoodsCategory, GoodsChannel

"""
categories = {
    '组号': {
                'channels': [] , # 当前组中的所有一级数据
                'sub_cats': [cat2.sub_cats, cat2],  # 当前组中的所有二级数据, 将来给每一个二级中多包装一个sub_cats用来保存它对应的三级
            }
    '组号' : {
                'channels': [],
                'sub_cats' : []
            }


}

"""
class IndexView(View):
    """首页"""

    def get(self, request):

        # 包装商品分类数据大字典
        categories = {}
        # 查询所有商品分组数据
        goods_channel_qs = GoodsChannel.objects.order_by('group_id', 'sequence')

        # 遍历商品频道查询集
        for channel_model in goods_channel_qs:

            # 获取当前组号
            group_id = channel_model.group_id

            if group_id not in categories:
                categories[group_id] = {
                    'channels': [],
                    'sub_cats': []
                }
            # 通过商品频道获取到一一对应的一级类别模型
            cat1 = channel_model.category
            cat1.url = channel_model.url
            # 把一级类别添加到当前组中
            categories[group_id]['channels'].append(cat1)


        context = {
            'categories': categories
        }
        return render(request, 'index.html', context)