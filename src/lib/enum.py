from enum import Enum

class TemplateMail(Enum):

    REGISTER = 'src/templates/register.html'
    RECALL_TICKET = 'src/templates/recall_ticket.html'

class VAType(Enum):
    MASTER_MERCHANT = 'MASTER_MERCHANT'
    MERCHANT = 'MERCHANT'
    USER = 'USER'

class VARole(Enum):
    ADMIN = 'admin'
    MASTER_MERCHANT = 'master_merchant'

    @classmethod
    def check_role(cls, value):
        return value in cls._value2member_map_

class APIResponseCode(Enum):
    SUCCESS_CODE = {"code": "00", "detail": "Success"}
    WAIT_PROCESSING = {"code": "01", "detail": "Contact NH"}
    TRANSACTION_UNKNOWN_ERROR = {"code": "05", 
                                 "detail": "Transaction error unknown"}
    OPT_EXPIRED = {"code": "08", "detail": "Authentication failed"}
    REQUIRED_OPT = {"code": "10", "detail": "Required to enter OTP"}
    INVALID_AMOUNT = {"code": "13", "detail": "Invalid amount"}
    INVALID_CARD_NO = {"code": "14", "detail": "Card number does not exist"}
    NO_FOUND_TRANSACTION = {"code": "25",
                            "detail": "No original transaction found to revert"}
    ACCOUNT_EXIST = {"code": "26",
                     "detail": "The linked account already exists"}
    FAIL_FORMAT = {"code": "30", "detail": "Fail format"}
    FORBIDDEN = {"code": "31", "detail": "User account error"}
    ACCOUNT_LOCK = {"code": "36", "detail": "Account of user is locked"}
    ACCOUNT_NO_SUBSCRIBE_SERVICE = {"code": "46", 
                                    "detail": "Account don't subscribe service"}
    AMOUNT_NOT_ENOUGH = {"code": "51", "detail": "Account don't enough amount"}
    FAIL_OPT = {"code": "20", "detail": "OPT fail"}
    TRANSACTION_EXCEEDING_LIMIT = {"code": "61", "detail": "Transaction exceeding limit"}
    ERROR_NOT_IDENTIFIED = {"code": "21", "detail": "Error not identified"}
    TIME_OUT_ERROR = {"code": "68", "detail": "Process time out"}
    FAIL_OPT_THREE_TIMES = {"code": "75", "detail": "OPT is fail 3 times"}
    INTERNAL_SERVER = {"code": "91", "detail": "Internal server error"}
    TRANSACTION_DUPLICATE = {"code": "94", "detail": "Transaction duplicate"}
    NOT_FOUND = {"code": "100", "detail": "Not found"}
    


