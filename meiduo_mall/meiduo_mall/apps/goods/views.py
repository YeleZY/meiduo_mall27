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

class DetailView(View):
    """商品详情界面"""

    def get(self, request, sku_id):

        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')

        category = sku.category  # 获取当前sku所对应的三级分类

        # 查询当前sku所对应的spu
        spu = sku.spu

        """1.准备当前商品的规格选项列表 [8, 11]"""
        # 获取出当前正显示的sku商品的规格选项id列表
        current_sku_spec_qs = sku.specs.order_by('spec_id')
        current_sku_option_ids = []  # [8, 11]
        for current_sku_spec in current_sku_spec_qs:
            current_sku_option_ids.append(current_sku_spec.option_id)


        """2.构造规格选择仓库
        {(8, 11): 3, (8, 12): 4, (9, 11): 5, (9, 12): 6, (10, 11): 7, (10, 12): 8}
        """
        # 构造规格选择仓库
        temp_sku_qs = spu.sku_set.all()  # 获取当前spu下的所有sku
        # 选项仓库大字典
        spec_sku_map = {}  # {(8, 11): 3, (8, 12): 4, (9, 11): 5, (9, 12): 6, (10, 11): 7, (10, 12): 8}
        for temp_sku in temp_sku_qs:
            # 查询每一个sku的规格数据
            temp_spec_qs = temp_sku.specs.order_by('spec_id')
            temp_sku_option_ids = []  # 用来包装每个sku的选项值
            for temp_spec in temp_spec_qs:
                temp_sku_option_ids.append(temp_spec.option_id)
            spec_sku_map[tuple(temp_sku_option_ids)] = temp_sku.id


        """3.组合 并找到sku_id 绑定"""
        spu_spec_qs = spu.specs.order_by('id')  # 获取当前spu中的所有规格

        for index, spec in enumerate(spu_spec_qs):  # 遍历当前所有的规格
            spec_option_qs = spec.options.all()  # 获取当前规格中的所有选项
            temp_option_ids = current_sku_option_ids[:]  # 复制一个新的当前显示商品的规格选项列表
            for option in spec_option_qs:  # 遍历当前规格下的所有选项
                temp_option_ids[index] = option.id  # [8, 12]
                option.sku_id = spec_sku_map.get(tuple(temp_option_ids))  # 给每个选项对象绑定下他sku_id属性

            spec.spec_options = spec_option_qs  # 把规格下的所有选项绑定到规格对象的spec_options属性上

        context = {
            'categories': get_categories(),  # 商品分类
            'breadcrumb': get_breadcrumb(category),  # 面包屑导航
            'sku': sku,  # 当前要显示的sku模型对象
            'category': category,  # 当前的显示sku所属的三级类别
            'spu': spu,  # sku所属的spu
            'spec_qs': spu_spec_qs,  # 当前商品的所有规格数据
        }
        return render(request, 'detail.html', context)
