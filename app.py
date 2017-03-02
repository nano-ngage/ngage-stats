from flask import Flask
import psycopg2
import sys
import json
import os
#104.131.147.199
conn = psycopg2.connect("dbname='" + os.environ['DBDB'] + "' user='postgres' host='" + os.environ['DBIP'] + "' password='" + os.environ['DBPW'] + "'")
#conn = psycopg2.connect("dbname='ngagepg' user='postgres' host='104.131.147.199' password='jordansucks'")
cur = conn.cursor()
print "\nShow me the databases:\n"

app = Flask(__name__)

@app.route('/')
def welcome():
  return 'Hello World!'

@app.route('/userStats/<id>')
def userStats(id):
  cur.execute("""SELECT * from "user" where "userID" = %s""",(id))
  name = cur.fetchone()[2]
  cur.execute("""SELECT distinct "sessionID" from "response" where "userID" = %s""",(id))
  session = cur.fetchone()[0]
  cur.execute("""SELECT distinct "answerID" from "response" where "userID" = %s""",(id))
  answer = cur.fetchone()[0]
  if (session != None):
    return 'User ' + name + ' participated in ' + str(session) + ' sessions and answered ' + str(answer) + ' questions.'
  else:
    return 'Nothing found'

@app.route('/userSessionStats/<id>')
def userSessionStats(id):
  cur.execute("""SELECT 
                s."sessionID",
                count(DISTINCT p."userID") participants, 
                count(DISTINCT q."questionID") questions,
                count(DISTINCT r."responseID") responses 
                from "session" s 
                left outer join "question" q on s."presentationID" = q."presentationID"
                left outer join "participant" p on s."sessionID" = p."sessionID" 
                left outer join "response" r on s."sessionID" = r."sessionID" 
                where s."sessionID" IN (SELECT distinct s."sessionID" FROM "session" s INNER JOIN "presentation" p ON s."presentationID" = p."presentationID" WHERE p."userID" = %s)
                group by s."sessionID"
                """,(id))
  columns = ('sessionID', 'participants', 'questions', 'responses')
  results = []
  for row in cur.fetchall():
     results.append(dict(zip(columns, row)))
  return json.dumps(results, indent=2)

@app.route('/sessionStats/<id>')
def sessionStats(id):
    cur.execute("""SELECT count(q."questionID") from "question" q inner join "session" s on s."presentationID" = q."presentationID" and s."sessionID" = %s""",(id))
    questionCount = cur.fetchone()[0]
    cur.execute("""SELECT count(p."userID") from "participant" p inner join "session" s on s."sessionID" = p."sessionID" and s."sessionID" = %s""",(id))
    participantCount = cur.fetchone()[0]
    cur.execute("""SELECT count(p."userID") from "participant" p inner join "session" s on s."sessionID" = p."sessionID" and s."sessionID" = %s""",(id))
    responseCount = cur.fetchone()[0]   
if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=4555)

