from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Product(Base):
    __tablename__ = 'product_name'

    product_id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    stripe_product_id = Column(String(100))
    url = Column(String(256), nullable=False)

    def __str__(self):
        return self.name


class Price(Base):
    __tablename__ = 'price'

    price_id = Column(Integer, primary_key=True)
    stripe_price_id = Column(String(100), nullable=True)
    price = Column(Integer)  # cents

    product_id = Column(ForeignKey(Product.product_id))
    product = relationship(Product, remote_side=Product.product_id, foreign_keys=product_id)


    def get_display_price(self):
        return "{0:.2f}".format(self.price / 100)

