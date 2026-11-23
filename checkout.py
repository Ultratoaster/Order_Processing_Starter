"""Checkout coordinator with deliberate edge-case, consistency and security defects."""
from models import OrderResult


class CheckoutService:
    def __init__(self, repository, payment_gateway):
        self.repository = repository
        self.payment_gateway = payment_gateway

    def checkout(self, cart, payment_token, request_id):
        if not cart or not payment_token or not request_id:
            return OrderResult(None, 'invalid', 0)

        existing = self.repository.check_order_status_by_request_id(request_id)
        
        
        if existing and existing[1] == 'paid':
            return OrderResult(existing[0], 'duplicate', existing[2])
                
        if len(cart.lines) == 0:
            return OrderResult(None, 'empty', 0)
        amount = cart.total()

        oos = False
        for line in cart.lines:
            product = self.repository.get_product(line.sku)
            if product.stock < line.quantity:
                oos = True
                print(f'Out of stock: {line.sku} requested {line.quantity}, available {product.stock}')
        if oos:
            return OrderResult(None, 'out_of_stock', amount)   
        
        print(f'Tendering payment.')

        try:
            response = self.payment_gateway.charge(amount, payment_token)
            status = 'paid' if response['approved'] else 'declined'
        except Exception:
            status = 'payment_error'
            print('Payment error occurred.')

        order_id = self.repository.save_order(cart.user_id, amount, status, request_id)

        if status != 'paid':
            return OrderResult(None, status, amount)
        
        for line in cart.lines:
            self.repository.update_stock(line.sku, line.quantity)
        cart.lines.clear()
        cart.discounted_total = None
        cart.discount_code = None
        cart.save()

        return OrderResult(order_id, status, amount)
