from flask import Flask, render_template, request,url_for
import twitter
import json
import time
import subprocess 
from urllib import unquote,urlencode

app = Flask(__name__)

@app.route("/")
def hello():
    return render_template('index.html')

@app.route('/qmap', methods=['POST'])
def get_tweet_data():

    userHashTag = request.form['hashtag']
    app.logger.info(userHashTag)
    hashtag = userHashTag
    if hashtag=='':
        return '';
    app.logger.info(hashtag) 

    # Set your own
    CONSUMER_KEY = ''
    CONSUMER_SECRET = ''
    OAUTH_TOKEN = ''
    OAUTH_TOKEN_SECRET = ''
    API_KEY ='';
    auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET,
                               CONSUMER_KEY, CONSUMER_SECRET)
    
    twitter_api = twitter.Twitter(auth=auth)

    search_results = twitter_api.search.tweets(q=hashtag, count=100,result_type='recent', geocode = '39.8,-95.58306884,2500km');
 
    # Extract the information on the (up to) 100 most recent tweets
    # as a list
    statuses = search_results['statuses']
 
    # Iterate through 5 more batches of results by following the cursor 
    # back in time
    for _ in range(10):
        #print("Length of statuses", len(statuses))
        try:
            next_results = search_results['search_metadata']['next_results']
            app.logger.info('Second query')
        # The as statement is required in Python 3  
        # A comma would be required instead for Python 2.5 and earlier  
        # Python 2.6 and 2.7 support both the comma and the as statement
        except KeyError as e: # No more results when next_results doesn't exist
            app.logger.info('No more results')
            break
        
        # Create a dictionary from next_results, which has the following form:
        # ?max_id=313519052523986943&q=NCAA&include_entities=1
        kwargs = dict([kv.split('=') for kv in unquote(next_results[1:]).split("&") ])    
        
        # Search for the 100 next most recent tweets
        search_results = twitter_api.search.tweets(**kwargs)
        # Append the results of the last search to the statuses list
        statuses += search_results['statuses']

    lenStat = len(statuses);
    app.logger.info('Found ' + str((lenStat))+ ' tweets'); 

    locationInfo = [];

    count = 0;

    for i in range(len(statuses)):
    	count +=1;
    	locationInfo.append({'type':'Feature','properties':{'timestamp':statuses[i]['created_at']}, 'geometry':statuses[i]['coordinates']})

    #app.logger.info(json.dumps(locationInfo,indent=1));
    
    for i in range(len(statuses)):
        if 'coordinates' in statuses[i]:
            if statuses[i]['coordinates'] is not None:
                element = {};
                element['type'] = 'Feature';
                element['properties'] ={'timestamp':statuses[i]['created_at']};#,'hashtag':hashtag};
                s = statuses[i]['coordinates'];
                element['geometry'] = s; 
    	          
	app.logger.info('Total '+str(len(locationInfo)) + ' tweets with loc info')
	lcInfo={};
	lcInfo['type']="FeatureCollection";
	lcInfo['features']=locationInfo;


	outputFile = 'flask_'+hashtag+'.geojson';
	with open(outputFile, 'w') as outfile:
	    json.dump(lcInfo, outfile)

	app.logger.info('Wrote to file');

	if len(locationInfo) < 10:
		return 'Very few tweets found to visualize hashtag '+ hashtag;

	command="curl -v -F file=@"+outputFile+" \"https://ilgeakkaya.cartodb.com/api/v1/imports/?api_key="+API_KEY+"&create_vis=true\"";

	result = subprocess.check_output(command, shell=True)
	resj = json.loads(result) 

	while resj['success']!=True:
		time.sleep(1)
		result = subprocess.check_output(command, shell=True)
		resj = json.loads(result) 
		app.logger.info('Trying');

	if resj['success']:
	    statusOfImport= "curl -v \"https://ilgeakkaya.cartodb.com/api/v1/imports/"+str(resj['item_queue_id'])+"?api_key="+API_KEY+"\"";
	    res2 = subprocess.check_output(statusOfImport, shell=True)
	    
	    res2 = json.loads(res2);
	    app.logger.info(res2['state']);

	    while res2['state']!='complete':
			time.sleep(1)
			statusOfImport= "curl -v \"https://ilgeakkaya.cartodb.com/api/v1/imports/"+str(resj['item_queue_id'])+"?api_key="+API_KEY+"\"";
			res2 = subprocess.check_output(statusOfImport, shell=True)
			res2 = json.loads(res2)
			app.logger.info(res2['state']);

	   #finally, convert the timestamp row to date format

        columnStatus = False
        tname = res2['table_name']
        while columnStatus == False:
        	convertTimestamp = "curl -v \"https://ilgeakkaya.cartodb.com/api/v2/sql?q=SELECT *, CAST (timestamp AS date) FROM "+res2['table_name']+"&api_key="+API_KEY+"\"";
        	#convertTimestamp = "curl -v \"https://ilgeakkaya.cartodb.com/api/v1/imports/q=UPDATE "+tname+" SET my_time = to_timestamp(timestamp, 'MMM dd DD HH:MM:SS +0000 YYYY')&api_key="+API_KEY+"\"";
        	
        	res3 = subprocess.check_output(statusOfImport, shell=True)
        	res3 = json.loads(res3);
        	columnStatus = res3['state'];
        	app.logger.info(res3['visualization_id']);


	return res2['table_name'];


if __name__ == "__main__":
    app.run(debug=True)


