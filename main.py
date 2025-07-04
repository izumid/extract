import mysql.connector
import configparser
import os
import traceback
import datetime
import re
import pandas as pd
import decimal
import datetime
from collections import Counter
import json

def file_fill(file, header, message):
	file.write(header)
	if message is None: traceback.print_exc(file=file)
	else: file.write(f"{message}\n\n")
	file.write(f"{"="*50}\n\n")
	file.write("\n\n")


def log(filename,header,period,message=None,overright_size=2):
	filename = filename + ".txt"
	header = f"-=-=-= {header}: {period};  =-=-=-=\n\n"
	
	if not os.path.exists(os.path.join(os.getcwd(),filename)): open(filename, "x")
	
	if os.stat(filename).st_size < overright_size:
		with open(filename, 'a+') as f:
			file_fill(file=f,header=header,message=message)
	else:
		with open(filename, 'w+') as f:
			file_fill(file=f,header=header,message=message)


def show_time(on,message,time):
	if on: print(f"{message}: {time}")


def debug_code(debug,message,var=None):
	if debug == 1: print(f"{message}: {var};\r\n")


def extract(query,config,debug):
	try: 
		connection = mysql.connector.connect(**config)
		cursor = connection.cursor()    

		for result in cursor.execute(query, multi=True):
			if result.with_rows: result_set = result.fetchall()

		cursor.close()
		connection.close()
		if result_set is None or result_set == []: log("log_error",f"Step: 'Cursor execute'", datetime.datetime.today(), message=f"Empty result set!! \n\n Number of rows affected [{result.rowcount}] by statement:\n '{result.statement}'")
	except mysql.connector.Error as error:
		debug_code(debug,(error,"Can't connect."))
		log("log_error",f"Step: 'DB Connection'", datetime.datetime.today())

	return(result_set)


def database_column(query):
	list_aux = re.findall(r'(as|AS|As|aS)\s*"([^"]*)"', query)
	header = []

	for x in [x[1] for x in list_aux]:
		if not x in header: header.append(x)
	
	return(header)


def result_set_transform(result_set,column_name,debug):
	ls=[]

	for element in result_set:
		lst = list(element)
		lst = [float(x) if isinstance(x, decimal.Decimal) == True else x for x in lst]
		ls.append(lst)
	
	df = pd.DataFrame(ls)
	df.columns = column_name

	return(df)


def base_generate(separated,query,config,debug,destination,basefile_name,day=0,last_month=0):
	column_name = database_column(query)

	end_date = datetime.datetime.now() + datetime.timedelta(days=day)
	today = int(end_date.strftime('%d'))

	if today == 1: start_date = end_date
	else: start_date = end_date - datetime.timedelta(days=today-1)

	if separated == False:
			result_set = extract(query,config,debug)
			debug_code(debug,"Executed query",query)
			df = result_set_transform(result_set,column_name,debug)

			prefix = end_date.strftime("%Y%m%d")
			
			for path in destination:
				if not os.path.exists(os.path.join(path,end_date.strftime('%Y'))): 
					os.makedirs(os.path.join(path,end_date.strftime('%Y')))

				path_file = os.path.join(path,end_date.strftime('%Y'),f"{prefix}_{basefile_name}.xlsx")
				debug_code(debug,"Previous month file name",path_file)
				df.to_excel(path_file,index=False)
	else:
			temp_end_date = end_date + datetime.timedelta(days=day)
			for i in range(last_month):
				sql_q = query

				for i in range((Counter(query.split())["custom"])+1):
					if i % 2 == 0: sql_q = sql_q.replace("custom",start_date.strftime("%Y%m%d"),1)
					else:  sql_q = sql_q.replace("custom",temp_end_date.strftime("%Y%m%d"),1)

				result_set = extract(sql_q,debug)

				if result_set is not None and result_set != []:
					df = result_set_transform(result_set,column_name,debug)
							
					debug_code(debug,"Previous month query", sql_q)
					prefix = f"{start_date.strftime("%Y")}{start_date.strftime("%m").zfill(2)}.{start_date.strftime("%B")}"
					
					for path in destination:
						if not os.path.exists(os.path.join(path,start_date.strftime('%Y'))): 
							os.makedirs(os.path.join(path,start_date.strftime('%Y')))
						
						path_file = os.path.join(path,start_date.strftime('%Y'),f"{prefix}_{basefile_name}.xlsx")
						debug_code(debug,"Previous month file name",path_file)
						df.to_excel(path_file,index=False)
						debug_code(debug,"File created!!")

				end_date = end_date - datetime.timedelta(days=int(end_date.strftime('%d')))
				temp_end_date = end_date + datetime.timedelta(days=day)
						
				debug_code(debug,"Previous month end_date",end_date)

				start_date = end_date - datetime.timedelta(days=int(end_date.strftime('%d'))-1)
				debug_code(debug,"Previous month start_date",start_date)


def main():
	try:
		config = configparser.RawConfigParser()
		config.read(os.path.join(os.getcwd(),'config.ini'))
		with open(os.path.join(os.getcwd(),"config/config.json")) as jsonfile: config_json = json.load(jsonfile)
		debug = int(config["EVALUATE"]["debug"])
		start = datetime.datetime.now()
		check_time = int(config["EVALUATE"]["time"])
		basefile_name = config["FILE"]["basefile_name"]
		export_type  = int(config["SQL"]["export_type"])
		destination = (config["PATH"]["destination"]).replace("custom",os.getlogin()).split(',')
		day = int(config["SQL"]["add_current_day"])
		with open(os.path.join(os.getcwd(),f"query/{config["FILE"]["name_query"]}.sql"), 'r', encoding='utf-8') as file: query = file.read()

		match export_type:
			case 0:
				base_generate(separated=False,query=query,debug=debug,destination=destination,basefile_name=basefile_name)
			case 1:  
				base_generate(separated=True,query=query,debug=debug,destination=destination,basefile_name=basefile_name,day=day,last_month=int(config["FILE"]["previous_month"]))
			case 2:
				index_where =  query.index("WHERE")
				query=(query[:index_where-1]+";")
				base_generate(separated=False,query=query,debug=debug,destination=destination,basefile_name=basefile_name,day=day,last_month=int(config["FILE"]["previous_month"]))
		
	except Exception as error:
		debug_code(debug,({"eror": f"Failed to generate file(s): {error}"}))
		log("log_error","'Saving base file'",datetime.datetime.today())

	log(check_time,"Start Time",start)
	log(check_time,"Duration",datetime.datetime.now()-start)


if __name__ == "__main__":
	main()