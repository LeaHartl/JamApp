from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, EntryForm, EntrySearchForm, StakeForm
from app.tables import Results, StakeTable
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Entry, Stake
from werkzeug.urls import url_parse
from sqlalchemy import desc, func, case
from datetime import datetime
import pandas as pd



def updateAblCol(stk):
        FEs = [e.FE for e in Entry.query.filter(Entry.stake_id == stk).all()]
        FE_news = [e.FE_new for e in Entry.query.filter(Entry.stake_id == stk).all()]
        ids = [e.id for e in Entry.query.filter(Entry.stake_id == stk).all()]

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
        abl = [e.abl_since_last for e in Entry.query.filter(Entry.stake_id == stk).all()]
        entrydate = [e.date for e in Entry.query.filter(Entry.stake_id == stk).all()]
        ids = [e.id for e in Entry.query.filter(Entry.stake_id == stk).all()]

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
        print(stk)
        abl = [e.abl_since_last for e in Entry.query.filter(Entry.stake_id == stk).all()]
        entrydate = [e.date for e in Entry.query.filter(Entry.stake_id == stk).all()]
        ids = [e.id for e in Entry.query.filter(Entry.stake_id == stk).all()]

        abl_df = pd.DataFrame(
                {'ids': ids,
                 'abl': abl,
                 }, index=entrydate)

        # print(abl_df)
        d_d = Stake.query.filter(Stake.stake_id == stk).first()
        # print('hello', d_d)
        d_date = d_d.drilldate
        # print(d_date)
        e_date = abl_df.index.max()
        # print(e_date)

        # print(entrydate)
        abl_df = abl_df.loc[d_date:e_date]
        abl_df2 = abl_df.iloc[1:,:]
        print(abl_df)
        print(abl_df2)
        # print(abl_df.shift())
        abl_value = abl_df2['abl'].sum()
        print('value: ', abl_value)

        u_stake = db.session.query(Stake).filter(Stake.stake_id == stk).one()
        u_stake.abl_since_drilled = abl_value

        db.session.commit()


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')  # , user=user)


@app.route('/stakes')
def stakes():
    stk = Stake.query.all()
    table = StakeTable(stk)
    table.border = True
    for s in stk:
        sincedrilldate(s.stake_id)
    # print(table.__html__())
    return render_template('stakes.html', table=table)

# @app.route('/stakes_update')
# def stakesreload():
#     stk = Stake.query.all()
#     for s in stk:
#         sincedrilldate(s.stake_id)
#     table = StakeTable(stk)
#     table.border = True
#     return render_template('stakes.html', table=table)

@app.route('/search_entries', methods=['GET', 'POST'])
def search_entries():  
    search = EntrySearchForm(request.form)
    if request.method == 'POST':
        # session['search'] = search
        # print('hello')
        return search_results(search)

    return render_template('search_entries.html', form=search)


@app.route('/new_entries', methods=['GET', 'POST'])
@login_required
def new_entries():
    form = EntryForm()
    if form.validate_on_submit():
        # newide = db.session.query(Entry).order_by(desc('date')).first()
        oldid = db.session.query(Entry).order_by(desc('id')).first()
        newid = oldid.id+1

        entry = Entry(date=form.date.data, stake_id=form.stake_id.data,
                      FE=form.FE.data, FE_new=form.FE_new.data,
                      comment=form.comment.data, who=current_user.username,
                      id=newid)
                      # abl_since_last=oldvalue.FE_new-newvalue)
                      # abl_since_oct=qr.mySum)

        db.session.add(entry)
        db.session.commit()

        updateAblCol(form.stake_id.data)
        updateAblSeasonCol(form.stake_id.data)

        flash('Ablesung gespeichert!')
        return redirect(url_for('search_entries'))

    return render_template("entry1.html", title='Home Page', form=form,
                           entries=new_entries)


@app.route('/new_stakes', methods=['GET', 'POST'])
@login_required
def new_stakes():
    form = StakeForm()
    if form.validate_on_submit():
        oldid = db.session.query(Stake).order_by(desc('id')).first()
        newid = oldid.id+1

        stake = Stake(drilldate=form.drilldate.data, stake_id=form.stake_id.data,
                      x=form.x.data, y=form.y.data,
                      comment=form.comment.data, who=current_user.username,
                      id=newid)

        db.session.add(stake)
        db.session.commit()

        # updateAblCol(form.stake_id.data)
        # updateAblSeasonCol(form.stake_id.data)

        flash('Pegel gespeichert!')
        return redirect(url_for('stakes'))

    return render_template("new_stake.html", title='Home Page', form=form)
    # return render_template("search_entries.html", title='Home Page', form=form,
    #                        entries=new_entries)


@app.route('/search_results', methods=['GET', 'POST'])
def search_results(search):
    #form = EntrySearchForm()
    stk = search.data['search']
    print(stk)

    results = Entry.query.filter(Entry.stake_id == stk).all()
    print(results)
    if not results:
        flash('No results found!')
        return redirect('/')
    else:
        # display results
        # sort = request.args.get('sort', 'id')
        # reverse = (request.args.get('direction', 'asc') == 'desc')
        # table = Results(results)
        table = Results(results)
                        # sort_by=sort,
                        # sort_reverse=reverse)
                        # search=search)
        table.border = True
        return render_template('search_entries.html', table=table, form=search)


@app.route('/entry/<int:id>', methods=['GET', 'POST'])
def editEntry(id):
    qry = Entry.query.filter(Entry.id == id)
    entry = qry.first()
    form = EntryForm(formdata=request.form, obj=entry)

    qry = Entry.query.filter(Entry.id == id)
    entry = qry.first()
    stk = entry.stake_id
    search = EntrySearchForm(request.form)

    if form.validate_on_submit():
        # save edits
        entry = Entry(id=id, date=form.date.data, stake_id=form.stake_id.data,
                      FE=form.FE.data, FE_new=form.FE_new.data,
                      comment=form.comment.data, who=current_user.username,
                      timestamp=entry.timestamp, abl_since_last=entry.abl_since_last)
        db.session.merge(entry)
        db.session.commit()

        updateAblCol(form.stake_id.data)
        updateAblSeasonCol(form.stake_id.data)

        flash('entry updated successfully!')

        results = Entry.query.filter(Entry.stake_id == stk).all()
        table = Results(results)
        table.border = True

        return redirect(url_for('search_entries'))
    return render_template('edit_entry.html', form=form)

@app.route('/stake/<int:id>', methods=['GET', 'POST'])
def editStake(id):
    # return render_template('index.html')#, form=form)
    qry = Stake.query.filter(Stake.id == id)
    stake = qry.first()
    form = StakeForm(formdata=request.form, obj=stake)

    # qry = Entr.query.filter(Entry.id == id)
    # entry = qry.first()
    stk = stake.stake_id
    print(stk)
    # search = EntrySearchForm(request.form)

    if form.validate_on_submit():
        # save edits
        stake = Stake(id=id, drilldate=form.drilldate.data, stake_id=form.stake_id.data,
                      x=form.x.data, y=form.y.data,
                      comment=form.comment.data, who=current_user.username)
        db.session.merge(stake)
        db.session.commit()

        flash('stake updated successfully!')
        sincedrilldate(stk)

        results = Stake.query.all()
        table = Results(results)
        table.border = True
        return redirect(url_for('stakes'))
    return render_template('new_stake.html', title='Home Page', form=form)


# delete an entry
@app.route('/delentry/<int:id>', methods=['GET', 'POST'])
def deleteEntry(id):
    qry = Entry.query.filter(Entry.id == id)
    entry = qry.first()
    stk = entry.stake_id

    search = EntrySearchForm(request.form)
    # if form.validate_on_submit():

    db.session.delete(entry)
    db.session.commit()

    updateAblCol(stk)
    updateAblSeasonCol(stk)

    flash('entry deleted successfully!')

    results = Entry.query.filter(Entry.stake_id == stk).all()
    table = Results(results)
    table.border = True
    return render_template('search_entries.html', table=table, form=search)


# delete a stake
@app.route('/delstake/<int:id>', methods=['GET', 'POST'])
def deleteStake(id):
    qry = Stake.query.filter(Stake.id == id)
    stake = qry.first()
    stk = stake.stake_id
    db.session.delete(stake)
    db.session.commit()

    flash('stake deleted successfully!')
    results = Stake.query.all()
    table = StakeTable(results)
    table.border = True
    return redirect(url_for('stakes'))
    return render_template('new_stake.html', title='Home Page', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
        # return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)