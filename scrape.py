import pandas as pd
from lxml import html
import requests

TEAM_CODES = ['crd', 'atl', 'rav', 'buf', 'car', 'chi', 'cin','cle','dal','den','det','gnb','htx','clt','jax','kan',
			'mia','min','nwe','nor','nyg','nyj','rai','phi','pit','sdg','sfo','sea','ram','tam','oti','was']

TEAM_NAMES = ['Cardinals','Falcons','Ravens','Bills','Panthers','Bears','Bengals','Browns','Cowboys','Broncos','Lions','Packers','Texans','Colts','Jaguars','Chiefs','Dolphins',
				'Vikings','Patriots','Saints','Giants','Jets','Raiders','Eagles','Steelers','Chargers','49ers','Seahawks','Rams','Buccaneers','Titans','Redskins']

TEAMS = dict(zip(TEAM_NAMES,TEAM_CODES))

def get_team_string_regular(t):

	return "http://www.pro-football-reference.com/play-index/play_finder.cgi?request=1&match=summary_all&search=&player_id=&year_min=2015&year_max=2015&team_id=%s&opp_id=&game_type=&playoff_round=&game_num_min=0&game_num_max=99&week_num_min=0&week_num_max=99&quarter=1&quarter=2&quarter=3&quarter=4&quarter=5&tr_gtlt=lt&minutes=15&seconds=00&down=3&down=4&yds_to_go_min=1&yds_to_go_max=5&yg_gtlt=gt&yards=&is_first_down=-1&field_pos_min_field=team&field_pos_min=&field_pos_max_field=team&field_pos_max=&end_field_pos_min_field=team&end_field_pos_min=&end_field_pos_max_field=team&end_field_pos_max=&type=PASS&type=RUSH&is_complete=-1&is_turnover=-1&turnover_type=interception&turnover_type=fumble&is_scoring=-1&score_type=touchdown&score_type=field_goal&score_type=safety&is_sack=-1&include_kneels=0&no_play=0&game_day_of_week=&game_location=&game_result=&margin_min=&margin_max=&order_by=yards&rush_direction=LE&rush_direction=LT&rush_direction=LG&rush_direction=M&rush_direction=RG&rush_direction=RT&rush_direction=RE&pass_location=SL&pass_location=SM&pass_location=SR&pass_location=DL&pass_location=DM&pass_location=DR" % t

def get_team_string_twopoint(t):
	return "http://www.pro-football-reference.com/play-index/play_finder.cgi?request=1&match=summary_all&search=&player_id=&year_min=2015&year_max=2015&team_id=%s&opp_id=&game_type=&playoff_round=&game_num_min=0&game_num_max=99&week_num_min=0&week_num_max=99&quarter=1&quarter=2&quarter=3&quarter=4&quarter=5&tr_gtlt=lt&minutes=15&seconds=00&yds_to_go_min=&yds_to_go_max=&yg_gtlt=gt&yards=&is_first_down=-1&field_pos_min_field=team&field_pos_min=&field_pos_max_field=team&field_pos_max=&end_field_pos_min_field=team&end_field_pos_min=&end_field_pos_max_field=team&end_field_pos_max=&type=2PCR&type=2PCP&is_complete=-1&is_turnover=-1&turnover_type=interception&turnover_type=fumble&is_scoring=-1&score_type=touchdown&score_type=field_goal&score_type=safety&is_sack=-1&include_kneels=0&no_play=0&game_day_of_week=&game_location=&game_result=&margin_min=&margin_max=&order_by=yards&rush_direction=LE&rush_direction=LT&rush_direction=LG&rush_direction=M&rush_direction=RG&rush_direction=RT&rush_direction=RE&pass_location=SL&pass_location=SM&pass_location=SR&pass_location=DL&pass_location=DM&pass_location=DR" % t


def get_page(s):

	return requests.get(s).content

def get_table(s,which="regular"):

	xpath = '//div[@id="div_"]/table'
	
	tree = html.fromstring(get_page(s))

	try:
		table = tree.xpath(xpath)[0]
	except IndexError:
		return None

	return table

def get_table_values(table):

	if table is None:
		return pd.DataFrame()

	_,thead,tbody = table.getchildren()

	columns = []

	for th in thead.getchildren()[0].getchildren():
		if th.getchildren():
			columns.append(th.getchildren()[0].text)
		else:
			columns.append(th.text)

	values = []
	for tr in tbody.getchildren():
		row = []
		for td in tr.getchildren():
			if td.getchildren():
				row.append(td.getchildren()[0].text)
			else:
				row.append(td.text)
		values.append(row)
	
	return pd.DataFrame(values,columns=columns)

def team_table(t, which="regular"):

	def table_process(table):

		if table.shape[0] == 0:
			return table

		del table['Detail']
		table.Yds = table.Yds.fillna(0)
		table.Yds = table.Yds.astype(int)
		table.ToGo = table.ToGo.astype(int)
		table['success'] = (table.Yds > table.ToGo).astype(int)
		# table.Tm = table.Tm.apply(lambda x: TEAM_CODES.index(TEAMS[x]))
		# table.Opp = table.Opp.apply(lambda x: TEAM_CODES.index(TEAMS[x]))
		table['TmScore'],table['OppScore'] = zip(*table.Score.str.split("-").tolist())
		table[['TmScore','OppScore']] = table[['TmScore','OppScore']].astype(int)
		table['ScoreDifferential'] = table.TmScore - table.OppScore

		if which == "twopoint":
			table.success = (table.EPA == '1').astype(int)

		return table

	if which == "regular":
		return table_process(get_table_values(get_table(get_team_string_regular(t))))
	else:
		return table_process(get_table_values(get_table(get_team_string_twopoint(t), 'twopoint')))

def scrape_all():

	all_tables_regular = None
	all_tables_twopoint = None
	for t in TEAM_CODES:
		table = team_table(t)
		table.to_csv("data/%s_regular.csv"% t,index=False)

		if all_tables_regular is None:
			all_tables_regular = table
		else:
			all_tables_regular = pd.concat((all_tables_regular,table))

		table = team_table(t,"twopoint")
		table.to_csv("data/%s_twopoint.csv"% t,index=False)

		if all_tables_twopoint is None:
			all_tables_twopoint = table
		else:
			all_tables_twopoint = pd.concat((all_tables_twopoint,table))

		
	all_tables_regular.to_csv("data/all_regular.csv",index=False)
	all_tables_twopoint.to_csv("data/all_twopoint.csv",index=False)


if __name__ == "__main__":
	scrape_all()