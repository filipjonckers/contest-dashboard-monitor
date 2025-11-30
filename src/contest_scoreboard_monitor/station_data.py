import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class StationData:
    auth: str = ''
    ctassis: int = 0
    ctband: int = 0
    ctmode: int = 0
    ctopera: int = 0
    ctoverl: int = 0
    ctpwr: int = 0
    ctstatn: int = 0
    cttime: int = 0
    cttrans: int = 0
    date: datetime = None
    dxcc: str = ''
    elap: int = 0
    hrs: int = 0
    itu: int = 0
    lat: float = 0.0
    lon: float = 0.0
    m10: int = 0
    m15: int = 0
    m160: int = 0
    m20: int = 0
    m40: int = 0
    m80: int = 0
    mctotal: int = 0
    mptotal: int = 0
    mstotal: int = 0
    mtotal: int = 0
    mztotal: int = 0
    p10: int = 0
    p15: int = 0
    p160: int = 0
    p20: int = 0
    p40: int = 0
    p80: int = 0
    ptotal: int = 0
    q10: int = 0
    q15: int = 0
    q160: int = 0
    q20: int = 0
    q40: int = 0
    q80: int = 0
    qtotal: int = 0
    rownum: int = 0
    score: int = 0
    sign: str = ''
    soft: str = ''
    wac: str = ''
    waz: int = 0
    rate: int = 0

    def __init__(self, dict_data: Dict[str, Any]):
        try:
            if dict_data:
                for key, value in dict_data.items():
                    # correctly handle datetime fields
                    if key == 'date' and isinstance(value, str):
                        value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                    setattr(self, key, value)
        except Exception as e:
            logging.error("Error extracting Station data: %s", e)

    def __str__(self):
        # print values of all attributes
        attrs = vars(self)
        return f"{self.date}:" + ' '.join(f"{key:>6}={value:<7}" for key, value in attrs.items())
