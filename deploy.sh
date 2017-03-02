#!/usr/bin/env bash

echo "stopping running application"
ssh $DEPLOY_USER@$DEPLOY_HOST 'docker stop ngage-stats'
ssh $DEPLOY_USER@$DEPLOY_HOST 'docker rm ngage-stats'

echo "pulling latest version of the code"
ssh $DEPLOY_USER@$DEPLOY_HOST 'docker pull nanongage/ngage-stats:latest'

echo "starting the new version"
ssh $DEPLOY_USER@$DEPLOY_HOST 'docker run -d --restart=always --link ngage-db:ngagedb -e DBIP="'$DBIP'" -e DBDB="'$DBDB'" -e DBPW="'$DBPW'" --name ngage-stats -p 4555:4555 nanongage/ngage-stats:latest'

echo "success!"

exit 0