"""Domain adapter registry for Holocron.

This module provides a central registry for skill domain adapters,
allowing domains to be registered and retrieved by ID.

Example:
    ```python
    from holocron.domains.registry import DomainRegistry
    from holocron.domains.base import DomainAdapter

    @DomainRegistry.register("my-domain")
    class MyDomainAdapter(DomainAdapter):
        ...

    # Later, retrieve the adapter
    adapter = DomainRegistry.get("my-domain")
    ```
"""

from typing import Type

from holocron.domains.base import DomainAdapter


class DomainRegistry:
    """Central registry for skill domain adapters.

    Provides class-level registration and retrieval of domain adapters.
    Domains register themselves using the @register decorator.
    """

    _adapters: dict[str, Type[DomainAdapter]] = {}
    _instances: dict[str, DomainAdapter] = {}

    @classmethod
    def register(cls, domain_id: str):
        """Decorator to register a domain adapter.

        Args:
            domain_id: Unique identifier for the domain

        Returns:
            Decorator function

        Example:
            ```python
            @DomainRegistry.register("reading-skills")
            class ReadingSkillsAdapter(DomainAdapter):
                ...
            ```
        """

        def decorator(adapter_class: Type[DomainAdapter]) -> Type[DomainAdapter]:
            if domain_id in cls._adapters:
                raise ValueError(f"Domain '{domain_id}' is already registered")
            cls._adapters[domain_id] = adapter_class
            return adapter_class

        return decorator

    @classmethod
    def get(cls, domain_id: str) -> DomainAdapter:
        """Get a domain adapter instance by ID.

        Creates a new instance if one doesn't exist, otherwise
        returns the cached instance.

        Args:
            domain_id: The domain identifier

        Returns:
            DomainAdapter instance

        Raises:
            ValueError: If domain_id is not registered
        """
        if domain_id not in cls._adapters:
            available = ", ".join(cls._adapters.keys()) or "none"
            raise ValueError(
                f"Unknown domain: '{domain_id}'. Available domains: {available}"
            )

        if domain_id not in cls._instances:
            cls._instances[domain_id] = cls._adapters[domain_id]()

        return cls._instances[domain_id]

    @classmethod
    def get_class(cls, domain_id: str) -> Type[DomainAdapter]:
        """Get the domain adapter class (not instance) by ID.

        Args:
            domain_id: The domain identifier

        Returns:
            DomainAdapter class

        Raises:
            ValueError: If domain_id is not registered
        """
        if domain_id not in cls._adapters:
            available = ", ".join(cls._adapters.keys()) or "none"
            raise ValueError(
                f"Unknown domain: '{domain_id}'. Available domains: {available}"
            )

        return cls._adapters[domain_id]

    @classmethod
    def list_domains(cls) -> list[str]:
        """List all registered domain IDs.

        Returns:
            List of domain identifier strings
        """
        return list(cls._adapters.keys())

    @classmethod
    def is_registered(cls, domain_id: str) -> bool:
        """Check if a domain is registered.

        Args:
            domain_id: The domain identifier

        Returns:
            True if domain is registered
        """
        return domain_id in cls._adapters

    @classmethod
    def clear(cls) -> None:
        """Clear all registered domains.

        Primarily useful for testing.
        """
        cls._adapters.clear()
        cls._instances.clear()

    @classmethod
    def clear_instances(cls) -> None:
        """Clear cached instances but keep registrations.

        Useful when you want to reset adapter state.
        """
        cls._instances.clear()

    @classmethod
    def get_all(cls) -> dict[str, DomainAdapter]:
        """Get all registered domain adapters as instances.

        Returns:
            Dictionary mapping domain_id to adapter instance
        """
        return {domain_id: cls.get(domain_id) for domain_id in cls._adapters}
