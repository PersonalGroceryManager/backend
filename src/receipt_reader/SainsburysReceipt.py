"""
This script contains the main class for parsing and storing data of a Sainsbury
receipt.

This file can be ran to verify the parsing logic.
"""
import argparse
import logging
from typing import List, Dict
from datetime import datetime as dt

# Third-Party Imports
import pandas as pd
from pypdf import PdfReader

# TODO: Create another Receipt class to be inherited (in case of other receipts)

class SainsburysReceipt():
    
    def __init__(self, pdf_file):

        self._file = pdf_file
                
        self._content = None           # A list of PDF lines (Raw)
        self._filtered_content = None  # A list of strings for items
        self._order_id = None          # Order ID
        self._order_date = None        # Order Date
        self._total_price = None       # Total price of order
        self._payment_card = None      # Last four digits of payment card
        self._quantities = None        # List of quantities for each item
        self._weights = None           # List of weights for each item
        self._names = None             # List of names for each item
        self._prices = None            # List of prices for each item

        self._item_df = None           # Pandas Dataframe of all orders
        self._json = None              # JSON representation of order
        
        self._parse_receipt()
        # Order ID, time, price and card
        self._find_order_info()
        # Order Items
        self._filter_content_to_items()
        self._find_items_info()
        self._process_item_info()
        self._jsonify_receipt()
  
    def _parse_receipt(self):
        """
        Uses the PdfReader module to read and parse the receipts pdf into a list, each element
        representing a line in the receipt.
        """
        reader = PdfReader(self._file)

        pdf_content = []
        for page in reader.pages:
            text = page.extract_text()  # This returns a single string of everything on the pdf
            lines = text.split("\n")    # This creates a list for each line
            pdf_content.extend(lines)   # Extend it to the pdf_content list
        self._content = pdf_content
        

    def _find_order_info(self):
        """
        Uses the PdfReader module to read and parse the receipts pdf into a list, each element
        representing a line in the receipt.
        """
    
        for idx, line in enumerate(self._content):
            
            # Look for order ID by splitting by colon ":"
            if line.startswith("Your receipt for order: "):
                _, order_id = line.split(':')  # Split into ["Your receipt for order:", order_id] 
                order_id = order_id.strip()    # Use strip to remove any leading/trailing whitespace
            
            # The time contains multiple colons. Therefore we look for the first colon only.
            if line.startswith("Slot time:"):
                first_colon_index = line.index(":")
                order_time = line[first_colon_index + 1:]
                order_time = order_time.strip()  # Use strip to remove any leading/trailing whitespace
            
            # The price is on the same line as "total paid"
            if line.startswith("Total paid"):
                _, total_price = line.split('£')
                total_price = float(total_price.strip())
            
            # The actual card number exists on the line after this text
            if line.startswith("We took payment on a card ending in"):
                # Next line, first four characters is the payment card
                payment_card = int(self._content[idx+1][0:4])
                break  # Break here since no information is needed after
            
            # For newer receipts, the card number appear on lines differently
            elif line.startswith("ending in"):
                # Same line, starting from 10th to 14th character
                payment_card = int(self._content[idx][10:14])
                break  # Break here since no information is needed after
            

        # Convert the date string into a datetime object.
        # ----------
        # Split the time information into a two components [date (Thursday 3rd August 2023), time (9:00pm - 10:00pm)]
        order_date, order_hour = order_time.split(',')
        # Further split the date information into day, date, month and year
        day, date, month, year = order_date.split()
        # Remove the suffixes from order_date by removing last two characters (st, nd, rd, th)
        date = date[:-2]
        # Process the hour data, retaining only the starting time (e.g. 1:00pm - 2:00pm)
        order_hour = order_hour.split(" - ")[0]
        # Rejoin the date information into a single string, then convert it into a datetime object
        order_date = f"{day} {date} {month} {year} {order_hour}"
        order_date = dt.strptime(order_date, r'%A %d %B %Y %I:%M%p')
        
        # Save permanently as attributes
        self._order_id = order_id
        self._order_date = order_date
        self._total_price = total_price
        self._payment_card = payment_card

    def _filter_content_to_items(self):
        """
        Remove unnecessary information within the receipt besides the orders. This is located between
        "Delivery summary" and "Order summary".
        """
        # The order starts after the line "Delivery summary" and ends after "Order summary". 
        # Only retain whatever is in between.
        for index, line in enumerate(self._content):
            if line.startswith("Delivery summary") or line.startswith("Groceries"):
                start_index = index
            elif line.startswith("Order summary"):
                end_index = index
        
        self._filtered_content = self._content[start_index + 1: end_index]


    def _find_items_info(self):
        """
        With a filtered list (e.g. returned from find_orders(content_list)), decouple each line into
        the "Quantity", "Item" and "Price" of each Item.

        Logic:
            1. The "amount" of an item is either:
                - Quantity
                - Weight
            2. Item name starts with a capital letter. This works most of the time since quantities are
            numeric, sometimes with lowercase units such as kg, g etc.
            3. Prices are the numeric values occuring after £
            4. For long orders (multi-lines) check whether the £ symbol appears. If it does not, append it to the next line
        """

        # Initialize lists
        quantities = []
        weights = []
        names = []
        prices = []

        previous_line = ''         # In case a single item spans multiple rows. See logic below.
        previous_line_length = 0   # To adjust pound index in case of multi-line rows
        
        for order in self._filtered_content:

            # Find the index of the pound symbol. Everything after this is assumed to be the price.      
            pound_index = order.rfind('£')

            # 1. If there is no pound symbol, pound_index will return -1. If this is the case, save the
            #    current line as a variable named "previous_line". As long as the pound symbol is not found, 
            #    it will keep adding to 'previous_line'.
            # 2. Variable previous_line_length is to readjust for pound_index since the multi-line order
            #    is appended together, so the index where the pound occurs is:
            #               previous_line_length + current_line_pound_index
            if pound_index == -1:
                previous_line = previous_line + order
                previous_line_length = len(order)
                continue   # Skip this loop
            
            # Whenever the pound_symbol is found, reset variables to an empty string to prepare
            # for additional multi-line orders.
            else:
                # Aggregate multi-line order into a single string
                order = previous_line + order
                pound_index = previous_line_length + pound_index
                
                # Reset variables
                previous_line = ''
                previous_line_length = 0
                
                # Analyse each character within the string.
                for index, char in enumerate(order):

                    # Find the index of the item name. Item name is assumed to be the first capital letter 
                    # (units are usually in ml, kg etc. that are not uppercase)
                    if char.isupper():
                        item_index = index
                        break
                
                # Using indices, categorize the information with their respective rows
                amount = order[: item_index].strip()  # .strip to remove whitespace from both sides
                name = order[item_index: pound_index - 1]
                price = order[pound_index + 1:]
                
                # Amount can either be quantity or weight. Store it as 'weight' if it ends with 'kg'.
                # Add other units in the future.
                if amount.endswith("kg"):
                    weight = float(amount[:-2])  # Strip the 'kg' characters
                    quantity = None
                else:
                    # Some text may leak into "amount" if the brand name is not
                    # capitalized, such as "innocent". We strip any text from
                    # amount and add it back to the name
                    cleaned_amount = ""
                    leftover_name  = ""
                    
                    # Loop across characters in amount
                    for idx, char in enumerate(amount):
                        
                        # Loop until we find a non-digit. All initial digits 
                        # will be assigned to amount, whereas all other 
                        # characters are leftover names
                        if not str.isdigit(char):
                            cleaned_amount = amount[:idx]
                            leftover_name = amount[idx:]    
                            break

                    # Since first character of "name" is currently capitalized,
                    # it makes sense to add a space             
                    name = leftover_name + " " + name
                    
                    # Default weight to none - TODO: Try to find weight info
                    # within "name"
                    weight = None
                    
                    # Safe type conversion 
                    quantity = int(cleaned_amount) if cleaned_amount else int(amount)

                # Append to each list
                quantities.append(quantity)            # Quantity stored as integers
                weights.append(weight)                 # Weight stored as floats
                names.append(name)                     # Item names stored as strings
                prices.append(float(price))            # Price stored as floats

        self._quantities = quantities
        self._weights = weights
        self._names = names
        self._prices = prices
    
    
    def _process_item_info(self):
        """
        With the quantities, weights, names and prices of each item, process the data such that each item
        always take one row (an item with a quantity of two will become two items of one quantity each).
        This is to ensure each item can be split separately.
        """
        
        # For rows with a quantity above one (quantity = n), split this into 
        # n rows and divide the price by n to obtain individual prices
        # ----------
        
        # New lists to store the decoupled information
        decoupled_weights = []
        decoupled_items = []
        decoupled_prices = []
        
        for quantity, weight, item, price in zip(self._quantities, self._weights, self._names, self._prices):
            # When quantity exceeds 1, split that order into individual items
            if (quantity) and (quantity > 1):
                decoupled_weights.extend([weight] * quantity)
                decoupled_items.extend([item] * quantity)
                # Prices are summed so these are divided by quantity
                decoupled_prices.extend([price/quantity] * quantity)
            
            # If quantity is one then just append it normally
            else:
                decoupled_weights.append(weight)
                decoupled_items.append(item)
                decoupled_prices.append(price)
                
        # Convert to dataframe as a viewable form
        self._item_df = pd.DataFrame(
            {
                # Append the order_id (which is equal throughout) for referencing other datatables
                'order_id': [self._order_id] * len(decoupled_items),
                'weight': decoupled_weights,
                'item_name': decoupled_items,
                'price': decoupled_prices
            }
        )
        
        # Store items as a list
        self._item_list = []
        for quantity, weight, item, price in zip(self._quantities, self._weights, self._names, self._prices):
            self._item_list.append({"item_name": item, "quantity": quantity, "weight": weight, "price": price})

        
    def _jsonify_receipt(self):
        """
        Store the receipt information into a JSON-like dictionary.
        """
        self._json = {
            "receipt_id": self._order_id,
            "slot_time": self._order_date,
            "items": [],
            "total_price": self._total_price,
            "payment_card": self._payment_card
            }
        
        for quantity, weight, name, price in zip(self._quantities, self._weights, self._names, self._prices):
            item_entry = {"name": name, "quantity": quantity, "weight": weight, "price": price}
            self._json["items"].append(item_entry)
        
    
    
    @property
    def order_id(self) -> int:
        return self._order_id
    
    @property
    def order_date(self) -> dt:
        return self._order_date
    
    @property
    def total_price(self) -> float:
        return self._total_price
    
    @property
    def payment_card(self) -> int:
        return self._payment_card
    
    @property
    def item_df(self) -> pd.DataFrame:
        return self._item_df
    
    @property
    def item_list(self) -> List[Dict]:
        return self._item_list
    
    @property
    def json(self) -> dict:
        return self._json
    
    
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description="PDF file of Sainsbury's receipt")
    parser.add_argument('--file', type=str, required=True, help="The path to the Sainsburys receipt.")
    args = parser.parse_args()
    file_path = args.file
    print(f"The file specified is {file_path}")
    
    Receipt = SainsburysReceipt(file_path)   # TODO: search the file name within the receipts directory
    
    print(f'Order ID:     {Receipt.order_id}')
    print(f"Order date:   {Receipt.order_date}")
    print(f'Total price:  {Receipt.total_price}')
    print(f'Payment card: {Receipt.payment_card}')
    print(f"Orders:       {Receipt.item_df}")
    print(f"Receipt Json: {Receipt.json}")
    