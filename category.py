from dataclasses import dataclass


@dataclass
class Category:
    catid: int = -1
    testid: int = -1
    ctwac: int = -1
    ctoper: int = -1
    cttrans: int = -1
    ctband: int = -1
    ctpwr: int = -1
    ctmode: int = -1
    ctassis: int = -1
    ctstatn: int = -1
    cttime: int = -1
    ctoverl: int = -1
    categoryname: str = None
    wherescores: str = None
    ct_oper: str = None
    ct_band: str = None
    ct_mode: str = None
    ct_assis: str = None
    ct_trans: str = None
    ct_power: str = None
    ct_statn: str = None
    ct_overl: str = None
    ct_time: str = None

    def __str__(self):
        return f"{self.categoryname} (ID: {self.catid}, contest id: {self.testid})"
