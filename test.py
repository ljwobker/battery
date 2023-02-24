#!/usr/bin/python3

from decimal import Decimal

a = [Decimal("1.23666"), Decimal("3.45666")]

fmt = '.2f'
new = [','.join(f'{val:{fmt}}' for val in a)]
print(new)

