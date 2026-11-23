1. Discounts can be infinitely stacked, including a flat -$ leading to negative values payments.
    apply discount when calculating total so nothing drifts when adding/removing/or anything else

2. cart: additem allows addition of negative quantities
    guard 

2. cart: 18 Quantity check, but we don't include existing cart contents, nor does adding things to the cart decrement availability
    check existing earlier, increment existing if it exists, otherwise new line with quanitity

    further we need to check add and remove quantities so we don't have negatives

3. cart: load adds items again to existing cart
    clear lines before we load

4. cart: adding a new item doesn't trigger an already applied discount
    reapply discount on added item

5. checkout: discount_code maintained across carts, not wrong, but unintuitive
    clear it

6. cart: discount are applied with floating-point math, leading to error technically the entire system neglects local context, but I'm not fixing that
    use decimal within the system, converting from and to float when storing, ideally would use integer cents for consistency with db but not editing schema

7. already paid order will be reprocessed if somehow submitted again (by request_id)
    check repository by request_id and guard from payment

8. Payment token is printed
    this should be obfuscated and secure, for this we'll just stop printing it.

9. checkout: I don't know why you'd only check for a requestID on a large order, but I just made it always check for one so that's moot. It also just printed without actually doing anything.

10. repository: sql injection for get_product and get_saved_cart 
    parameterize sku and user_id

11. repository: list_orders doesn't use the user_id
    add it as part of the query

12. two simultaneous checkouts could cause stock issues, ideally we would be reserving stock and only after reserving accepting payment, I'm not adding that.