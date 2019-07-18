# -*- coding: utf-8 -*-

from collections import namedtuple
from datetime import datetime
from dateutil import relativedelta

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.osv import expression

import logging

_logger = logging.getLogger(__name__)


class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    def _get_global_route_rules_values(self):
        rules = super(Warehouse, self)._get_global_route_rules_values()
        rule = self.get_rules_dict()[self.id][self.delivery_steps]
        rule = [r for r in rule if r.from_loc == self.lot_stock_id][0]
        location_id = rule.from_loc
        location_dest_id = rule.dest_loc
        try:
            rules['mto_pull_id']['create_values'].update({
                'procure_method': 'mts_else_mto',
                'route_id': self._find_global_route('stock.route_warehouse0_mto', _('MTS else MTO')).id
            })
            rules['mto_pull_id']['update_values'].update({
                'name': self._format_rulename(location_id, location_dest_id, 'MTS else MTO'),
            })
        except Exception as e:
            _logger.error('Error while _get_global_route_rules_values %s.' % self.name)
        return rules

