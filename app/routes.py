from flask import render_template, flash, redirect, url_for, request, Response
from app import app, db
from app.forms import LoginForm, RegistrationForm, EntryForm, EntrySearchForm, StakeForm
from app.tables import Results, StakeTable
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Entry, Stake
from werkzeug.urls import url_parse
from sqlalchemy import desc, func, case, and_
import pandas as pd
from datetime import datetime

from bokeh.embed import components
from bokeh.resources import INLINE

import app.bokeh_embed as be
import app.helpers as hlp


@app.route('/plot1', methods=['GET'])
def plot1():
    script, div = components(be.pointplot())

    return render_template(
        'embed.html',
        plot_script=script,
        plot_div=div,
        js_resources=INLINE.render_js(),
        css_resources=INLINE.render_css(),
        ).encode(encoding='UTF-8')


@app.route('/plot2', methods=['GET'])
def plot2():
    script, div = components(be.pointplotbyyear())

    return render_template(
        'embed.html',
        plot_script=script,
        plot_div=div,
        js_resources=INLINE.render_js(),
        css_resources=INLINE.render_css(),
        ).encode(encoding='UTF-8')


@app.route('/')
@app.route('/index')
def index():
    
    script, div = components(be.mapplot())

    return render_template(
        'index.html',
        plot_script=script,
        plot_div=div,
        js_resources=INLINE.render_js(),
        css_resources=INLINE.render_css(),
        ).encode(encoding='UTF-8')
    return render_template('index.html', title='Home')  


@app.route('/ablationmap')
def ablationmap():
    #hlp.avgabl()
    tabs, df = be.mapplot2()
    script, div = components(tabs)
    # print('hello', df)
    df = df[['stake_id', 'abl_since_oct_2019', 'abl_since_oct_2020', 'abl_since_oct_2021',
             'lastentry_2019', 'lastentry_2020', 'lastentry_2021', 'x', 'y', 'xc', 'yc']]
    df.rename(columns={'abl_since_oct_2019': 'ablation2019', 'abl_since_oct_2020': 'ablation2019',
                       'abl_since_oct_2021': 'ablation2021'}, inplace=True)
    return render_template(
        'ablationmap.html',
        plot_script=script,
        plot_div=div,
        js_resources=INLINE.render_js(),
        css_resources=INLINE.render_css(),
        outputdata=df.to_csv(index=False)
        ).encode(encoding='UTF-8')



@app.route('/getcsvablation')
def getcsvablation():
    output = request.args.get('pass', None)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=ablation.csv"})
    return redirect('/')


@app.route('/lastentries')
def lastentries():
    now = datetime.now()

    latest = db.session.query(Entry, func.max(Entry.date)).\
        group_by(Entry.stake_id).order_by(Entry.date)

    output = [item[0] for item in latest]
    outputdf = pd.DataFrame(columns=['stake_id', 'date', 'FE'])

    outputdf['stake_id'] = [out.stake_id for out in output]
    # outputdf['drilldate'] = [out.drilldate for out in output]
    # outputdf['abl_since_drilled'] = [out.abl_since_drilled for out in output]
    outputdf['FE'] = [out.FE_new for out in output]
    outputdf['date'] = [out.date for out in output]
    outputdf['comment'] = [out.comment for out in output]

    if not latest:
        flash('No results found!')
        return redirect('/')
    else:
        table = Results(output)
        table.border = True
        #print(outputdf.to_markdown())

        # forPrint = outputdf.to_()
        print(outputdf.to_markdown())
        return render_template('lastentries.html', table=table,
            output=outputdf.to_csv(index=False))#, output2=outputdf.to_markdown())


@app.route('/getcsv')
def getcsv():
    output = request.args.get('pass', None)
    # print('hello', output)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=download.csv"})
    return redirect('/')



@app.route('/stakes')
def stakes():
    stk = Stake.query.all()
    table = StakeTable(stk)
    table.border = True
    for s in stk:
        hlp.sincedrilldate(s.stake_id)

    output = [item for item in stk]
    outputdf = pd.DataFrame(columns=['stake_id', 'Lon', 'Lat'])
    outputdf['stake_id'] = [out.stake_id for out in output]
    outputdf['Bohrdatum'] = [out.drilldate for out in output]
    outputdf['Abl. seit Bohrdatum'] = [out.abl_since_drilled for out in output]
    outputdf['Kommentar'] = [out.comment for out in output]
    outputdf['Lon'] = [out.x for out in output]
    outputdf['Lat'] = [out.y for out in output]
    # print(outputdf)

    return render_template('stakes.html', table=table, output=outputdf.to_csv(index=False))


@app.route('/search_entries', methods=['GET', 'POST'])
def search_entries():
    search = EntrySearchForm(request.form)
    if request.method == 'POST':
        print('yes')

        return search_results(search)
    print(search)

    return render_template('search_entries.html', form=search)


@app.route('/getcsvstakes')
def getcsvstakes():
    stk = request.args.get('stk', None)
    data = Entry.query.filter(Entry.stake_id == stk).all()
    outputdf = pd.DataFrame([(d.stake_id, d.date, d.FE, d.FE_new, d.comment,
                              d.abl_since_last, d.abl_since_oct) for d in data],
                            columns=['stake_id', 'date', 'FE', 'FE neu', 'Kommentar',
                            'Ablation seit letzter Messung', 'Abl. seit Herbst'])
    outputdf.sort_values(by=['date'], inplace=True)
    return Response(
        outputdf.to_csv(),
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=Pegelblatt_P"+stk+".csv"})
    return redirect('/')


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

        hlp.updateAblCol(form.stake_id.data)
        hlp.updateAblSeasonCol(form.stake_id.data)

        flash('Ablesung gespeichert!')
        return redirect(url_for('search_entries'))

    return render_template("entry1.html", title='Home Page', form=form,
                           entries=new_entries)


@app.route('/new_stakes', methods=['GET', 'POST'])
@login_required
## FIND WAY TO CHECK FOR DUPLICATE STAKE NAME ENTRIES!
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
    # print(stk)

    results = Entry.query.filter(Entry.stake_id == stk).order_by(Entry.date).all()
    # print(results)
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
        return render_template('search_entries.html', table=table, form=search, stk=stk)


@app.route('/entry/<int:id>', methods=['GET', 'POST'])
@login_required
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

        hlp.updateAblCol(form.stake_id.data)
        hlp.updateAblSeasonCol(form.stake_id.data)

        flash('entry updated successfully!')

        results = Entry.query.filter(Entry.stake_id == stk).all()
        table = Results(results)
        table.border = True

        return redirect(url_for('search_entries'))
    return render_template('edit_entry.html', form=form)


@app.route('/stake/<int:id>', methods=['GET', 'POST'])
@login_required
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
        hlp.sincedrilldate(stk)

        results = Stake.query.all()
        table = Results(results)
        table.border = True
        return redirect(url_for('stakes'))
    return render_template('new_stake.html', title='Home Page', form=form)


# delete an entry
@app.route('/delentry/<int:id>', methods=['GET', 'POST'])
@login_required
def deleteEntry(id):
    qry = Entry.query.filter(Entry.id == id)
    entry = qry.first()
    stk = entry.stake_id

    search = EntrySearchForm(request.form)
    # if form.validate_on_submit():

    db.session.delete(entry)
    db.session.commit()

    hlp.updateAblCol(stk)
    hlp.updateAblSeasonCol(stk)

    flash('entry deleted successfully!')

    results = Entry.query.filter(Entry.stake_id == stk).all()
    table = Results(results)
    table.border = True
    return redirect(url_for('search_entries'))
    # return render_template('search_entries.html', table=table, form=search)


# delete a stake
@app.route('/delstake/<int:id>', methods=['GET', 'POST'])
@login_required
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


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)