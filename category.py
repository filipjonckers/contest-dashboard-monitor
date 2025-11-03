from dataclasses import dataclass


@dataclass
class Category:
    catid: int
    testid: int
    ctoper: int
    cttrans: int
    ctpwr: int
    categoryname: str
    wherescores: str

    ct_oper: str = None
    ct_trans: str = None
    ct_power: str = None

    def __str__(self):
        return f"{self.categoryname} (ID: {self.catid}, contest id: {self.testid})"
