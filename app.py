from flask import Flask, render_template, url_for, request, session, redirect, jsonify, send_file
import json

app = Flask(__name__)
app.secret_key=b'\xba\x88<>il\r LR\x82\x10\xae\xe3\xc7\xf13\x0c\x19\x8eW\xbd\xf3\x02G\xce\x85\xc5\xd9\x97\x98\xf8\xe3\xbb\xfb]\x1a{\xc0\x8d[k\x17<\xe3\xf6\xd9u\xad~x\xdc\xd4\x90\xda\xa7<KE]b\xa6T\x04\xdc\xb0\x0fu)\xfc\x1f+\xa8\xd9\xac\xfb\x1bP^Q\xa5"b\x8f\x8a)\x01\xb5d\xd2\x00\x99S\xcb\x01\x184\x93\x94c'
VALID_CREDENTIALS = {'admin': 'brothersarethebest',
                     'jonathan': 'jonathancool'}
def load_json(filename):
    with open(filename, "r") as json_file:
        return json.load(json_file)
    
def write_json(filename, data):
    with open(filename, "w") as json_file:
        json.dump(data, json_file)

DRINKS = load_json("./storage/DRINKS.JSON")
BREAKFAST = load_json("./storage/BREAKFAST.JSON")
LUNCH = load_json("./storage/LUNCH.JSON")
JAPANESE = load_json("./storage/JAPANESE.JSON")
TABLE_ORDERS = load_json("./storage/TABLE_ORDERS.JSON")

import requests
import json
import pytz
import locale

from datetime import datetime, timedelta


class InvoiceGenerator:
    """ API Object for Invoice-Generator tool - https://invoice-generator.com/ """

    URL = "https://invoice-generator.com"
    DATE_FORMAT = "%d %b %Y"
    LOCALE = "en_US"
    TIMEZONE = "Europe/Paris"
    # Below are the default template parameters that can be changed (see https://github.com/Invoiced/invoice-generator-api/)
    TEMPLATE_PARAMETERS = [
        "header",
        "to_title",
        "ship_to_title",
        "invoice_number_title",
        "date_title",
        "payment_terms_title",
        "due_date_title",
        "purchase_order_title",
        "quantity_header",
        "item_header",
        "unit_cost_header",
        "amount_header",
        "subtotal_title",
        "discounts_title",
        "tax_title",
        "shipping_title",
        "total_title",
        "amount_paid_title",
        "balance_title",
        "terms_title",
        "notes_title",
    ]

    def __init__(self, sender, to,
                 logo=None,
                 ship_to=None,
                 number=None,
                 payments_terms=None,
                 due_date=None,
                 notes=None,
                 terms=None,
                 currency="USD",
                 date=datetime.now(tz=pytz.timezone(TIMEZONE)),
                 discounts=0,
                 tax=0,
                 shipping=0,
                 amount_paid=0,
                 ):
        """ Object constructor """
        self.logo = logo
        self.sender = sender
        self.to = to
        self.ship_to = ship_to
        self.number = number
        self.currency = currency
        self.custom_fields = []
        self.date = date
        self.payment_terms = payments_terms
        self.due_date = due_date
        self.items = []
        self.fields = {"tax": "%", "discounts": False, "shipping": False}
        self.discounts = discounts
        self.tax = tax
        self.shipping = shipping
        self.amount_paid = amount_paid
        self.notes = notes
        self.terms = terms
        self.template = {}

    def _to_json(self):
        """
        Parsing the object as JSON string
        Please note we need also to replace the key sender to from, as per expected in the API but incompatible with from keyword inherent to Python
        We are formatting here the correct dates
        We are also resetting the two list of Objects items and custom_fields so that it can be JSON serializable
        Finally, we are handling template customization with its dict
        """
        locale.setlocale(locale.LC_ALL, InvoiceGenerator.LOCALE)
        object_dict = self.__dict__
        object_dict['from'] = object_dict.get('sender')
        object_dict['date'] = self.date.strftime(InvoiceGenerator.DATE_FORMAT)
        if object_dict['due_date'] is not None:
            object_dict['due_date'] = object_dict.get('due_date')
        object_dict.pop('sender')
        for index, item in enumerate(object_dict['items']):
            object_dict['items'][index] = item.__dict__
        for index, custom_field in enumerate(object_dict['custom_fields']):
            object_dict['custom_fields'][index] = custom_field.__dict__
        for template_parameter, value in self.template.items():
            object_dict[template_parameter] = value
        object_dict.pop('template')
        return json.dumps(object_dict)

    def add_custom_field(self, name=None, value=None):
        """ Add a custom field to the invoice """
        self.custom_fields.append(CustomField(
            name=name,
            value=value
        ))

    def add_item(self, name=None, quantity=0, unit_cost=0.0, description=None):
        """ Add item to the invoice """
        self.items.append(Item(
            name=name,
            quantity=quantity,
            unit_cost=unit_cost,
            description=description
        ))

    def download(self, file_path):
        """ Directly send the request and store the file on path """
        json_string = self._to_json()
        response = requests.post(InvoiceGenerator.URL, json=json.loads(json_string), stream=True, headers={'Accept-Language': InvoiceGenerator.LOCALE})
        if response.status_code == 200:
            open(file_path, 'wb').write(response.content)
        else:
            raise Exception(f"Invoice download request returned the following message:{response.json()} Response code = {response.status_code} ")


    def set_template_text(self, template_parameter, value):
        """ If you want to change a default value for customising your invoice template, call this method """
        if template_parameter in InvoiceGenerator.TEMPLATE_PARAMETERS:
            self.template[template_parameter] = value
        else:
            raise ValueError("The parameter {} is not a valid template parameter. See docs.".format(template_parameter))

    def toggle_subtotal(self, tax="%", discounts=False, shipping=False):
        """ Toggle lines of subtotal """
        self.fields = {
            "tax": tax,
            "discounts": discounts,
            "shipping": shipping
        }


class Item:
    """ Item object for an invoice """

    def __init__(self, name, quantity, unit_cost, description=""):
        """ Object constructor """
        self.name = name
        self.quantity = quantity
        self.unit_cost = unit_cost
        self.description = description


class CustomField:
    """ Custom Field object for an invoice """

    def __init__(self, name, value):
        """ Object constructor """
        self.name = name
        self.value = value



# Create an instance of InvoiceGenerator







@app.route("/")
def home():
    return render_template("home.html")

@app.route("/staff/login", methods=["GET", "POST"])
def stafflogin():
    if request.method=="GET":
        return render_template("staff/login.html")
    elif request.method=="POST":
        username = request.form.get('username')
        password = request.form.get('password')

        if username in VALID_CREDENTIALS and VALID_CREDENTIALS[username] == password:
            session['username'] = username
            return redirect(url_for("staffdash"))
        else:
            return "Invalid username or password. Please try again."

@app.route("/staff")
def staffdash():
    if 'username' in session:
        return render_template("staff/dash.html", username=session["username"])
    else:
        return redirect(url_for("home"))


@app.route("/staff/logout")
def stafflogout():
    return redirect(url_for("stafflogin"))

@app.route("/staff/order/remove", methods=["GET", "POST"])
def order_r():
    global TABLE_ORDERS
    if request.method == "POST":
        TABLE_ORDERS = load_json("./storage/TABLE_ORDERS.JSON")
        table_number = str(request.form.get("table_number"))
        order_id = int(request.form.get("order_id"))

        if table_number in TABLE_ORDERS:
            removed_order = TABLE_ORDERS[table_number].pop(order_id - 1)
            write_json("storage/TABLE_ORDERS.JSON", TABLE_ORDERS)
            return f"Removed order for Table {table_number}, Order ID {order_id}: {removed_order['item']}"
        else:
            return f"Invalid table number or order ID."

    return render_template("staff/remove_order.html", table_orders=TABLE_ORDERS)
    

@app.route("/staff/order/drinks/", methods=["GET", "POST"])
def drinkorder_add():
    global TABLE_ORDERS
    if request.method == "POST":
        item_index = int(request.form.get("item_index"))
        table_number = str(request.form.get("table_number"))
        item_note = str(request.form.get("item_note"))

        selected_item = DRINKS[item_index]
        item_name = selected_item['name']
        item_price = selected_item['price']
        TABLE_ORDERS = load_json("storage/TABLE_ORDERS.JSON")

        if table_number not in TABLE_ORDERS:
            TABLE_ORDERS[table_number] = []

        # Calculate a unique order_id for the new item
        existing_order_ids = [int(order['order_id']) for order in TABLE_ORDERS[table_number]]
        if existing_order_ids:
            order_id = str(max(existing_order_ids) + 1)
        else:
            order_id = '1'

        TABLE_ORDERS[table_number].append({'status':'ordered','order_id': order_id, 'item': item_name, 'price': item_price, "note": item_note})
        write_json("storage/TABLE_ORDERS.JSON", TABLE_ORDERS)

    return render_template("staff/drinkorder.html", menu_items=DRINKS, table_orders=TABLE_ORDERS)

@app.route("/staff/order/breakfast/", methods=["GET", "POST"])
def breakfastorder_add():
    global TABLE_ORDERS
    if request.method == "POST":
        item_index = int(request.form.get("item_index"))
        table_number = str(request.form.get("table_number"))
        item_note = str(request.form.get("item_note"))

        selected_item = BREAKFAST[item_index]
        item_name = selected_item['name']
        item_price = selected_item['price']
        TABLE_ORDERS = load_json("storage/TABLE_ORDERS.JSON")

        if table_number not in TABLE_ORDERS:
            TABLE_ORDERS[table_number] = []

        # Calculate a unique order_id for the new item
        existing_order_ids = [int(order['order_id']) for order in TABLE_ORDERS[table_number]]
        if existing_order_ids:
            order_id = str(max(existing_order_ids) + 1)
        else:
            order_id = '1'

        TABLE_ORDERS[table_number].append({'status':'ordered','order_id': order_id, 'item': item_name, 'price': item_price, "note": item_note})
        write_json("storage/TABLE_ORDERS.JSON", TABLE_ORDERS)

    return render_template("staff/breakfastorder.html", menu_items=BREAKFAST, table_orders=TABLE_ORDERS)

@app.route("/staff/order/lunch/", methods=["GET", "POST"])
def lunchorder_add():
    global TABLE_ORDERS
    if request.method == "POST":
        item_index = int(request.form.get("item_index"))
        table_number = str(request.form.get("table_number"))
        item_note = str(request.form.get("item_note"))

        selected_item = LUNCH[item_index]
        item_name = selected_item['name']
        item_price = selected_item['price']
        TABLE_ORDERS = load_json("storage/TABLE_ORDERS.JSON")

        if table_number not in TABLE_ORDERS:
            TABLE_ORDERS[table_number] = []

        # Calculate a unique order_id for the new item
        existing_order_ids = [int(order['order_id']) for order in TABLE_ORDERS[table_number]]
        if existing_order_ids:
            order_id = str(max(existing_order_ids) + 1)
        else:
            order_id = '1'

        TABLE_ORDERS[table_number].append({'status':'ordered','order_id': order_id, 'item': item_name, 'price': item_price, "note": item_note})
        write_json("storage/TABLE_ORDERS.JSON", TABLE_ORDERS)

    return render_template("staff/lunchorder.html", menu_items=LUNCH, table_orders=TABLE_ORDERS)

@app.route("/staff/order/japanese/", methods=["GET", "POST"])
def japaneseorder_add():
    global TABLE_ORDERS
    if request.method == "POST":
        item_index = int(request.form.get("item_index"))
        table_number = str(request.form.get("table_number"))
        item_note = str(request.form.get("item_note"))

        selected_item = JAPANESE[item_index]
        item_name = selected_item['name']
        item_price = selected_item['price']
        TABLE_ORDERS = load_json("storage/TABLE_ORDERS.JSON")

        if table_number not in TABLE_ORDERS:
            TABLE_ORDERS[table_number] = []

        # Calculate a unique order_id for the new item
        existing_order_ids = [int(order['order_id']) for order in TABLE_ORDERS[table_number]]
        if existing_order_ids:
            order_id = str(max(existing_order_ids) + 1)
        else:
            order_id = '1'

        TABLE_ORDERS[table_number].append({'status':'ordered','order_id': order_id, 'item': item_name, 'price': item_price, "note": item_note})
        write_json("storage/TABLE_ORDERS.JSON", TABLE_ORDERS)

    return render_template("staff/lunchorder.html", menu_items=JAPANESE, table_orders=TABLE_ORDERS)

@app.route("/kitchen/mark/<table>/<int:id>")
def kitchenmark(table, id):
    TABLE_ORDERS = load_json("./storage/TABLE_ORDERS.JSON")
    if table in TABLE_ORDERS:
        orders_for_table = TABLE_ORDERS[table]
        if "1" <= str(id) <= str(len(orders_for_table)):
            selected_order = orders_for_table[int(id) - 1]
            selected_order["status"] = f"Waiting For Delivery {session['username']}"
            write_json("./storage/TABLE_ORDERS.JSON", TABLE_ORDERS)
            return jsonify(TABLE_ORDERS), 200
        else:
            return jsonify({"message": "Invalid order id"}), 404
    else:
        return jsonify({"message": "Invalid table number"}), 404

@app.route("/waiter/mark/<table>/<int:id>")
def waitermark(table, id):
    TABLE_ORDERS = load_json("./storage/TABLE_ORDERS.JSON")
    if table in TABLE_ORDERS:
        orders_for_table = TABLE_ORDERS[table]
        if "1" <= str(id) <= str(len(orders_for_table)):
            selected_order = orders_for_table[int(id) - 1]
            selected_order["status"] = f"Delivered by {session['username']}"
            write_json("./storage/TABLE_ORDERS.JSON", TABLE_ORDERS)
            return jsonify(TABLE_ORDERS), 200
        else:
            return jsonify({"message": "Invalid order id"}), 404
    else:
        return jsonify({"message": "Invalid table number"}), 404


    
@app.route("/staff/order/view/<table>/")
def view_order(table):
    TABLE_ORDERS = load_json("storage/TABLE_ORDERS.JSON")
    orders_for_table = TABLE_ORDERS.get(table, [])
    
    return render_template("staff/view_order.html", table_number=table, orders=orders_for_table)

@app.route("/generate_invoice/<table_number>")
def generate_invoice(table_number):
    global TABLE_ORDERS
    # Assuming you have a way to fetch the orders for the given table_number
    table_orders = table_number
    TABLE_ORDERS = load_json("./storage/TABLE_ORDERS.JSON")
    
    # Create an InvoiceGenerator instance
    invoice = InvoiceGenerator(
        sender="Brothers Restarant",
        to=f"Table {table_number}",
        logo="favicon.png",
        number="INVOICE",
        payments_terms="No Refunds",
        due_date="PAID",
        notes="Thank you for your business!",
        terms="No refunds.",
        currency="GBP",
        discounts=0,
        tax=0,
        shipping=0,
    )


    # Add items based on the table orders
    for order in TABLE_ORDERS[str(table_number)]:
        invoice.add_item(name=order["item"], quantity=1, unit_cost=order["price"])

    # Customize template text
    invoice.set_template_text("header", "Invoice")
    invoice.set_template_text("subtotal_title", "Subtotal:")
    invoice.set_template_text("total_title", "Total Amount Due:")

    # Toggle subtotal lines
    invoice.toggle_subtotal(tax="%", discounts=True, shipping=True)

    # Download the invoice as a PDF file
    file_path = f"invoice_table_{table_number}.pdf"
    invoice.download(file_path)

    # Return a response to allow the user to download the PDF
    return send_file(file_path, as_attachment=True)

@app.route("/staff/extracharge/<table>/<charge>/<note>")
def extracharge(table, charge, note):
    existing_order_ids = [int(order['order_id']) for order in TABLE_ORDERS[table]]
    if existing_order_ids:
        order_id = str(max(existing_order_ids) + 1)
    else:
        order_id = '1'
    if not TABLE_ORDERS[table]:
        TABLE_ORDERS[table].append({'status':'ordered','order_id': order_id, 'item': 'extra charges', 'price': charge, "note": note})
    else:
        TABLE_ORDERS[table] = []
        TABLE_ORDERS[table].append({'status':'ordered','order_id': order_id, 'item': 'extra charges', 'price': charge, "note": note})
    
    

@app.route("/getlist")
def getlist():
    return load_json("storage/TABLE_ORDERS.JSON")

@app.route("/getmenu/<menu>")
def getmenu(menu):
    return load_json("./storage/"+menu)


if __name__ == "__main__":
    app.run(port=33921)