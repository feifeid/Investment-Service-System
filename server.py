#!/usr/bin/env python2.7

"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@104.196.18.7/w4111
#
# For example, if you had username biliris and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://biliris:foobar@104.196.18.7/w4111"
#
#DATABASEURI = "postgresql://user:password@104.196.18.7/w4111"
DATABASEURI = "postgresql://fd2400:2038@35.185.80.252/w4111"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/',methods=['GET', 'POST'])
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args


  
  
  #set default value
  entityList=["Company","People","Investment","Acquisition","Group"] 
  columnList=["Name","Status","Homepage Url", "City","Founded Data", "First Funding Date", "Last Funding Date", "Number of Organization Investors"]
  selectedEntity = request.form.get('entity_select')

  filterATitle="Status"
  filterAList=["All","operating","ipo","acquired","unknown"]   
  filterBTitle="Location"
  filterBList=["All","Europe","Asia","North America"]  
  sortAList=["Default","Number of Organization Investors", "Founded Date", "First Funding Date", "Last Funding Date"]
  sortBList=["ASC","DESC"]
  selectedFilterA="All"  
  selectedFilterB="All" 
  selectedSortA="Default"
  order=["ASC","DESC"]
  selectedSortB= order[0]
  selectedSortB = request.form.get('sortB_select')
  if selectedSortB is None:
      selectedSortB= order[0]
  queryString="SELECT O.name, C.status, O.homepage_url,L.city, C.founded_at,C.first_funding_at, C.last_funding_at,Count(DISTINCT R_O.investor_org_id) As Num_Investors FROM Organization O, Location L,Company C LEFT OUTER JOIN Round_Org R_O ON R_O.company_id=C.crunchbase_uuid WHERE O.location_id=L.id AND O.crunchbase_uuid=C.crunchbase_uuid  Group By C.crunchbase_uuid, O.name, C.status, O.homepage_url,L.city, C.founded_at,C.first_funding_at, C.last_funding_at"

  #if the table is company, then change the filter/sort accordingly
  if selectedEntity=="Company":  
      queryString="SELECT O.name, C.status, O.homepage_url,L.city, C.founded_at,C.first_funding_at, C.last_funding_at,Count(DISTINCT R_O.investor_org_id) As Num_Investors FROM Organization O, Location L,Company C LEFT OUTER JOIN Round_Org R_O ON R_O.company_id=C.crunchbase_uuid WHERE O.location_id=L.id AND O.crunchbase_uuid=C.crunchbase_uuid"      
      columnList=["Name","Status","Homepage Url", "City","Founded Data", "First Funding Date", "Last Funding Date", "Number of Organization Investors"]
      filterATitle="Status"
      filterAList=["All","operating","ipo","acquired","unknown"]   
      filterBTitle="Location"
      filterBList=["All","Europe","Asia","North America"]  
      sortAList=["Default","Number of Organization Investors", "Founded Date", "First Funding Date", "Last Funding Date"]      
      selectedFilterA = request.form.get('filterA_select')
      selectedFilterB = request.form.get('filterB_select')
      selectedSortA = request.form.get('sortA_select')      
      if selectedFilterA=="operating" or selectedFilterA=="ipo" or selectedFilterA=="acquired" or selectedFilterA=="unknown":
          queryString +=" And C.status="+"'"+selectedFilterA+"'"
      if selectedFilterB=="Europe":
          queryString +=" And (L.country_code='AUT' OR L.country_code='CHE' OR L.country_code='DEU' OR L.country_code='FRA' OR L.country_code='GBR' OR L.country_code='RUS')" 
      elif selectedFilterB=="Asia":
          queryString +=" And (L.country_code='CHN' OR L.country_code='HKG' OR L.country_code='KOR')"
      elif selectedFilterB=="North America":
          queryString +=" And L.country_code='USA'"
      queryString +="  Group By C.crunchbase_uuid, O.name, C.status, O.homepage_url,L.city, C.founded_at,C.first_funding_at, C.last_funding_at"
      if selectedSortA=="Number of Organization Investors":
          queryString +=" ORDER BY "+"Num_Investors"+" "+selectedSortB
      elif selectedSortA=="Founded Date":
          queryString +=" ORDER BY "+"C.founded_at"+" "+selectedSortB
      elif selectedSortA=="First Funding Date":
          queryString +=" ORDER BY "+"C.first_funding_at"+" "+selectedSortB
      elif selectedSortA=="Last Funding Date":
          queryString +=" ORDER BY "+"C.last_funding_at"+" "+selectedSortB
      
  #if the table is People, then change the filter/sort accordingly
  elif selectedEntity=="People":  
      queryString="SELECT P.first_name,P.last_name,P.linkedin_url,L.city, O.name, P.title FROM People P,Organization O, Location L WHERE P.location_id=L.id AND P.organization_id=O.crunchbase_uuid"
      columnList=["First Name","Last Name","Linkedin Url", "City","Organization","Title"]   
      filterATitle="Location"
      filterAList=["All","Europe","Asia","North America"]  
      sortAList=["Default","first_name", "last_name"]
      selectedFilterA = request.form.get('filterA_select')
      selectedSortA = request.form.get('sortA_select')

      if selectedFilterA=="Europe":
          queryString +=" And (L.country_code='AUT' OR L.country_code='CHE' OR L.country_code='DEU' OR L.country_code='FRA' OR L.country_code='GBR' OR L.country_code='RUS')" 
      elif selectedFilterA=="Asia":
          queryString +=" And (L.country_code='CHN' OR L.country_code='HKG' OR L.country_code='KOR')"
      elif selectedFilterA=="North America":
          queryString +=" And L.country_code='USA'"
      if selectedSortA=="first_name" or selectedSortA=="last_name":
          queryString +=" ORDER BY "+selectedSortA+" "+selectedSortB

  #if the table is Group, then change the filter/sort accordingly      
  elif selectedEntity=="Group":  
      queryString="SELECT O.name, G.primary_role, O.homepage_url,L.city, O.short_description FROM Organization O, Location L,Group_Org G  WHERE O.location_id=L.id AND O.crunchbase_uuid=G.crunchbase_uuid"
      columnList=["Name","Primary Role","Homepage Url","City","Short Description"]      
      filterATitle="Primary Role"
      filterAList=["All","other","venture","school"]
      sortAList=["Default","name"]
      filterBTitle="Location"
      filterBList=["All","Europe","Asia","North America"]  
      selectedFilterA = request.form.get('filterA_select')
      selectedFilterB = request.form.get('filterB_select')
      selectedSortA = request.form.get('sortA_select')
      if selectedFilterA=="Other" or selectedFilterA=="Venture" or selectedFilterA=="School":
          queryString += " And G.primary_role="+"'"+selectedFilterA+"'"
      if selectedFilterB=="Europe":
          queryString +=" And (L.country_code='AUT' OR L.country_code='CHE' OR L.country_code='DEU' OR L.country_code='FRA' OR L.country_code='GBR' OR L.country_code='RUS')" 
      elif selectedFilterB=="Asia":
          queryString +=" And (L.country_code='CHN' OR L.country_code='HKG' OR L.country_code='KOR')"
      elif selectedFilterB=="North America":
          queryString +=" And L.country_code='USA'"
      if selectedSortA=="name":
          queryString +=" ORDER BY "+selectedSortA+" "+selectedSortB
  
  #if the table is Investment, then change the filter/sort accordingly      
  elif selectedEntity=="Investment": 
      queryStringA="SELECT O1.name,O2.name, R_O.funding_round_type, R_O.funding_round_code,R_O.raised_amount_usd FROM Round_Org R_O, Organization O1,Organization O2 WHERE O1.crunchbase_uuid = R_O.company_id AND O2.crunchbase_uuid = R_O.investor_org_id"
      queryStringB="SELECT O3.name,P.last_name, R_P.funding_round_type, R_P.funding_round_code,R_P.raised_amount_usd FROM Round_Peo R_P, Organization O3,People P WHERE O3.crunchbase_uuid = R_P.company_id AND P.crunchbase_uuid = R_P.investor_peo_id"
      queryString="SELECT O1.name,O2.name, R_O.funding_round_type, R_O.funding_round_code,R_O.raised_amount_usd FROM Round_Org R_O, Organization O1,Organization O2 WHERE O1.crunchbase_uuid = R_O.company_id AND O2.crunchbase_uuid = R_O.investor_org_id UNION SELECT O3.name,P.last_name, R_P.funding_round_type, R_P.funding_round_code,R_P.raised_amount_usd FROM Round_Peo R_P, Organization O3,People P WHERE O3.crunchbase_uuid = R_P.company_id AND P.crunchbase_uuid = R_P.investor_peo_id"
      columnList=["Company Name","Investor Name","Funding Round Type","Founidng Round Code","Raised Amount USD"]  
      filterATitle="Investment Type"
      filterAList=["All","Invested By Individuals", "Invested By Organizations"]      
      filterBTitle="Funding Round Type"
      filterBList=["All","venture","undisclosed","seed","grant","post_ipo_equity"]
      sortAList=["Default","raised_amount_usd","funding_round_code"]
      selectedFilterA = request.form.get('filterA_select')
      selectedFilterB = request.form.get('filterB_select')
      selectedSortA = request.form.get('sortA_select')
      if selectedFilterA=="All":
          queryString=queryStringA+ " UNION "+queryStringB
          if selectedFilterB=="venture" or selectedFilterB=="undisclosed" or selectedFilterB=="seed" or selectedFilterB=="grant" or selectedFilterB=="post_ipo_equity":
              queryString=queryStringA+" And R_O.funding_round_type="+"'"+selectedFilterB+"'" + " UNION "+queryStringB+" And R_P.funding_round_type="+"'"+selectedFilterB+"'"
          if selectedSortA== "raised_amount_usd" or selectedSortA=="funding_round_code":
              queryString +=" ORDER BY "+selectedSortA+" "+selectedSortB
      if selectedFilterA=="Invested By Organizations":
          queryString=queryStringA
          if selectedFilterB=="venture" or selectedFilterB=="undisclosed" or selectedFilterB=="seed" or selectedFilterB=="grant" or selectedFilterB=="post_ipo_equity":
              queryString+=" And R_O.funding_round_type="+"'"+selectedFilterB+"'" 
          if selectedSortA=="raised_amount_usd" or selectedSortA=="funding_round_code":
              queryString +=" ORDER BY "+selectedSortA+" "+selectedSortB
      if selectedFilterA=="Invested By Individuals":
          queryString=queryStringB          
          if selectedFilterB=="venture" or selectedFilterB=="undisclosed" or selectedFilterB=="seed" or selectedFilterB=="grant" or selectedFilterB=="post_ipo_equity":
              queryString+=" And R_P.funding_round_type="+"'"+selectedFilterB+"'" 
          if selectedSortA=="raised_amount_usd" or selectedSortA=="funding_round_code":
              queryString +=" ORDER BY "+selectedSortA+" "+selectedSortB
      
  #if the table is Acquisition, then change the filter/sort accordingly  
  elif selectedEntity=="Acquisition":  
     queryString="SELECT O1.name, O2.name, A.price_amount, A.price_currency_code FROM Acquire A, Organization O1, Organization O2 WHERE O1.crunchbase_uuid=company_id AND O2.crunchbase_uuid=acquirer_id"
     columnList=["Company Name","Acquirer Name","Price Amount","Price Currency Code"]
     filterATitle="Price Currency"
     filterAList=["All","USD","GBP"]
     sortAList=["Default","price_amount"]
     selectedFilterA = request.form.get('filterA_select')
     selectedSortA = request.form.get('sortA_select')
     if selectedFilterA=="USD" or selectedFilterA=="GBP":
         queryString += " And A.price_currency_code="+"'"+selectedFilterA+"'"
     if selectedSortA=="price_amount":
         queryString +=" ORDER BY "+selectedSortA+" "+selectedSortB

  
  #get the result from DB according to query
  state = {'entityChoice': selectedEntity,'filterAChoice': selectedFilterA, 'filterBChoice': selectedFilterB, 'sortAChoice': selectedSortA,'sortBChoice': selectedSortB}
  cursor = g.conn.execute(queryString)
  names = []
  tableInfo=[]
  for result in cursor:
     names.append(result)
     temp=[]
     for value in result:
         if isinstance(value, unicode):
             temp.append(value.encode('ascii','ignore'))
         else:
             temp.append(str(value))
     tableInfo.append(temp)
     print(result)
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  
   
  context = dict(data = names,tableData=tableInfo,entityList=entityList,filterAList=filterAList,filterBList=filterBList,filterATitle=filterATitle,filterBTitle=filterBTitle, sortAList=sortAList,sortBList=sortBList, state=state, order=order, columnList=columnList)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #

  
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
  return render_template("another.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test VALUES (NULL, ?)', name)
  return redirect('/')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
