from typing import Generic, List, Optional, TypeVar, Literal

from pydantic import BaseModel, Field, field_validator


T = TypeVar("T")


class Pager(BaseModel):
    """Pagination metadata returned by the NEPSE API."""
    pageNo: int
    itemsPerPage: int
    pagePerDisplay: int
    totalNextPages: int


class Company(BaseModel):
    companyId: int
    companyName: str
    stockSymbol: str
    sectorId: int
    sectorName: Optional[str] = None


class BaseMarketItem(BaseModel):
    """Base model for shared market data fields to keep things DRY."""
    stockSymbol: str
    companyName: str
    noOfTransactions: int = Field(description="Total number of trades executed.")
    maxPrice: float = Field(description="Highest traded price of the day.")
    minPrice: float = Field(description="Lowest traded price of the day.")
    openingPrice: float
    closingPrice: float = Field(description="Last Traded Price (LTP) or final close.")
    amount: float = Field(description="Total turnover value in Nepalese Rupees (NPR).")
    previousClosing: float
    differenceRs: float = Field(description="Absolute price change in NPR.")
    percentChange: float = Field(description="Percentage change from previous close.")
    volume: int = Field(description="Total number of shares traded.")
    ltv: float = Field(default=0.0, description="Last Traded Volume.")
    asOfDate: str
    asOfDateString: Optional[str] = None
    tradeDate: str
    dataType: Optional[str] = None


class StockLiveItem(BaseMarketItem):
    """Represents a single stock's live trading data."""
    pass


class TopMoverItem(BaseMarketItem):
    """Represents a top moving stock (gainer, turnover, or volume)."""
    pass


class MarketSummary(BaseModel):
    totalAmount: float = Field(description="Total market turnover in NPR.")
    totalShares: int = Field(description="Total market volume (shares traded).")
    totalTxns: int = Field(description="Total number of transactions across the market.")


class LiveMarketResult(BaseModel):
    stocks: List[StockLiveItem]
    summary: Optional[MarketSummary] = None


class DividendRecord(BaseModel):
    sn: int
    companyName: str
    stockSymbol: str
    bonus: float = Field(default=0.0, description="Bonus share percentage.")
    cash: float = Field(default=0.0, description="Cash dividend percentage.")
    totalDividend: float = Field(default=0.0, description="Total dividend percentage.")
    bookClosureDateAD: Optional[str] = None
    bookClosureDateBS: Optional[str] = None
    fiscalYearAD: Optional[str] = None
    fiscalYearBS: Optional[str] = Field(None, description="Fiscal year in Bikram Sambat (e.g., '2079/80').")
    rightShare: Optional[str] = Field(None, description="Rights share issuance ratio if applicable.")
    rightBookCloseDateAD: Optional[str] = None
    rightBookCloseDateBS: Optional[str] = None

    @field_validator("bonus", "cash", "totalDividend", mode="before")
    @classmethod
    def parse_str_float(cls, value: object) -> float:
        """Safely parse floats, handling dirty API data like commas, hyphens, or 'N/A'."""
        if isinstance(value, str):
            clean_val = value.strip().replace(",", "")
            if clean_val in ("", "-", "N/A", "null"):
                return 0.0
            try:
                return float(clean_val)
            except ValueError:
                return 0.0
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0


class PriceHistoryRecord(BaseModel):
    sn: int
    tradeDate: str
    tradeDateString: Optional[str] = None
    maxPrice: float
    minPrice: float
    closingPrice: float
    noOfTransactions: int
    volume: int
    amount: float = Field(description="Turnover amount in NPR.")
    previousClosing: float
    differenceRs: float
    percentChange: float


IndicatorType = Literal["gainers", "turnover", "sharestraded"]


class PaginatedData(BaseModel, Generic[T]):
    """Wraps a page of data with pagination metadata."""
    data: List[T]
    pager: Pager