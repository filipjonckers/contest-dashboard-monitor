from dataclasses import dataclass


@dataclass
class Category:
    catid: int
    testid: int
    ctwac: int
    ctoper: int
    cttrans: int
    ctband: int
    ctpwr: int
    ctmode: int
    ctassis: int
    ctstatn: int
    cttime: int
    ctoverl: int
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
