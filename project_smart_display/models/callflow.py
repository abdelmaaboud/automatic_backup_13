# -*- coding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions SARL
# in Luxembourg 2018

from odoo import models, fields

class Callflow(models.Model):
    _name = 'project.smart.display.callflow'

    name = fields.Char()
    number = fields.Char()
    display_ids = fields.Many2many('project.smart.display')