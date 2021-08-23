from app import app, db
from sqlalchemy import desc, func, case, and_

import matplotlib.pylab as pl
import matplotlib
from datetime import datetime

import pandas as pd
import numpy as np
import geopandas as gpd
from app.models import User, Stake, Entry


def updateAblCol(stk):
    FEs = [e.FE for e in Entry.query.filter(Entry.stake_id == stk).order_by(Entry.date).all()]
    FE_news = [e.FE_new for e in Entry.query.filter(Entry.stake_id == stk).order_by(Entry.date).all()]
    ids = [e.id for e in Entry.query.filter(Entry.stake_id == stk).order_by(Entry.date).all()]

    FE_df = pd.DataFrame(
            {'FE': FEs,
             'FE_new': FE_news,
             }, index=ids)
    FE_df['abl'] = FE_df['FE'] - FE_df['FE_new'].shift(1)
    # print(FE_df)
    dct = FE_df['abl'].to_dict()
    # print(dct)

    db.session.query(Entry).filter(
        Entry.id.in_(dct)).update(
        {Entry.abl_since_last: case(dct, value=Entry.id)},
        synchronize_session=False)

    db.session.commit()


def updateAblSeasonCol(stk):
    abl = [e.abl_since_last for e in Entry.query.filter(Entry.stake_id == stk).order_by(Entry.date).all()]
    entrydate = [e.date for e in Entry.query.filter(Entry.stake_id == stk).order_by(Entry.date).all()]
    ids = [e.id for e in Entry.query.filter(Entry.stake_id == stk).order_by(Entry.date).all()]

    abl_df = pd.DataFrame(
            {'ids': ids,
             'abl': abl,
             }, index=entrydate)

    now = datetime.now()
    yr = now.year

    # print(entrydate)

    df_1 = abl_df.groupby(abl_df.index.year)['abl'].cumsum()

    abl_df['cumsum'] = abl_df['abl'].cumsum()
    abl_df['sumAbl'] = df_1.values
    abl_df['entrydate'] = abl_df.index

    # print('test', abl_df)
    abl_df.set_index('ids', inplace=True)
    # print(abl_df)
    dct = abl_df['sumAbl'].to_dict()

    db.session.query(Entry).filter(
        Entry.id.in_(dct)).update(
        {Entry.abl_since_oct: case(dct, value=Entry.id)},
        synchronize_session=False)

    db.session.commit()


def sincedrilldate(stk):
    abl = [e.abl_since_last for e in Entry.query.filter(Entry.stake_id == stk).order_by(Entry.date).all()]
    entrydate = [e.date for e in Entry.query.filter(Entry.stake_id == stk).order_by(Entry.date).all()]
    ids = [e.id for e in Entry.query.filter(Entry.stake_id == stk).order_by(Entry.date).all()]

    abl_df = pd.DataFrame(
            {'ids': ids,
             'abl': abl,
             }, index=entrydate)

    d_d = Stake.query.filter(Stake.stake_id == stk).first()
    d_date = d_d.drilldate
    e_date = abl_df.index.max()

    abl_df = abl_df.loc[d_date:e_date]
    abl_df2 = abl_df.iloc[1:, :]
    abl_value = abl_df2['abl'].sum()
    # print('value: ', abl_value)

    u_stake = db.session.query(Stake).filter(Stake.stake_id == stk).one()
    u_stake.abl_since_drilled = abl_value

    db.session.commit()



