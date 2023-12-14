from sqlalchemy import String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Handphone(Base):
    __tablename__ = "pemilihan_hp"
    id: Mapped[int] = mapped_column(primary_key=True)
    kamera: Mapped[int] = mapped_column()
    ram: Mapped[int] = mapped_column()
    baterai: Mapped[int] = mapped_column()
    harga: Mapped[int] = mapped_column()
    ukuranlayar: Mapped[int] = mapped_column()  
    
    def __repr__(self) -> str:
        return f"Handphone(id={self.id!r}, kamera={self.kamera!r}, ram={self.ram!r}, baterai={self.baterai!r}, harga={self.harga!r}, ukuranlayar={self.ukuranlayar!r})"
    