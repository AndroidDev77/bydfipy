"""
Type definitions for the BYDFi API client
"""

from typing import Dict, List, Any, Optional, TypedDict, Union
from typing_extensions import Literal, NotRequired


# API Response Types
class TickerData(TypedDict):
    symbol: str
    priceChange: str
    priceChangePercent: str
    lastPrice: str
    lastQty: str
    open: str
    high: str
    low: str
    volume: str
    quoteVolume: str
    openTime: int
    closeTime: int


class OrderBookItem(TypedDict):
    price: str
    quantity: str


class OrderBookData(TypedDict):
    lastUpdateId: int
    bids: List[OrderBookItem]
    asks: List[OrderBookItem]


class TradeData(TypedDict):
    id: int
    price: str
    qty: str
    time: int
    isBuyerMaker: bool
    isBestMatch: bool


class KlineData(TypedDict):
    openTime: int
    open: str
    high: str
    low: str
    close: str
    volume: str
    closeTime: int
    quoteVolume: str
    trades: int
    takerBuyBaseVolume: str
    takerBuyQuoteVolume: str


# Account & Order Types
class BalanceData(TypedDict):
    asset: str
    free: str
    locked: str


class AccountData(TypedDict):
    makerCommission: int
    takerCommission: int
    buyerCommission: int
    sellerCommission: int
    canTrade: bool
    canWithdraw: bool
    canDeposit: bool
    updateTime: int
    balances: List[BalanceData]


OrderSide = Literal["BUY", "SELL"]
OrderType = Literal[
    "LIMIT", "MARKET", "STOP_LOSS", "STOP_LOSS_LIMIT", "TAKE_PROFIT", "TAKE_PROFIT_LIMIT"
]
OrderStatus = Literal[
    "NEW", "PARTIALLY_FILLED", "FILLED", "CANCELED", "PENDING_CANCEL", "REJECTED", "EXPIRED"
]
TimeInForce = Literal["GTC", "IOC", "FOK"]


class OrderData(TypedDict):
    symbol: str
    orderId: int
    clientOrderId: str
    transactTime: int
    price: str
    origQty: str
    executedQty: str
    status: OrderStatus
    timeInForce: TimeInForce
    type: OrderType
    side: OrderSide
    stopPrice: NotRequired[str]
    icebergQty: NotRequired[str]
    origQuoteOrderQty: NotRequired[str]
    updateTime: int
    isWorking: bool


class OrderListParams(TypedDict):
    symbol: str
    orderId: NotRequired[int]
    startTime: NotRequired[int]
    endTime: NotRequired[int]
    limit: NotRequired[int]


class CreateOrderParams(TypedDict):
    symbol: str
    side: OrderSide
    type: OrderType
    timeInForce: NotRequired[TimeInForce]
    quantity: NotRequired[Union[str, float]]
    quoteOrderQty: NotRequired[Union[str, float]]
    price: NotRequired[Union[str, float]]
    newClientOrderId: NotRequired[str]
    stopPrice: NotRequired[Union[str, float]]
    icebergQty: NotRequired[Union[str, float]]
    recvWindow: NotRequired[int]


# WebSocket Types
WSMessageType = Literal[
    "ticker", "ticker.24h", "orderbook", "trades", "klines", "account", "order"
]


class WSMessage(TypedDict):
    type: WSMessageType
    stream: str
    data: Dict[str, Any]
    time: int