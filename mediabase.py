import urllib2
import urllib
import cookielib, Cookie
from lxml import etree

login_url = "http://mediabase.com/WebLogon/ValidateLogon.asp"
login_values = {
	'userName':'',
	'password':'',
	'login.x':'26',
	'login.y':'10',
	'login':'LOGIN'
}

names = {	
	'y0R': 'Rhythmic', 
	'a2R': 'Hot AC', 
	'r1R': 'Triple A', 
	'a1R': 'AC', 
	'h1R': 'Top 40', 
	'g1R': 'Gospel -> Overall', 
	'u2R': 'Urban AC', 
	'c1R': 'Country -> Overall', 
	'after_midnite': 'After Midnite', 
	'u1R': 'Urban', 
	'overall_big_picture': 'THE BIG PICTURE WITH HISTORY', 
	'r2R': 'Active Rock', 
	'r3R': 'Alternative', 
	'y1R': 'Dance'
}

chart_with_airplay_rows_xpath = "//table[@id='Table4']/*/tr[@align='right']"
afet_midnite_chart_rows_xpath = "//table[@id='Table4']/*/tr[@align='right']"
big_picture_with_history_rows_xpath = "//table[@id='Table4']/*/tr[@align='right']"
table_row_xpath = "//tr[@align='right']"

chart_with_airplay_grid_columns = {
	'rank_lw': './/td[1]/span/text()',
	'rank_tw': './/td[2]/span/text()',
	'artist': './/a[1]//text()',
	'song': './/td[6]/a/text()',
	'spins_tw': './/td[9]/span/text()',
	'spins_pm': './/td[11]/span/text()',
	'audience_tw': './/td[@bgcolor="#D6D7E0"][1]/span/text()',
	'audience_pm': './/td[@bgcolor="#D6D7E0"][3]/span/text()',
}

chart_with_airplay_grid_columns_v2 = {
	'rank_lw': ['.//span//text()', 0],
	'rank_tw': ['.//span//text()', 1],
	'artist': ['.//span//text()', 2],
	'song': ['.//a//text()', 2],
	'spins_tw': ['.//span//text()', 5],
	'spins_pm': ['.//span//text()', 7],
	'audience_tw': ['.//td[@bgcolor="#D6D7E0"][1]/span/text()', 0],
	'audience_pm': ['.//td[@bgcolor="#D6D7E0"][3]/span/text()', 0]
}

chart_with_airplay_grid_columns_lw = {
	'rank_lw': ['.//span//text()', 2],
	'artist': ['.//span//text()', 3],
	'song': ['.//span//text()', 5],
}

afet_midnite_chart_columns = {
	'rank_lw': [".//text()", 0],
	'rank_tw': [".//text()", 2],
	'artist': [".//text()", 4],
	'song': [".//text()", 7],
	'spins_tw': [".//text()", 11],
	'spins_pm': [".//text()", 15],
	'audience_tw': '-',
	'audience_pm': '-',
}

big_picture_with_history_columns = {
	'rank_lw': './/td[1]/span/text()',
	'rank_tw': './/td[2]/span/text()',
	'artist': './/td[3]/span/text()',
	'song': './/td[4]/span/text()',
	'spins_tw': './/td[6]/span/text()',
	'spins_pm': './/td[8]/span/text()',
	'audience_tw': './/td[14]/span/text()',
	'audience_pm': './/td[16]/span/text()',
}

def get_mediadb_data(urls):
	## Setting cookie jar to pass auth
	cookies = cookielib.CookieJar()
	## Building opener on it
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies), urllib2.HTTPHandler)
	## Requesting login page
	request = urllib2.Request("http://mediabase.com/WebLogon/WebLogon.asp")
	response = opener.open(request)
		
	## Encoding login data and sending POST request
	data = urllib.urlencode(login_values)
	request = urllib2.Request(login_url, data)
	response = opener.open(request)
	
	result = []
	
	for e in urls:
		columns, url, format = e
		request = urllib2.Request(url)
		response = opener.open(request)
		response_body = response.read()
		result.append([columns, response_body, format])
	
	return result
	
	
def get_lw_data(url):
	## Setting cookie jar to pass auth
	cookies = cookielib.CookieJar()
	## Building opener on it
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies), urllib2.HTTPHandler)
	## Requesting login page
	request = urllib2.Request("http://mediabase.com/WebLogon/WebLogon.asp")
	response = opener.open(request)
		
	## Encoding login data and sending POST request
	data = urllib.urlencode(login_values)
	request = urllib2.Request(login_url, data)
	response = opener.open(request)
	
	request = urllib2.Request(url)
	response = opener.open(request)
	response_body = response.read()
	
	return response_body


def scrape(format, numdays, threshold):
	urls = []
	
	## From list of input formats generate requests with according XPATH
	for f in format:
		if f == "after_midnite":
			url = "http://mediabase.com/mmrweb/7/BuildingAfterMidniteChart.asp?NUMDAYS=%s&ChartType=R" % (numdays)
			columns = afet_midnite_chart_columns
		elif f == "overall_big_picture":
			url = "http://mediabase.com/mmrweb/7/BigPictureWithHistory.asp?NUMDAYS=%s&ReportMode=BUILDING&ChartType=R" % (numdays)
			columns = big_picture_with_history_columns
		else:
			url = "http://mediabase.com/mmrweb/Building/BuildingChartWAirplaygrid.asp?NUMDAYS=%s&format=%s" % (numdays, f)
			columns = chart_with_airplay_grid_columns_v2
		
		urls.append([columns, url, f])

	## And get all the responses in one list
	data = get_mediadb_data(urls)
	
	result = []
	
	## Parse each response
	for dataset in data:
		columns, html, format = dataset
		tree = etree.HTML(html)
		table_rows = tree.xpath(table_row_xpath)

		tmp_res = []
		
		for row in table_rows:
			e = {}
			for name, val in columns.iteritems():
				try:
					e_xpath = val[0]
					pos = val[1]
					e[name] = row.xpath(e_xpath)[pos]
				except:
					e[name] = '-'
			if not e["rank_tw"].isdigit():
				continue
			tmp_res.append(e)
		threshold_value = int(tmp_res[int(threshold)-1]['spins_tw'])
		result.append([tmp_res, format, threshold_value])

	return result
	
		
def get_search_results(data, artist, song):
	result = {}
	
	target_name = "%s/%s" % (artist, song)
	result[target_name] = {}
	
	for dataset in data:
		dataset_rows, format, threshold_value = dataset
		result[target_name][format] = []
		
		for row in dataset_rows:
			row["threshold_value"] = threshold_value
			if artist.lower() in row["artist"].lower() and song.lower() in row["song"].lower():
				result[target_name][format].append(row)
		
		url = "http://mediabase.com/mmrweb/7/ChartsSaturday.asp?format=%s" % format
		
		
		
		lw_data = get_lw_data(url)
		tree = etree.HTML(lw_data)
		table_rows = tree.xpath(table_row_xpath)
		tmp_res = []
		for row in table_rows:
			e = {}
			for name, val in chart_with_airplay_grid_columns_lw.iteritems():
				try:
					e_xpath = val[0]
					pos = val[1]
					e[name] = row.xpath(e_xpath)[pos]
				except:
					e[name] = '-'
			tmp_res.append(e)	
		
		for row in result[target_name][format]:
			for e in tmp_res:
				if e["artist"] == row["artist"] and e["song"] == row["song"]:
					print row["rank_lw"], e["rank_lw"]
					row["rank_lw"] = e["rank_lw"]
					print row["rank_lw"], e["rank_lw"]
	
	
	print result
	return result
	
def process_search_result(data, threshold):
	result = {}
	for entry in data.keys():
		result[entry] = {}
		for chart in data[entry].keys():
			chart_name = names[chart]
			result[entry][chart_name] = {}
			for row in data[entry][chart]:
				result[entry][chart_name]["rank"] = "%s*-%s*" % (row['rank_lw'], row['rank_tw'])
				result[entry][chart_name]["spins"] = "%s spins (%s)" % (row['spins_tw'], row['spins_pm'])
				result[entry][chart_name]["top"] = "%s spins from top %s" % (int(row['threshold_value']) - int(row['spins_tw']), threshold)
				result[entry][chart_name]["audience"] = "%s mil (%sk)" % (row['audience_tw'], float(row['audience_pm']) * 1000)
			if not result[entry][chart_name]:
				result[entry].pop(chart_name, None)
	print result
	return result
	
def make_email_body(data):
	if not data[data.keys()[0]]:
		return None
	entry = data[data.keys()[0]]
	email = "%s\n" % (data.keys()[0])
	for row_key in entry.keys():
		if entry[row_key]:
			email += "%s %s %s %s %s\n" % (
				row_key,
				entry[row_key]['rank'],
				entry[row_key]['spins'],
				entry[row_key]['top'],
				entry[row_key]['audience']
				)
	print email
	return email
