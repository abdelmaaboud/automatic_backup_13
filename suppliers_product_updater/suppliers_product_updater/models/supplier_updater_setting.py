# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from lxml import etree
from xml.dom import minidom
from xml.dom.minidom import Node
import tempfile
from ftplib import FTP
import pysftp
import zipfile
import datetime
import requests
import re

import logging
_logger = logging.getLogger(__name__)


class UpdaterSetting(models.Model):
    _name = 'supplier.updater.setting'

    active = fields.Boolean('Active')
    demo_mode = fields.Boolean('Demo mode')
    frequency = fields.Integer('Update frequency (in hours)')
    last_update = fields.Datetime('Last Execution', readonly=True)

    supplier_mode = fields.Selection([('td', 'TechData'), ('also', 'Also'), ('im', 'Ingram Micro')], string="Supplier mode")
    supplier_id = fields.Many2one('res.partner', string="Supplier")

    # TechData
    td_customer_number = fields.Char('TechData - Customer number')
    td_auth_code = fields.Char('TechData - Auth code')
    td_info_type = fields.Selection([('STOCK', 'STOCK'), ('PRICE', 'PRICE'), ('PRICE DETAILS', 'PRICE DETAILS'), ('FULL', 'FULL'), ('QUICK', 'QUICK')], 'TechData - Info Type')

    # ALSO
    also_server = fields.Char('Also - Server')
    also_user = fields.Char('Also - User')
    also_password = fields.Char('Also - Password')
    also_file = fields.Char('Also - File path')

    # Ingram Micro
    im_server = fields.Char('Ingram Micro - Server')
    im_user = fields.Char('Ingram Micro - User')
    im_password = fields.Char('Ingram Micro - Password')
    im_file = fields.Char('Ingram Micro - File path')

    #Update the frequency in the cron "Supplier APIs Products Updater"
    """@api.onchange('frequency')
    def update_cron_interval(self):
        cron_id = self.env.ref('suppliers_product_updater.ir_cron_suppliers_product_updater_setting')
        cron_id.interval_number = self.frequency"""

    def name_get(self):
        res=[]
        for setting in self:
            name = setting.supplier_mode + " - " + setting.supplier_id.name
            if setting.demo_mode:
                name += " - DEMO"
            if setting.last_update:
                name += " (" + setting.last_update + ")"
            res.append((setting.id, name))
        return res

    @api.multi
    def execute_updater(self):
        # List of product
        for setting in self:
            supplierinfo_ids = self.env['product.supplierinfo'].search([
                ('state', '!=', 'obsolete'),
                ('name', '=', setting.supplier_id.id)]
            )
            setting.execute_updater_for_supplierinfo_ids(supplierinfo_ids)
            setting.last_update = datetime.datetime.now()

    @api.multi
    def execute_updater_for_supplierinfo_ids(self, supplierinfo_ids):
        for setting in self:
            if setting.supplier_mode == 'td':
                setting.updateProductsForTechData(supplierinfo_ids)

            elif setting.supplier_mode == 'also':
                setting.updateProductsForALSO(supplierinfo_ids)

            elif setting.supplier_mode == 'im':
                setting.updateProductsForIngramMicro(supplierinfo_ids)

            _logger.debug("Check obsolesence")
            setting.checkObsolesenceForSupplierInfo(supplierinfo_ids)

            # Log last run time



    # ---- CRON METHODS
    def _cron_suppliers_product_updater(self):
        setting_ids = self.env['supplier.updater.setting'].search([('active', '=', True)])

        for setting in setting_ids:
            # Check last update
            if (fields.Datetime.from_string(setting.last_update) + datetime.timedelta(hours=setting.frequency) <= datetime.datetime.now()):
                setting.execute_updater()

    # ---- MODEL METHODS : SUPPLIER UPDATER METHODS
    def updateProductsForTechData(self, supplierinfo_ids):
        numberOfProducts = len(supplierinfo_ids)
        step = 500
        interationCounter = 0

        while(interationCounter * step < numberOfProducts):

            start = interationCounter * step
            end = (interationCounter + 1) * step
            if end > numberOfProducts:
                end = numberOfProducts

            interationCounter += 1

            supplierinfo_by_segment = supplierinfo_ids[start:end]

            # Get the products that are supplied by TechData
            products_by_techdata = []
            for supplierinfo in supplierinfo_by_segment:
                # Demo mode, limit to max 10 products
                if self.demo_mode and len(products_by_techdata) == 10:
                    break

                distrib_code = supplierinfo.product_code if (supplierinfo.product_code and supplierinfo.product_code.find("-") == -1 and not re.search('[a-zA-Z]', supplierinfo.product_code) and self.representsInt(supplierinfo.product_code) and len(supplierinfo.product_code) < 8) else False

                products_by_techdata.append([supplierinfo.product_tmpl_id.id, supplierinfo.product_tmpl_id.default_code, distrib_code])

            # Create an XML with an entry for each product that has TechData as supplier
            nsmap = {}
            onlinecheck = etree.Element("OnlineCheck", nsmap=nsmap)

            # Header
            header_node = etree.Element("Header")

            node = etree.Element("BuyerAccountId")
            node.text = self.td_customer_number
            header_node.append(node)

            node = etree.Element("AuthCode")
            node.text = self.td_auth_code
            header_node.append(node)

            node = etree.Element("Type")
            node.text = self.td_info_type
            header_node.append(node)

            onlinecheck.append(header_node)

            # Items
            i = 1
            for prod in products_by_techdata:
                if not prod[1] and not prod[2]:
                    continue
                prod_node = etree.SubElement(onlinecheck, "Item", line=str(i))
                # Manuf ID
                manuf_id = etree.SubElement(prod_node, "ManufacturerItemIdentifier")
                if prod[2] == False and prod[1] != False:
                    manuf_id.text = str(prod[1])
                #prod_node.append(manuf_id)
                # Distrib ID
                distrib_id = etree.SubElement(prod_node, "DistributorItemIdentifier")
                if prod[2] != False:
                    distrib_id.text = str(prod[2])
                #prod_node.append(distrib_id)
                # Quantity
                quant = etree.SubElement(prod_node, "Quantity")
                quant.text = str(1)

                i = i + 1

            _logger.debug("Request: %s", etree.tostring(onlinecheck, pretty_print=True))

            url = "http://intcom.xml.techdata-europe.com:8080/Onlchk"
            #if self.demo_mode == True:
            #    url = "http://intcom.xml.quality.techdata.de:8080/Onlchk"
            #_logger.debug("Send Request to URL: %s", url)

            # Send the XML & get the result
            request = requests.post(url, data={'xmlmsg': etree.tostring(onlinecheck, pretty_print=True)})
            #_logger.debug("Request result: %s", request.status_code)

            # HTTP request satus == OK
            if request.status_code == 200:
                # Get the result
                result = request.content
                _logger.debug("XML: %s", result) #etree.tostring(result, pretty_print=True))

                # Parse the XML
                #dom = minidom.parseString(result.encode('utf-8'))

                root = etree.fromstring(result)
                for child in root:
                    if child.tag == "Item":
                        #_logger.debug("Item: %s", etree.tostring(child, pretty_print=True))
                        #line_number = int(child.attrib['line'])
                        distrib_code = ""
                        manuf_code = ""
                        unit_price = 0.0
                        state = "sellable"
                        quantity_available = 0
                        array_index = 0

                        for info in child:
                            # Manuf code
                            if info.tag == "ManufacturerItemIdentifier":
                                manuf_code = info.text

                            # Distrib code
                            if info.tag == "DistributorItemIdentifier":
                                distrib_code = info.text

                            # EAN
                            if info.tag == "EAN":
                                ean = info.text

                            # Availability
                            if info.tag == "AvailabilityTotal":
                                if info.text is not None:
                                    quantity_available = int(info.text)

                            # Price
                            if info.tag == "UnitPriceAmount":
                                if info.text is not None:
                                    p = info.text.replace(",", ".")
                                    unit_price = float(p)

                            # Obsolesence
                            if info.tag == "Note":
                                if info.text != '' and (str(info.text).find("obsolete") > -1
                                                        or str(info.text).find("is not maintained in our catalogue") > -1):
                                    state = "obsolete"

                        # Update the products
                        product_id = self.getIdFromDistAndManufNumbers(products_by_techdata, distrib_code, manuf_code)
                        self.updateProductInSystem(product_id, self.supplier_id, distrib_code, unit_price, quantity_available, ean, manuf_code, state)

            else:
                _logger.debug("There was an error while getting the result from techData: %s", request.status_code)

    def updateProductsForALSO(self, supplierinfo_ids):

        fileLines = self.ftpGetFileAsLinesListUnzipFirst('ftp', self.also_server, self.also_user, self.also_password, self.also_file)

        if not fileLines or len(fileLines) == 0:
            _logger.debug("Downloaded file is corrupted")
            return

        allowedHeaderNames = ['ProductID','EuropeanArticleNumber','AvailableQuantity','NetPrice','EndOfLife']
        headerNames_Names_TableIndex = {}

        headerNamesList = fileLines[0].split(";")

        for i in range(0, len(headerNamesList)):
            headerNames_Names_TableIndex[headerNamesList[i]] = i

        dataLines = {}

        for line in fileLines[1:len(fileLines)]:
            line = line.replace('"', '')
            dataLine = line.split(";")
            ean13 = dataLine[headerNames_Names_TableIndex['EuropeanArticleNumber']]
            dataLines[ean13] = {
                headerNames_Names_TableIndex[allowedHeaderNames[0]]: dataLine[headerNames_Names_TableIndex[allowedHeaderNames[0]]],
                headerNames_Names_TableIndex[allowedHeaderNames[1]]: dataLine[headerNames_Names_TableIndex[allowedHeaderNames[1]]],
                headerNames_Names_TableIndex[allowedHeaderNames[2]]: dataLine[headerNames_Names_TableIndex[allowedHeaderNames[2]]],
                headerNames_Names_TableIndex[allowedHeaderNames[3]]: dataLine[headerNames_Names_TableIndex[allowedHeaderNames[3]]],
                headerNames_Names_TableIndex[allowedHeaderNames[4]]: dataLine[headerNames_Names_TableIndex[allowedHeaderNames[4]]],
            }

        for supplierinfo in supplierinfo_ids:
            supplier_code = ''
            quantity_available = 0
            state = "obsolete"
            price = 0
            product = supplierinfo.product_tmpl_id
            ean = False

            if product.barcode in dataLines:
                productDict = dataLines[product.barcode]
                supplier_code = productDict[headerNames_Names_TableIndex['ProductID']]
                price = float(productDict[headerNames_Names_TableIndex['NetPrice']])
                quantity_available = int(productDict[headerNames_Names_TableIndex['AvailableQuantity']])
                stateTmp = productDict[headerNames_Names_TableIndex['EndOfLife']]

                if stateTmp and stateTmp == 'X':
                    state = "obsolete"
                else:
                    state = "sellable"
            else:
                state = "obsolete"
                quantity_available = 0
                supplier_code = ''


            self.updateProductInSystem(product.id, self.also_partner_id, supplier_code, price, quantity_available, ean, state)

    def updateProductsForIngramMicro(self, supplierinfo_ids):
        try:
            file = self.ftpGetFileAsLinesList('sftp', self.im_server, self.im_user, self.im_password, self.im_file)
        except IOError:
            raise UserError(_('Eror with the file!'))

        allowedHeaderNames = ['Ingram Part Number','EANUPC Code','Availability (Local Stock)','Customer Price Including Fees', 'Vendor Part Number']
        headerNames_Names_TableIndex = {}

        headerNamesList = file.readline().split(",")
        #_logger.debug("\n HeaderNames : %s", headerNamesList)

        for i in range(0, len(headerNamesList)):
            headerNames_Names_TableIndex[headerNamesList[i]] = i

        dataLinesByIMCode = {}
        dataLinesByEAN = {}
        for line in file: #[1:len(fileLines)]:
            dataLine = line.split(",")
            im_code = int(dataLine[headerNames_Names_TableIndex['Ingram Part Number']])
            dataLinesByIMCode[im_code] = {
                headerNames_Names_TableIndex[allowedHeaderNames[0]]: dataLine[headerNames_Names_TableIndex[allowedHeaderNames[0]]],
                headerNames_Names_TableIndex[allowedHeaderNames[1]]: dataLine[headerNames_Names_TableIndex[allowedHeaderNames[1]]],
                headerNames_Names_TableIndex[allowedHeaderNames[2]]: dataLine[headerNames_Names_TableIndex[allowedHeaderNames[2]]],
                headerNames_Names_TableIndex[allowedHeaderNames[3]]: dataLine[headerNames_Names_TableIndex[allowedHeaderNames[3]]],
                headerNames_Names_TableIndex[allowedHeaderNames[4]]: dataLine[headerNames_Names_TableIndex[allowedHeaderNames[4]]],
            }
            ean13 = dataLine[headerNames_Names_TableIndex['EANUPC Code']]
            dataLinesByEAN[ean13] = {
                headerNames_Names_TableIndex[allowedHeaderNames[0]]: dataLine[headerNames_Names_TableIndex[allowedHeaderNames[0]]],
                headerNames_Names_TableIndex[allowedHeaderNames[1]]: dataLine[headerNames_Names_TableIndex[allowedHeaderNames[1]]],
                headerNames_Names_TableIndex[allowedHeaderNames[2]]: dataLine[headerNames_Names_TableIndex[allowedHeaderNames[2]]],
                headerNames_Names_TableIndex[allowedHeaderNames[3]]: dataLine[headerNames_Names_TableIndex[allowedHeaderNames[3]]],
                headerNames_Names_TableIndex[allowedHeaderNames[4]]: dataLine[headerNames_Names_TableIndex[allowedHeaderNames[4]]],
            }

        for supplierinfo in supplierinfo_ids:
            product = supplierinfo.product_tmpl_id

            # Supplier product code exists in the system
            if supplierinfo.product_code != '' and supplierinfo.product_code in dataLinesByIMCode:
                productDict = dataLinesByIMCode[supplierinfo.product_code]
                _logger.debug("\n found by IMCODE : Product Dict : %s", productDict)

                supplier_code = int(productDict[headerNames_Names_TableIndex['Ingram Part Number']])
                product_code = productDict[headerNames_Names_TableIndex['Vendor Part Number']]
                price = float(productDict[headerNames_Names_TableIndex['Customer Price Including Fees']])
                quantity_available = int(productDict[headerNames_Names_TableIndex['Availability (Local Stock)']])
                ean = productDict[headerNames_Names_TableIndex['EANUPC Code']]

                self.updateProductInSystem(product.id, self.supplier_id, supplier_code, price, quantity_available, ean, product_code, 'sellable')

            # EAN exists in the system
            elif product.barcode != '' and product.barcode in dataLinesByEAN:
                productDict = dataLinesByEAN[product.barcode]
                _logger.debug("\n found by EAN : Product Dict : %s", productDict)

                product_code = productDict[headerNames_Names_TableIndex['Vendor Part Number']]
                supplier_code = int(productDict[headerNames_Names_TableIndex['Ingram Part Number']])
                price = float(productDict[headerNames_Names_TableIndex['Customer Price Including Fees']])
                quantity_available = int(productDict[headerNames_Names_TableIndex['Availability (Local Stock)']])

                self.updateProductInSystem(product.id, self.supplier_id, supplier_code, price, quantity_available,  product.barcode, product_code, 'sellable')

            else:
                self.updateProductInSystem(product.id, self.supplier_id, '', 0, 0,  False, False, 'obsolete')



    def checkObsolesenceForSupplierInfo(self, supplierinfo_ids):
        for supplier_info in supplierinfo_ids:
            if len(supplier_info.product_tmpl_id.seller_ids) > 0 and all([s == "obsolete" for s in supplier_info.product_tmpl_id.seller_ids.mapped('state')]):
                supplier_info.product_tmpl_id.state = "obsolete"
            else:
                supplier_info.product_tmpl_id.state = "sellable"

    def updateProductInSystem(self, product_id, supplier_id, supplier_code, price, quantity_available, ean, internal_ref, state):
        if not product_id:
            return

        product_id = self.env['product.template'].browse([product_id])

        # Set the last price update date
        product_id.last_update_price = datetime.datetime.now()

        for supp in product_id.seller_ids:
            if supp.name == supplier_id:
                if supp.product_code != "" and not (supp.product_code == supplier_code):
                    supp.product_code = supplier_code

                product_id.last_update_price = datetime.datetime.now()
                supp.qty_available = quantity_available
                if ean:
                    supp.product_tmpl_id.barcode = ean
                supp.last_update = datetime.datetime.now()
                supp.state = state
                supp.price = float(price)
                if internal_ref:
                    product_id.default_code = internal_ref

                return

        if (price > 0 and state != 'obsolete'):
            # create a new supplierinfo
            #_logger.debug("create supplier info for template id: %s (product id=%s)", product.product_tmpl_id, product)
            self.env['product.supplierinfo'].create({
                    'product_tmpl_id': product_id.id,
                    'name': supplier_id.id,
                    'product_code': supplier_code,
                    'qty_available': int(quantity_available),
                    'min_qty': 0,
                    'delay': 1,
                    'last_update': datetime.datetime.now(),
                    'state': state,
                    'price': float(price),
                })

    # ---- UTILS METHODS
    def representsInt(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def getIdFromDistAndManufNumbers(self, array, dist_num, manuf_num):
        for p in array:
            if p[2] == dist_num:
                return p[0]
            if p[1] == manuf_num:
                return p[0]
        return False

    def ftpGetFileAsLinesListUnzipFirst(self, serverMode, serverAddress, username, password, path):
        tempFile = self.ftpGetFile(serverMode, serverAddress, username, password, path)

        #ZIP
        archive = zipfile.ZipFile(tempFile)
        #Takes the first file in ZIP
        for name in archive.namelist():
            extractedFile = archive.open(name)
            break

        #extractedFile.seek(0, 0);
        fileLines = extractedFile.readlines()
        extractedFile.close()
        archive.close()
        tempFile.close()
        return fileLines

    def ftpGetFileAsLinesList(self, serverMode, serverAddress, username, password, path):
        if serverMode == 'ftp':
            # doc: https://pythonprogramming.net/ftp-transfers-python-ftplib/
            ftp = FTP(serverAddress)
            ftp.login(user=username, passwd = password)
            # doc: https://pymotw.com/2/tempfile/
            tempFile = tempfile.TemporaryFile()
            ftp.retrbinary('RETR ' + path, tempFile.write, 1024)
            ftp.quit()
            tempFile.seek(0, 0)
            return tempFile.readlines()

        elif serverMode == 'sftp':
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            srv = pysftp.Connection(host=serverAddress, username=username, password=password, cnopts=cnopts)
            tmp_local_path = '/tmp/supplier_import.txt'
            srv.get(path, tmp_local_path)
            srv.close()
            tmp_file = open(tmp_local_path, 'r')
            return tmp_file
