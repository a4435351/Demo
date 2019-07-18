# -*- coding: utf-8 -*-

from collections import namedtuple, OrderedDict, defaultdict
from odoo import api, fields, models, registry, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    """ A rule describe what a procurement should do; produce, buy, move, ... """
    _inherit = 'stock.rule'

    procure_method = fields.Selection(selection_add=[('mts_else_mto', 'Take From Stock, if unavailable, Trigger Another Rule')],
        help="Take From Stock: the products will be taken from the available forecasted stock of the source location.\n"
             "Trigger Another Rule: the system will try to find a stock rule to bring the products in the source location. The available stock will be ignored.\n"
             "Take From Stock, if Unavailable, Trigger Another Rule: the products will be taken from the available stock of the source location."
             "If there is no stock available, the system will try to find a  rule to bring the products in the source location.")

    def _get_message_dict(self):
        """ Return a dict with the different possible message used for the
        rule message. It should return one message for each stock.rule action
        (except push and pull). This function is override in mrp and
        purchase_stock in order to complete the dictionary.
        """
        message_dict = {}
        source, destination, operation = self._get_message_values()
        if self.action in ('push', 'pull', 'pull_push'):
            suffix = ""
            if self.procure_method == 'make_to_order' and self.location_src_id:
                suffix = _("<br>A need is created in <b>%s</b> and a rule will be triggered to fulfill it.") % (source)
            if self.procure_method == 'mts_else_mto' and self.location_src_id:
                suffix = _("<br>If the products are not available in <b>%s</b>, a rule will be triggered to bring products in this location.") % source
            message_dict = {
                'pull': _('When products are needed in <b>%s</b>, <br/> <b>%s</b> are created from <b>%s</b> to fulfill the need.') % (destination, operation, source) + suffix,
                'push': _('When products arrive in <b>%s</b>, <br/> <b>%s</b> are created to send them in <b>%s</b>.') % (source, operation, destination)
            }
        return message_dict

    @api.model
    def _run_pull(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        res = super(StockRule, self).run_pull(product_id, product_qty, product_uom, location_id, name, origin, values)
        return res

    @api.model
    def _run_pull(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        moves_values_by_company = defaultdict(list)
        mtso_products_by_locations = defaultdict(list)

        if not self.location_src_id:
            msg = _('No source location defined on stock rule: %s!') % (self.name, )
            raise UserError(msg)

        if self.procure_method == 'mts_else_mto':
            mtso_products_by_locations[self.location_src_id].append(product_id.id)

        # Get the forecasted quantity for the `mts_else_mto` procurement.
        forecasted_qties_by_loc = {}
        for location, product_ids in mtso_products_by_locations.items():
            products = self.env['product.product'].browse(product_ids).with_context(location=location.id)
            forecasted_qties_by_loc[location] = {product.id: product.virtual_available for product in products}

        # Prepare the move values, adapt the `procure_method` if needed.
        procure_method = self.procure_method
        if procure_method == 'mts_else_mto':
            qty_needed = product_uom._compute_quantity(product_qty, product_id.uom_id)
            qty_available = forecasted_qties_by_loc[self.location_src_id][product_id.id]
            if float_compare(qty_needed, qty_available, precision_rounding=product_id.uom_id.rounding) <= 0:
                procure_method = 'make_to_stock'
                forecasted_qties_by_loc[self.location_src_id][product_id.id] -= qty_needed
            else:
                procure_method = 'make_to_order'

        # create the move as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
        # Search if picking with move for it exists already:
        group_id = False
        if self.group_propagation_option == 'propagate':
            group_id = values.get('group_id', False) and values['group_id'].id
        elif self.group_propagation_option == 'fixed':
            group_id = self.group_id.id
        move_values = self._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        move_values['procure_method'] = procure_method
        moves_values_by_company[self.company_id.id].append(move_values)

        for company_id, moves_values in moves_values_by_company.items():
            # create the move as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
            moves = self.env['stock.move'].sudo().with_context(force_company=company_id).create(moves_values)
            # Since action_confirm launch following procurement_group we should activate it.
            moves._action_confirm()
        return True
