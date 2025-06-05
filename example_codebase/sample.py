
def calculate_total(items):
    """Calculate total price of items."""
    total = 0
    for item in items:
        if hasattr(item, 'price'):
            total += item.price
        else:
            print(f"Warning: {item} has no price attribute")
    return total

class ShoppingCart:
    def __init__(self):
        self.items = []
    
    def add_item(self, item):
        self.items.append(item)
    
    def get_total(self):
        return calculate_total(self.items)
    
    def clear(self):
        self.items = []

def process_order(cart):
    """Process a shopping cart order."""
    if not cart.items:
        raise ValueError("Cannot process empty cart")
    
    total = cart.get_total()
    if total <= 0:
        raise ValueError("Invalid cart total")
    
    # Simulate payment processing
    print(f"Processing payment for ${total:.2f}")
    return {"status": "success", "total": total}
