from app.services.dividend_service import get_dividend_info, format_dividend_message


def test_get_dividend_info_accepts_optional_shares():
    data = get_dividend_info("ITC", shares=100)

    assert data is not None
    assert data["symbol"] == "ITC"
    assert data["shares"] == 100
    assert data["yearly"] == 1500.0
    assert data["monthly"] == 125.0


def test_format_dividend_message_works_with_service_result():
    data = get_dividend_info("ITC", shares=100)
    message = format_dividend_message(data)

    assert "ITC Dividend" in message
    assert "Shares: 100" in message
    assert "Yearly: ₹1,500.00" in message
    assert "Monthly: ₹125.00" in message
