# model.py
# qtdsexporter

# Created by M. Nasimul Haque.
# Copyright 2010, M. Nasimul Haque.

# This is a free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import os
import datetime

from sqlalchemy import *
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
    trade = Field(Integer)
    volume = Field(Integer)

    trade_at = Field(DateTime, required=True)

    code = ManyToOne("Code")

    def __repr__(self):
        return "%s - %s" % (self.code.code, self.trade_at)

    @classmethod
    def get_by_day(cls, day):
        day = datetime.datetime(day=day.day, month=day.month, year=day.year)
        day_after = datetime.timedelta(days=1) + day
        return cls.query.filter(between(cls.trade_at, day, day_after))

    @classmethod
    def get_by_code(cls, code, day):
        return cls.get_by_day(day).filter_by(code=code)


class Close(Entity):

    close = Field(Float, required=True)
    day = Field(Date, required=True)

    code = ManyToOne("Code")

    def __repr__(self):
        return "<Close: %.2f %s>" % (self.close, self.day)

