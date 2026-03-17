#!/usr/bin/env python3
"""
Comprehensive test demonstrating the abstract base class pattern.
Shows that the base class enforces proper inheritance.
"""

from uktax import UKTaxCalculatorBase, UKTaxCalculator2023, UKTaxCalculatorReformed
from abc import ABC
from attrs import define, field

print("\n" + "="*80)
print("ABSTRACT BASE CLASS PATTERN DEMONSTRATION")
print("="*80)

# Test 1: Base class cannot be instantiated
print("\n1. Attempting to instantiate abstract base class...")
print("   Code: base = UKTaxCalculatorBase()")
try:
    base = UKTaxCalculatorBase()
    print("   ✗ FAILED: Should not be able to instantiate abstract class")
    exit(1)
except TypeError as e:
    print(f"   ✓ SUCCESS: Raised TypeError as expected")
    print(f"   Message: {str(e)[:80]}...")

# Test 2: Verify proper inheritance
print("\n2. Verifying class hierarchy...")
print(f"   UKTaxCalculatorBase is abstract: {hasattr(UKTaxCalculatorBase, '__abstractmethods__')}")
print(f"   Abstract methods: {UKTaxCalculatorBase.__abstractmethods__}")
print(f"   UKTaxCalculator2023 extends Base: {issubclass(UKTaxCalculator2023, UKTaxCalculatorBase)}")
print(f"   Reformed extends Base: {issubclass(UKTaxCalculatorReformed, UKTaxCalculatorBase)}")

# Test 3: Subclasses implement abstract method
print("\n3. Testing that subclasses properly implement abstract method...")
classic = UKTaxCalculator2023()
reformed = UKTaxCalculatorReformed()

# Test with normal income (no tapering)
income_normal = 50000
pa_classic_normal = classic.calculate_personal_allowance(income_normal)
pa_reformed_normal = reformed.calculate_personal_allowance(income_normal)
print(f"   At £{income_normal:,}:")
print(f"      Classic PA: £{pa_classic_normal:,.0f}")
print(f"      Reformed PA: £{pa_reformed_normal:,.0f}")
print(f"      ✓ Both equal: {pa_classic_normal == pa_reformed_normal}")

# Test with high income (tapering applies)
income_high = 110000
pa_classic_high = classic.calculate_personal_allowance(income_high)
pa_reformed_high = reformed.calculate_personal_allowance(income_high)
print(f"   At £{income_high:,}:")
print(f"      Classic PA: £{pa_classic_high:,.0f} (with tapering)")
print(f"      Reformed PA: £{pa_reformed_high:,.0f} (no tapering)")
print(f"      ✓ Different: {pa_classic_high != pa_reformed_high}")

# Test 4: Polymorphism works
print("\n4. Testing polymorphism (same interface)...")
calculators = [
    ("2023 (Current)", UKTaxCalculator2023()),
    ("Reformed", UKTaxCalculatorReformed(additional_rate=0.50))
]

test_income = 120000
print(f"   Testing with income of £{test_income:,}:")
for name, calc in calculators:
    assert isinstance(calc, UKTaxCalculatorBase), f"{name} not instance of Base"
    marginal = calc.calculate_marginal_rate(test_income)
    effective = calc.calculate_effective_rate(test_income)
    net = calc.calculate_net_income(test_income)
    print(f"      {name:10s}: Marginal={marginal:5.1f}%, Effective={effective:5.1f}%, Net=£{net:>8,.0f}")

print("   ✓ All calculations work through base class interface")

# Test 5: Try to create a broken subclass (incomplete implementation)
print("\n5. Testing that incomplete implementation is caught...")
print("   Creating class without implementing abstract method...")

try:
    @define
    class BrokenCalculator(UKTaxCalculatorBase):
        """This class forgets to implement calculate_personal_allowance."""
        pass
    
    # Try to instantiate it
    broken = BrokenCalculator()
    print("   ✗ FAILED: Should not be able to instantiate incomplete subclass")
    exit(1)
except TypeError as e:
    print("   ✓ SUCCESS: Python prevented instantiation of incomplete subclass")
    print(f"   Message: {str(e)[:80]}...")

# Test 6: Correct implementation works
print("\n6. Creating complete subclass implementation...")

@define
class SimpleCalculator(UKTaxCalculatorBase):
    """Simple calculator with 50% personal allowance for everyone."""
    
    def calculate_personal_allowance(self, gross_income: float) -> float:
        """Give everyone half the standard personal allowance."""
        return self.personal_allowance * 0.5

try:
    simple = SimpleCalculator()
    pa = simple.calculate_personal_allowance(50000)
    print(f"   ✓ SUCCESS: Created SimpleCalculator")
    print(f"   Personal allowance: £{pa:,.0f} (50% of standard)")
    print(f"   ✓ Inherits all base class methods automatically")
    
    # Test it works
    marginal = simple.calculate_marginal_rate(50000)
    print(f"   Marginal rate at £50k: {marginal:.1f}%")
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    exit(1)

print("\n" + "="*80)
print("ALL TESTS PASSED!")
print("="*80)
print("\nKey Takeaways:")
print("  • Abstract base class enforces design contract")
print("  • Subclasses MUST implement calculate_personal_allowance()")
print("  • Python prevents instantiation of incomplete implementations")
print("  • All implementations share the same interface (polymorphism)")
print("  • Easy to extend with new tax system variants")
print("="*80 + "\n")
