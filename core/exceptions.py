"""============================================================
CORE - DOMAIN EXCEPTIONS
Framework mapping: service layer raises these; views/API convert them into user-readable responses.
============================================================"""
class MarketPulseError(Exception): pass
class MatlabUnavailable(MarketPulseError): pass
