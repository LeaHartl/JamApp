from flask_table import Table, Col, LinkCol, DatetimeCol
from flask import url_for


class Results(Table):
    id = Col('Id', show=False)
    stake_id = Col('Pegel Name')
    date = DatetimeCol('Datum', datetime_format="YYYY-MM-dd")#, allow_sort=True)
    FE = Col('FE', allow_sort=False)
    FE_new = Col('FE neu', allow_sort=False)
    #abl_oct = Col('Ablation seit Herbst')
    comment = Col('Kommentar', allow_sort=False)
    who = Col('Wer?')
    abl_since_last = Col('Ablation seit letzter Ablesung', allow_sort=False)
    abl_since_oct = Col('Ablation seit Herbst', allow_sort=False)
    # abl_since_o = Col('Ablation seit Herbst', allow_sort=False)
    edit = LinkCol('Edit', 'editEntry', url_kwargs=dict(id='id'), allow_sort=False)
    delete = LinkCol('Delete', 'deleteEntry', url_kwargs=dict(id='id'), allow_sort=False)

    # allow_sort = True

    # def sort_url(self, col_key, reverse=False):
    #     if reverse:
    #         direction = 'desc'
    #     else:
    #         direction = 'asc'
    #     return url_for('search_results', sort=col_key, direction=direction)#


class StakeTable(Table):
    # id = Col('Id', show=True)
    stake_id = Col('Pegelname')
    drilldate = DatetimeCol('Bohratum', datetime_format="YYYY-MM-dd")
    x = Col('Lon', allow_sort=False)
    y = Col('Lat', allow_sort=False)
    abl_since_drilled = Col('Ablation seit Bohrdatum', allow_sort=False)
    comment = Col('Kommentar')
    who = Col('wer?')
    edit = LinkCol('Edit', 'editStake', url_kwargs=dict(id='id'), allow_sort=False)
    delete = LinkCol('Delete', 'deleteStake', url_kwargs=dict(id='id'), allow_sort=False)


