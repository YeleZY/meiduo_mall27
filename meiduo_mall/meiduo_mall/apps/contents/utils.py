from goods.models import GoodsChannel


def get_categories():
    """返回商品类别数据"""

    # 包装商品分类数据大字典
    categories = {}
    # 查询所有商品分组数据
    goods_channel_qs = GoodsChannel.objects.order_by('group_id', 'sequence')

    # 遍历商品频道查询集
    for channel_model in goods_channel_qs:

        # 获取当前组号
        group_id = channel_model.group_id

        # 判断组号在字典的key中是否存在,不存在,再去准备新字典
        if group_id not in categories:
            categories[group_id] = {
                'channels': [],
                'sub_cats': []
            }
        # 通过商品频道获取到一一对应的一级类别模型
        cat1 = channel_model.category
        # 为一级类别多定义一个url属性
        cat1.url = channel_model.url

        # 把一级类别添加到当前组中
        categories[group_id]['channels'].append(cat1)

        # 获取指定一级下面的所有二级类别
        cat2_qs = cat1.subs.all()
        # 遍历当前所有的二级查询集,给每个二级类别多定义一个sub_cats属性,用来记录它下面的所有三级
        for cat2 in cat2_qs:
            # 获取指定二级下面的所有三级
            cat3_qs = cat2.subs.all()
            # 将当前二级下面的所有三级类别存储到cat2的sbu_cats属性上
            cat2.sub_cats = cat3_qs
            # 将当前组中的每一个二级添加到sub_cats key对应的列表中
            categories[group_id]['sub_cats'].append(cat2)
    from pprint import pprint
    pprint(categories)
    return categories