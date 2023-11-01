

def va_info(va_account:str) -> dict:
    return {
        "bank": va_account[4:7],
        "master_merchant_code": va_account[7:10],
        "industry_code": va_account[10:12] if len(va_account) > 10 else None,
        "merchant_code": va_account[12:16] if len(va_account) > 12 else None,
        "user_code": va_account[16:] if len(va_account) > 16 else None
    }