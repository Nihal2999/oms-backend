class UserAlreadyExistsException(Exception):
    pass

class InvalidCredentialsException(Exception):
    pass

class UserNotFoundException(Exception):
    pass

class OrderNotFoundException(Exception):
    pass

class ProductNotFoundException(Exception):
    pass

class InsufficientStockException(Exception):
    pass

class OrderAlreadyCancelledException(Exception):
    pass

class InvalidOrderStatusTransitionException(Exception):
    pass
class ProductNotDeletedException(Exception):
    pass

class UnauthorizedException(Exception):
    pass