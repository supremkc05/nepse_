from typing import Generic, List, Optional, TypeVar, Literal

from pydantic import BaseModel, field_validator


T = TypeVar("T")


class Pager(BaseModel):
    """Pagination metadata returned by several NepaliPaisa endpoints."""

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


class StockLiveItem(BaseModel):
    stockSymbol: str
    companyName: str
    noOfTransactions: int
    maxPrice: float
    minPrice: float
    openingPrice: float
    closingPrice: float
    amount: float
    previousClosing: float
    differenceRs: float
    percentChange: float
    volume: int
    ltv: float = 0.0
    asOfDate: str
    asOfDateString: Optional[str] = None
    tradeDate: str
    dataType: Optional[str] = None


class MarketSummary(BaseModel):
    totalAmount: float
    totalShares: int
    totalTxns: int


class LiveMarketResult(BaseModel):
    stocks: List[StockLiveItem]
    summary: Optional[MarketSummary] = None


class DividendRecord(BaseModel):
    sn: int
    companyName: str
    stockSymbol: str
    bonus: float = 0.0
    cash: float = 0.0
    totalDividend: float = 0.0
    bookClosureDateAD: Optional[str] = None
    bookClosureDateBS: Optional[str] = None
    fiscalYearAD: Optional[str] = None
    fiscalYearBS: Optional[str] = None
    rightShare: Optional[str] = None
    rightBookCloseDateAD: Optional[str] = None
    rightBookCloseDateBS: Optional[str] = None

    @field_validator("bonus", "cash", "totalDividend", mode="before")
    @classmethod
    def parse_str_float(cls, value: object) -> float:
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return 0.0

        if value is None:
            return 0.0

        return float(value)


class PriceHistoryRecord(BaseModel):
    sn: int
    tradeDate: str
    tradeDateString: Optional[str] = None
    maxPrice: float
    minPrice: float
    closingPrice: float
    noOfTransactions: int
    volume: int
    amount: float
    previousClosing: float
    differenceRs: float
    percentChange: float


IndicatorType = Literal["gainers", "turnover", "sharestraded"]


class TopMoverItem(BaseModel):
    stockSymbol: str
    companyName: str
    noOfTransactions: int
    maxPrice: float
    minPrice: float
    openingPrice: float
    closingPrice: float
    amount: float
    previousClosing: float
    differenceRs: float
    percentChange: float
    volume: int
    ltv: float = 0.0
    asOfDate: str
    asOfDateString: Optional[str] = None
    tradeDate: str
    dataType: Optional[str] = None


class PaginatedData(BaseModel, Generic[T]):
    """Wraps a page of data with pagination metadata."""

    data: List[T]
    pager: Pager
