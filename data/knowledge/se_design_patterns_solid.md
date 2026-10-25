topic: software_engineering

# Software Engineering: SOLID Principles and Design Patterns

Object-oriented system design relies on foundational architectural principles to ensure long-term maintainability, testability, and decoupled module dependencies.

## 1. The SOLID Principles
- **Single Responsibility (SRP):** A class should have only one reason to change, encapsulating a cohesive unit of functionality.
- **Open/Closed (OCP):** Software entities should be open for extension but closed for modification. Implement behavior variants via interfaces rather than editing core logic.
- **Liskov Substitution (LSP):** Subtypes must be substitutable for their base types without altering system correctness.
- **Interface Segregation (ISP):** Clients should not be forced to depend on methods they do not use; prefer fine-grained interfaces.
- **Dependency Inversion (DIP):** High-level business modules should depend on abstractions rather than low-level concrete implementations.

## 2. Common Creational and Structural Patterns
- **Factory Pattern:** Encapsulates object instantiation, allowing subclasses to dictate the concrete class instantiated.
- **Strategy Pattern:** Defines a family of interchangeable algorithms behind a shared interface, selecting execution strategy dynamically at runtime.

```python
# Strategy Pattern in Python
from abc import ABC, abstractmethod

class PricingStrategy(ABC):
    @abstractmethod
    def calculate(self, base_price: float) -> float:
        pass

class RegularPricing(PricingStrategy):
    def calculate(self, base_price: float) -> float:
        return base_price

class PremiumPricing(PricingStrategy):
    def calculate(self, base_price: float) -> float:
        return round(base_price * 0.85, 2)

class OrderCheckout:
    def __init__(self, strategy: PricingStrategy):
        self.strategy = strategy

    def compute_total(self, amount: float) -> float:
        return self.strategy.calculate(amount)
```

By decoupling execution strategies from calling controllers, software components adhere to the Open/Closed principle and can be independently unit tested with mocked dependencies.
