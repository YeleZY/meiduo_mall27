from django.shortcuts import render
from django.views import View
from django import http
from django.core.paginator import Paginator, EmptyPage

from contents.utils import get_categories
from .utils import get_breadcrumb
from .models import GoodsCategory, SKU
from meiduo_mall.utils.response_code import RETCODE


class ListView(View):
    """商品列表界面"""

    def get(self, request, category_id, page_num):
        """
        :param category_id: # 三级类别id
        :param page_num: 要看第几页数据
        """
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('category_id不存在')

        # 获取前端传入的排序规则
        sort = request.GET.get('sort', 'default')

        sort_field = '-create_time'  # 定义默认的排序字段
        if sort == 'price':
            sort_field = '-price'
        elif sort == 'hot':
            sort_field = '-sales'

        # 查询出指定类别下的所有商品
        sku_qs = category.sku_set.filter(is_launched=True).order_by(sort_field)

        # 创建分页器对象: Paginator(要分页的所有数据, 指定每页显示多少条数据)
        paginator = Paginator(sku_qs, 5)
        try:
            # 获取到指定页中的所有数据
            page_skus = paginator.page(page_num)
        except EmptyPage:
            return http.HttpResponseForbidden('超出指定页')
        # 获取它的总页数据
        total_page = paginator.num_pages

        context = {
            'categories': get_categories(),  # 商品类别数据
            'breadcrumb': get_breadcrumb(category),  # 面包屑导航数据
            'sort': sort,  # 排序字段
            'category': category,  # 第三级分类
            'page_skus': page_skus,  # 分页后数据
            'total_page': total_page,  # 总页数
            'page_num': page_num,  # 当前页码
        }
        return render(request, 'list.html', context)

class HotGoodsView(View):
    '''商品热销排序'''
    def get(self, request ,category_id):
        #校验
        try:
            cat3 = GoodsCategory.objects.get(id = category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('category_id不存在')
        #取到category_id后查询获取商品3级下销量最高的前两个商品

        sku_qs = cat3.sku_set.filter(is_launched = True).order_by('-sales')[:2]
        #模型转字典
        sku_list = []#用来装sku字典
        for sku_model in sku_qs:
            sku_list.append({
                'id':category_id,
                'price':sku_model.price,
                'name':sku_model.name,
                'default_image_url':sku_model.default_image.url
            })
        #响应
        return http.JsonResponse({'code':RETCODE.OK, 'errmas':'ok', 'hot_skus': sku_list})
