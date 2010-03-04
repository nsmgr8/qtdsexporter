import os

from elixir import *

dbfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dse.sqlite')

metadata.bind = "sqlite:///" + dbfile
#metadata.bind.echo = True


class Code(Entity):

    code = Field(Unicode(10), unique=True, required=True)

    trades = OneToMany("Trade")

    def __repr__(self):
        return self.code


class Trade(Entity):

    open = Field(Float)
    close = Field(Float)
    high = Field(Float)
    low = Field(Float)
    last = Field(Float)
    trade = Field(Integer)
    volume = Field(Integer)

    trade_at = Field(DateTime, required=True)

    code = ManyToOne("Code")

    def __repr__(self):
        return "%s - %s" % (self.code.code, self.trade_at)


