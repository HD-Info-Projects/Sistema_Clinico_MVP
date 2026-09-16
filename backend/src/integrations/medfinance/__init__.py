"""MedFinance integration contract.

No concrete MedFinance client exists in the current codebase. This package is
kept as the stable import location for the future external adapter.
"""


class MedFinanceIntegrationUnavailable(RuntimeError):
    """Raised when MedFinance is requested before a client is configured."""


__all__ = ["MedFinanceIntegrationUnavailable"]
