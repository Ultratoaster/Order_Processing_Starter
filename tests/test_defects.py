"""One test per defect in DEFECTS.MD (numbers refer to that list)."""
from decimal import Decimal

from cart import ShoppingCart
from checkout import CheckoutService
from payments import FakePaymentGateway


# 1. Discounts stacked and could go negative

def test_discounts_do_not_stack(cart):
    cart.add_item('MOU-01', 2)  # 59.90
    cart.apply_discount('WELCOME10')
    cart.apply_discount('WELCOME10')
    assert cart.total() == Decimal('53.91')


def test_flat_discount_never_makes_total_negative(cart):
    cart.add_item('USB-01', 1)  # 9.99 < 15
    cart.apply_discount('SAVE15')
    assert cart.total() == Decimal('0.00')


# 2. Negative / zero quantities

def test_non_positive_quantities_rejected(cart):
    assert cart.add_item('USB-01', -1) is False
    assert cart.add_item('USB-01', 0) is False
    cart.add_item('USB-01', 2)
    assert cart.remove_item('USB-01', -3) is False
    assert cart.lines[0].quantity == 2


# 2. Stock check ignored what was already in the cart

def test_stock_check_includes_quantity_already_in_cart(cart):
    # USB-01 stock is 50: 30 + 21 exceeds it even though 21 alone does not.
    assert cart.add_item('USB-01', 30)
    assert cart.add_item('USB-01', 21) is False
    assert len(cart.lines) == 1
    assert cart.lines[0].quantity == 30


# 3. Loading added items again to the existing cart

def test_repeated_load_does_not_duplicate_items(repo, cart):
    cart.add_item('USB-01', 2)
    cart.save()

    restored = ShoppingCart('alice', repo)
    restored.load()
    restored.load()
    assert len(restored.lines) == 1
    assert restored.lines[0].quantity == 2


# 4. Discount not updated when the cart changes

def test_discount_follows_cart_edits(cart):
    cart.add_item('MOU-01', 2)  # 59.90
    cart.apply_discount('WELCOME10')
    cart.remove_item('MOU-01', 1)  # 29.95 * 0.9
    assert cart.total() == Decimal('26.96')


# 5. Discount code carried over to the next order

def test_discount_code_cleared_after_checkout(repo, cart):
    cart.add_item('USB-01', 1)
    cart.apply_discount('WELCOME10')
    CheckoutService(repo, FakePaymentGateway()).checkout(cart, 'tok', 'req-1')
    assert cart.discount_code is None


# 6. Floating-point money

def test_money_is_exact_and_rounds_half_up(cart):
    cart.add_item('USB-01', 3)
    assert cart.subtotal() == Decimal('29.97')
    cart.remove_item('USB-01')
    cart.add_item('MOU-01', 1)  # 29.95 * 0.9 = 26.955
    cart.apply_discount('WELCOME10')
    assert cart.total() == Decimal('26.96')


# 7. Same request_id could be charged more than once

def test_repeated_request_charged_once_even_after_decline(repo, cart):
    cart.add_item('USB-01', 1)
    declined = CheckoutService(repo, FakePaymentGateway(should_approve=False)).checkout(cart, 'tok', 'req-1')
    assert declined.status == 'declined'

    gateway = FakePaymentGateway()
    service = CheckoutService(repo, gateway)
    paid = service.checkout(cart, 'tok', 'req-1')
    cart.add_item('USB-01', 1)  # client retries the same request
    retry = service.checkout(cart, 'tok', 'req-1')

    assert paid.status == 'paid'
    assert retry.status == 'duplicate'
    assert retry.order_id == paid.order_id
    assert len(gateway.calls) == 1


# 8. Payment token printed

def test_payment_token_not_printed(repo, cart, capsys):
    cart.add_item('USB-01', 1)
    CheckoutService(repo, FakePaymentGateway()).checkout(cart, 'SECRET-TOKEN', 'req-1')
    assert 'SECRET-TOKEN' not in capsys.readouterr().out


# 9. request_id only checked (and never enforced) on large orders

def test_missing_request_id_rejected_without_charging(repo, cart):
    gateway = FakePaymentGateway()
    cart.add_item('USB-01', 1)
    result = CheckoutService(repo, gateway).checkout(cart, 'tok', None)
    assert result.status == 'invalid'
    assert gateway.calls == []


# 10. SQL injection in get_product and get_saved_cart

def test_sql_injection_is_treated_as_data(repo, cart):
    injection = "x' OR '1'='1"
    assert repo.get_product(injection) is None

    cart.add_item('USB-01', 2)
    cart.save()
    attacker = ShoppingCart(injection, repo)
    attacker.load()
    assert attacker.lines == []


# 11. list_orders ignored user_id

def test_list_orders_only_returns_that_users_orders(repo):
    repo.save_order('alice', Decimal('10.00'), 'paid', 'req-a')
    repo.save_order('bob', Decimal('20.00'), 'paid', 'req-b')

    orders = repo.list_orders('alice')
    assert [row[1] for row in orders] == ['alice']
