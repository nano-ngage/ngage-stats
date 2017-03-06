from flask import Flask, request
from flask_api import status
from flask_cors import CORS, cross_origin
import psycopg2
import sys
import json
import os
#104.131.147.199
conn = psycopg2.connect("dbname='" + os.environ['DBDB'] + "' user='postgres' host='" + os.environ['DBIP'] + "' password='" + os.environ['DBPW'] + "'")
#conn = psycopg2.connect("dbname='ngagepg' user='postgres' host='104.131.147.199' password='jordansucks'")
cur = conn.cursor()
print "\nStarting Stats Server\n"

app = Flask(__name__)
CORS(app)

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
  try:
    cur.execute("""SELECT 
                  s."sessionID",
                  pr."title",
                  count(DISTINCT p."userID") participants, 
                  count(DISTINCT q."questionID") questions,
                  count(DISTINCT r."responseID") responses,
                  to_char(s."createdAt", 'DD/MM/YYYY')
                  from "session" s 
                  left outer join "question" q on s."presentationID" = q."presentationID"
                  left outer join "participant" p on s."sessionID" = p."sessionID" 
                  left outer join "presentation" pr on pr."presentationID" = s."presentationID"
                  left outer join "response" r on s."sessionID" = r."sessionID" 
                  where s."sessionID" IN (SELECT distinct s."sessionID" FROM "session" s INNER JOIN "presentation" p ON s."presentationID" = p."presentationID" WHERE p."userID" = %s)
                  group by s."sessionID", pr."title", s."createdAt" ORDER BY s."createdAt" """,[id])
    columns = ('sessionID', 'title', 'participants', 'questions', 'responses', 'createdAt')
    results = []
    for row in cur.fetchall():
       results.append(dict(zip(columns, row)))
    return str(json.dumps(results, indent=2))
  except psycopg2.Error as e:
    print e.pgerror
    return 'Server Failure', status.HTTP_400_BAD_REQUEST

@app.route('/groupStats', methods=['GET'])
def groupStats():
  try:
    groupID = request.args.get('groupID')
    presenterID = request.args.get('presenterID')
    cur.execute("""
      SELECT r."userID", u."firstName", u."lastName", count(r."responseID") as responses, count(DISTINCT pa."participantID") as participants
      FROM "response" r
      LEFT OUTER JOIN "participant" pa ON pa."userID" = r."userID" AND pa."sessionID" IN (SELECT s."sessionID" FROM "session" s INNER JOIN "presentation" p ON p."presentationID" = s."presentationID" AND p."userID" = %s)
      LEFT OUTER JOIN "user" u ON u."userID" = r."userID"
      WHERE r."userID" IN (select "userID" from "groupMember" where "groupID" = %s)
      AND r."sessionID" IN (SELECT s."sessionID" FROM "session" s INNER JOIN "presentation" p ON p."presentationID" = s."presentationID" AND p."userID" = %s)
      AND r."userID" > 0
      GROUP BY r."userID", u."firstName", u."lastName" """, [presenterID, groupID, presenterID])
    columns = ('userID', 'firstName', 'lastName', 'responses', 'participants')
    results = []
    for row in cur.fetchall():
       results.append(dict(zip(columns, row)))
    return str(json.dumps(results, indent=2))
  except psycopg2.Error as e:
    print e.pgerror
    return 'Server Failure', status.HTTP_400_BAD_REQUEST

@app.route('/presentationStats/<presentationID>')
def presentationStats(presentationID):
  try:
    cur.execute("""
      SELECT 
          s."sessionID",
          pr."title",
          count(DISTINCT p."userID") participants, 
          count(DISTINCT q."questionID") questions,
          count(DISTINCT r."responseID") responses,
          to_char(s."createdAt", 'DD/MM/YYYY')
          from "session" s 
          left outer join "question" q on s."presentationID" = q."presentationID"
          left outer join "participant" p on s."sessionID" = p."sessionID" 
          left outer join "presentation" pr on pr."presentationID" = s."presentationID"
          left outer join "response" r on s."sessionID" = r."sessionID" 
          where s."presentationID" = %s
          group by s."sessionID", pr."title", s."createdAt" ORDER BY s."createdAt" """, [presentationID])
    columns = ('sessionID', 'title', 'participants', 'questions', 'responses', 'createdAt')
    results = []
    for row in cur.fetchall():
       results.append(dict(zip(columns, row)))
    return str(json.dumps(results, indent=2))
  except psycopg2.Error as e:
    print e.pgerror
    return 'Server Failure', status.HTTP_400_BAD_REQUEST

@app.route('/participationStats/<userID>')
def participationStats(userID):
  try:
    cur.execute("""
        WITH sesh AS (SELECT s."sessionID", pa."userID", (count(DISTINCT r."responseID") * 1.0 / count(DISTINCT q."questionID")) as "percent" FROM "session" s 
        INNER JOIN "question" q ON q."presentationID" = s."presentationID" 
        INNER JOIN "participant" pa ON pa."sessionID" = s."sessionID" 
        INNER JOIN "response" r ON r."sessionID" = s."sessionID" and r."userID" = pa."userID" 
        group by s."sessionID", pa."userID")

        SELECT "allsessions".*, to_char(s."createdAt", 'DD/MM/YYYY'), p."title" FROM (
        SELECT COALESCE(s1."sessionID", s2."sessionID", s3."sessionID", s4."sessionID", s5."sessionID") "sessionID", "1.0", "0.8", "0.6", "0.4", "0.0" FROM 
        (SELECT "sessionID", count("userID") AS "1.0" FROM sesh WHERE "percent" >= 1.0 GROUP BY "sessionID" ORDER BY "sessionID") s1 FULL OUTER JOIN 
        (SELECT "sessionID", count("userID") AS "0.8" FROM sesh WHERE "percent" >= 0.8 GROUP BY "sessionID" ORDER BY "sessionID") s2 ON s1."sessionID" = s2."sessionID" FULL OUTER JOIN 
        (SELECT "sessionID", count("userID") AS "0.6" FROM sesh WHERE "percent" >= 0.6 GROUP BY "sessionID" ORDER BY "sessionID") s3 ON coalesce(s1."sessionID", s2."sessionID") = s3."sessionID" FULL OUTER JOIN 
        (SELECT "sessionID", count("userID") AS "0.4" FROM sesh WHERE "percent" >= 0.4 GROUP BY "sessionID" ORDER BY "sessionID") s4 ON coalesce(s1."sessionID", s2."sessionID", s3."sessionID") = s4."sessionID" FULL OUTER JOIN 
        (SELECT "sessionID", count("userID") AS "0.0" FROM sesh WHERE "percent" >= 0.0 GROUP BY "sessionID" ORDER BY "sessionID") s5 ON coalesce(s1."sessionID", s2."sessionID", s3."sessionID", s4."sessionID") = s5."sessionID") "allsessions"
        INNER JOIN "session" s ON s."sessionID" = "allsessions"."sessionID"
        INNER JOIN "presentation" p ON s."presentationID" = p."presentationID"
        WHERE "allsessions"."sessionID" IN (SELECT "sessionID" FROM "session" s INNER JOIN "presentation" p ON s."presentationID" = p."presentationID" AND p."userID" = %s)
        ORDER BY "allsessions"."sessionID"

          """, [userID])
    columns = ('sessionID', '1.0', '0.8', '0.6', '0.4', '0.0', 'createdAt', 'title')
    results = []
    for row in cur.fetchall():
       results.append(dict(zip(columns, row)))
    return str(json.dumps(results, indent=2))
  except psycopg2.Error as e:
    print e.pgerror
    return 'Server Failure', status.HTTP_400_BAD_REQUEST


# @app.route('/sessionStats/<id>')
# def sessionStats(id):
#     cur.execute("""SELECT count(q."questionID") from "question" q inner join "session" s on s."presentationID" = q."presentationID" and s."sessionID" = %s""",(id))
#     questionCount = cur.fetchone()[0]
#     cur.execute("""SELECT count(p."userID") from "participant" p inner join "session" s on s."sessionID" = p."sessionID" and s."sessionID" = %s""",(id))
#     participantCount = cur.fetchone()[0]
#     cur.execute("""SELECT count(p."userID") from "participant" p inner join "session" s on s."sessionID" = p."sessionID" and s."sessionID" = %s""",(id))
#     responseCount = cur.fetchone()[0]   


app.register_error_handler(400, lambda e: 'bad request!')

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=4555)

