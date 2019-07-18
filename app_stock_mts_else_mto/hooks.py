# -*- coding: utf-8 -*-

# Created on 2018-10-12
# author: 广州尚鹏，https://www.sunpop.cn
# email: 300883@qq.com
# resource of Sunpop
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

# Odoo在线中文用户手册（长期更新）
# https://www.sunpop.cn/documentation/user/10.0/zh_CN/index.html

# Odoo10离线中文用户手册下载
# https://www.sunpop.cn/odoo10_user_manual_document_offline/
# Odoo10离线开发手册下载-含python教程，jquery参考，Jinja2模板，PostgresSQL参考（odoo开发必备）
# https://www.sunpop.cn/odoo10_developer_document_offline/
# description:

from odoo import api, SUPERUSER_ID, _


def pre_init_hook(cr):
    pass
    # cr.execute("")

def post_init_hook(cr, registry):
    # 处理现有的mto变成 MTS else MTO 的路线，模拟write delivery_steps
    try:
        env = api.Environment(cr, SUPERUSER_ID, {})
        warehouses = env['stock.warehouse'].search([('active', '=', True)])
        for wh in warehouses:
            if wh.active and wh.delivery_steps:
                wh.write({
                    'delivery_steps': wh.delivery_steps,
                })
        rules = env['stock.rule'].sudo().search([('action', 'in', ('pull', 'pull_push')), ('procure_method', '=', 'make_to_order')])
        rules.write({
                'procure_method': 'mts_else_mto',
            })
    except Exception as e:
        pass

def uninstall_hook(cr, registry):
    # 把 MTS else MTO 的路线 换回原来 MTO
    try:
        env = api.Environment(cr, SUPERUSER_ID, {})
        mto_route = env.ref('stock.route_warehouse0_mto')
        mto_route.write({
            'name': _('Make To Order'),
        })
        mto_route.with_context(lang='en_US').write({
            'name': 'Make To Order',
        })

        warehouses = env['stock.warehouse'].search([('active', '=', True)])
        for wh in warehouses:
            if wh.active and wh.delivery_steps:
                wh.write({
                    'delivery_steps': wh.delivery_steps,
                })
        rules = env['stock.rule'].sudo().search([('action', 'in', ('pull', 'pull_push')), ('procure_method', '=', 'mts_else_mto')])
        rules.write({
                'procure_method': 'make_to_order',
            })
    except Exception as e:
        pass

