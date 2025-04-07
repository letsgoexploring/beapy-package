import datetime
import requests
import numpy as np
import pandas as pd
import sys


# August 3, 2015: Updated the getNipa() method to accomodate possible differences in data availability for series in tables. 
#                 Cleaned up and organized the code substantially.

class initialize:

    def __init__(self,apiKey=None):
        ''' Saves the API key.'''

        self.apiKey = apiKey

    # 1. Methods for getting information about the available datasets, parameters, and parameter values.

    def getDataSetList(self):

        '''Method returns a list of describing the datasets available through the BEA API. No arguments'''

        r = requests.get('http://www.bea.gov/api/data?&UserID='+self.apiKey+'&method=GETDATASETLIST&ResultFormat=JSON&')
        rJson = r.json()
        lines='Datasets available through the BEA API:\n\n'
        n=1

        dataSetList = []
        for element in rJson['BEAAPI']['Results']['Dataset']:
            if np.mod(n,5)==0:
                lines = lines+str(n).ljust(4,' ')+element['DatasetName'].ljust(20,' ') +': '+element['DatasetDescription']+'\n\n'
                dataSetList.append(element['DatasetName'])
            else:
                lines = lines+str(n).ljust(4,' ')+element['DatasetName'].ljust(20,' ') +': '+element['DatasetDescription']+'\n'
                dataSetList.append(element['DatasetName'])
            n+=1
        print(lines)
        self.dataSets = lines
        self.dataSetList = dataSetList

    def getParameterList(self,dataSetName):

        '''Method returns a list of the parameters for a given dataset. Argument: one of the dataset names returned by getDataSetList().'''

        r = requests.get('http://www.bea.gov/api/data?&UserID='+self.apiKey+'&method=GETPARAMETERLIST&datasetname='+dataSetName+'&ResultFormat=JSON&')
        rJson = r.json()
        lines = 'Parameters for the '+dataSetName+' dataset.\n\n'

        strWidth  = 25
        descrWidth = 50
        parameterList = []

        def splitString(origString, maxLength):
            splitLines = []
            line = ''
            for word in origString.split(' '):
                if len(line)+1+len(word)<maxLength:
                    line = line+word+' '
                else:
                    splitLines.append(line)
                    line = word+' '
            if len(line) != 0:
                splitLines.append(line)

            return splitLines


        for element in rJson['BEAAPI']['Results']['Parameter']:

            elementKeys = list(element.keys())

            lines = lines+'Parameter name'.ljust(strWidth,' ')  +'  '+element['ParameterName']+'\n'

            split = splitString(element['ParameterDescription'],descrWidth)
            for n,line in enumerate(split):
                if n ==0:
                    lines = lines+'Description'.ljust(strWidth,' ')  + '  '+line+'\n'
                else:
                    lines = lines+'  '.ljust(strWidth,' ')  + '  '+line+'\n'

            parameterList.append(element['ParameterName'])

            if element['ParameterIsRequiredFlag']==0:
                lines = lines+'Required?'.ljust(strWidth,' ')  + '  No'+'\n'
            else:
                lines = lines+'Required?'.ljust(strWidth,' ')  + '  Yes'+'\n'
            
            if 'AllValue' in elementKeys:
                if element['AllValue']=='':
                    lines = lines+'\"All\" Value'.ljust(strWidth,' ')  + '  N/A'+'\n'
                else:
                    lines = lines+'\"All\" Value'.ljust(strWidth,' ') +'  '+element['AllValue']+'\n'
            # if element['MultipleAcceptedFlag']==0:
            #     lines = lines+'Multiple (list) accepted?'.ljust(strWidth,' ')  + '  No'+'\n'
            # else:
            #     lines = lines+'Multiple (list) accepted?'.ljust(strWidth,' ')  + '  Yes'+'\n'
            lines = lines+'Data type'.ljust(strWidth,' ')  + '  '+element['ParameterDataType']+'\n'
            if 'ParameterDefaultValue' in elementKeys:
                if element['ParameterDefaultValue']=='':
                    lines = lines+'Default value'.ljust(strWidth,' ')  + '  N/A'+'\n\n\n'
                else:
                    lines = lines+'Default value'.ljust(strWidth,' ')  + '  '+element['ParameterDefaultValue']+'\n\n\n'
            else:
                lines = lines+'\n\n'

        print(lines)
        self.parameters = lines
        self.parameterList = parameterList

    def getParameterValues(self,dataSetName, parameterName):

        '''Method returns a list of the  values accepted for a given parameter of a dataset.
        Arguments: one of the dataset names returned by getDataSetList() and a parameter returned by getParameterList().'''

        r = requests.get('http://bea.gov/api/data?&UserID='+self.apiKey+'&method=GetParameterValues&datasetname='+dataSetName+'&ParameterName='+parameterName+'&')
        rJson = r.json()


        lines='Values accepted for '+parameterName+' in dataset '+dataSetName+':\n\n'

        if dataSetName.lower() == 'nipa' and parameterName.lower() == 'showmillions' and 'ParamValue' not in rJson['BEAAPI']['Results'].keys():

            lines+= 'ShowMillions'.ljust(20,' ')+': N\n'
            lines+= 'Description'.ljust(20,' ')+': Units in billions of USD (default)\n\n'
            lines+= 'ShowMillions'.ljust(20,' ')+': Y\n'
            lines+= 'Description'.ljust(20,' ')+': Units in millions of USD\n\n'

        else:

            descrWidth = 50
            def splitString(origString, maxLength):
                splitLines = []
                line = ''
                for word in origString.split(' '):
                    if len(line)+1+len(word)<maxLength:
                        line = line+word+' '
                    else:
                        splitLines.append(line)
                        line = word+' '
                if len(line) != 0:
                    splitLines.append(line)

                return splitLines

            columnNames = []
            for n,element in enumerate(rJson['BEAAPI']['Results']['ParamValue']):
                for key in element.keys():
                    if key not in columnNames:
                        columnNames.append(key)
            
            data = np.zeros([n,len(columnNames)])
            data[:] = np.nan
            tempFrame = pd.DataFrame(data,columns = columnNames)

            for n,element in enumerate(rJson['BEAAPI']['Results']['ParamValue']):
                for key,value in element.items():
                    tempFrame.loc[n,key] = element[key]

            # Sort tempFrame if the parameter falls into one of a few special categories
            if dataSetName.lower() == 'nipa':
                if parameterName.lower() =='tableid':
                    tempFrame.sort(columns = ['TableID'])
                elif parameterName.lower() =='year':
                    tempFrame = tempFrame[['TableID','FirstAnnualYear','LastAnnualYear','FirstQuarterlyYear','LastQuarterlyYear','FirstMonthlyYear','LastMonthlyYear']]
                    tempFrame.sort(columns = ['TableID'])

            elif dataSetName.lower() == 'fixedassets':
                if parameterName.lower() =='tableid':
                    tempFrame.sort(columns = ['TableID'])
                elif parameterName.lower() =='year':
                    tempFrame = tempFrame[['TableID','FirstAnnualYear','LastAnnualYear']]
                    tempFrame.sort(columns = ['TableID'])

            elif dataSetName.lower() == 'gdpbyindustry':
                if parameterName.lower() =='tableid':
                    tempFrame.sort(columns = ['Key'])

            for i in tempFrame.index:
                for c in tempFrame.columns:
                    split = splitString(tempFrame.loc[i,c],descrWidth)
                    for n, words in enumerate(split):
                        if n==0:
                            try:
                                lines+=c.ljust(20,' ')+': '+str(int(words))+'\n'
                            except:
                                lines+=c.ljust(20,' ')+': '+str(words)+'\n'
                        else:
                            try:
                                lines+=''.ljust(20,' ')+'  '+str(words)+'\n'
                            except:
                                lines+=''.ljust(20,' ')+'  '+str(words)+'\n'
                lines+='\n'
        
        print(lines)
        self.parameterValues = lines

    # 2. Methods for retreiving data.

    # 2.1 Regional Data (statistics by state, county, and MSA)

    def getRegionalData(self,KeyCode=None,GeoFips='STATE',Year='ALL'):
        '''Retrieve state and regional data.

        Name        Type    Required?   Multiple values?    "All" Value                     Default

        KeyCode     int     yes         no                  N/A                             
        GeoFips     str     no          yes                 'STATE' or 'COUNTY' or 'MSA'    STATE
        Year        int     no          yes                 "ALL"                           ALL
        '''

        # if type(KeyCode)==list:
        #     KeyCode = ','.join(KeyCode)

        # if type(Year)==list:
        #     Year = [str(y) for y in Year]
        #     Year = ','.join(Year)

        # if type(GeoFips)==list:
        #     GeoFips = ','.join(GeoFips)

        uri = 'http://bea.gov/api/data/?UserID='+self.apiKey+'&method=GetData&datasetname=RegionalData&KeyCode='+str(KeyCode)+'&Year='+str(Year)+'&GeoFips='+str(GeoFips)+'&ResultFormat=JSON&'
        r = requests.get(uri)
        rJson = r.json()

        dataDict = {}
        # dates = []
        # YearList = []
        # name =''

        columnNames = []
        dates = []

        try: 
            for element in rJson['BEAAPI']['Results']['Data']:
                if element['GeoName'] not in columnNames:
                    columnNames.append(element['GeoName'])

                date = convertDate(element['TimePeriod'],'A')
                if date not in dates:
                    dates.append(date)

            data = np.zeros([len(dates),len(columnNames)])
            data[:] = np.nan
            frame = pd.DataFrame(data,columns = columnNames, index = dates)

            for element in rJson['BEAAPI']['Results']['Data']:
                date = convertDate(element['TimePeriod'],'A')
                if 'DataValue' in element.keys():
                    frame.loc[date,element['GeoName']] = float(element['DataValue'].replace(',',''))

            frame = frame.sort_index()
            note = rJson['BEAAPI']['Results']['PublicTable']+' - '+rJson['BEAAPI']['Results']['Statistic']+' - '+rJson['BEAAPI']['Results']['UnitOfMeasure']
            
            return {'note':note,'data':frame}

        except:
            print('Invalid input.',sys.exc_info()[0])

    
    # 2.2 NIPA (National Income and Product Accounts)

    def getNipa(self,TableID=None,Frequency='A',Year='X',ShowMillions='N'):

        '''Retrieve data from a NIPA table.

        Name            Type    Required?   "All" Value     Default

        TableID         int     yes         N/A             None
        Frequency(A/Q)  str     yes         N/A             None
        Year            int     yes         "X"             "X"
        ShowMillions    str     no          N/A             'N'   
        '''

        if Frequency=='M':
            print('Error: monthly Frequency available for NIPA tables.')

        uri = 'http://bea.gov/api/data/?UserID='+self.apiKey+'&method=GetData&datasetname=NIPA&TableID='+str(TableID)+'&Frequency='+Frequency+'&Year='+str(Year)+'&ShowMillions='+ShowMillions+'&ResultFormat=JSON&'
        r = requests.get(uri)
        rJson = r.json()

        columnNames = []
        dates = []
        try:
            for element in rJson['BEAAPI']['Results']['Data']:
                if element['LineDescription'] not in columnNames:
                    columnNames.append(element['LineDescription'])
                
                date = convertDate(element['TimePeriod'],Frequency)
                if date not in dates:
                    dates.append(date)

            data = np.zeros([len(dates),len(columnNames)])
            data[:] = np.nan
            frame = pd.DataFrame(data,columns = columnNames, index = dates)

            for element in rJson['BEAAPI']['Results']['Data']:
                date = convertDate(element['TimePeriod'],Frequency)
                frame.loc[date,element['LineDescription']] = float(element['DataValue'].replace(',',''))
            
            frame = frame.sort_index()
            note = rJson['BEAAPI']['Results']['Notes'][0]['NoteText']

            return {'note':note,'data':frame}

        except:

            print('Error: invalid input.')

    # # 3.3 NIUnderlyingDetail (National Income and Product Accounts)

    # def getNIUnderlyingDetail(self,TableID,Frequency='A',Year='X'):

    #     if type(Year)==list:
    #         Year = [str(y) for y in Year]
    #         Year = ','.join(Year)

    #     uri = 'http://bea.gov/api/data/?UserID='+apiKey+'&method=GetData&datasetname=NIUnderlyingDetail&TableID='+str(TableID)+'&Year='+str(Year)+'&Frequency='+str(Frequency)+'&ResultFormat=JSON&'
    #     r = requests.get(uri)
    #     rJson = r.json()

    #     columnNames = []
    #     dates = []
    #     try:

    # 3.4 Fixed Assets

    def getFixedAssets(self,TableID=None,Year='X'):

        uri = 'http://bea.gov/api/data/?UserID='+self.apiKey+'&method=GetData&datasetname=FixedAssets&TableID='+str(TableID)+'&Year='+str(Year)+'&ResultFormat=JSON&'
        r = requests.get(uri)
        rJson = r.json()

        columnNames = []
        dates = []
        try:
            for element in rJson['BEAAPI']['Results']['Data']:
                if element['LineDescription'] not in columnNames:
                    columnNames.append(element['LineDescription'])
                
                date = convertDate(element['TimePeriod'],'A')
                if date not in dates:
                    dates.append(date)

            data = np.zeros([len(dates),len(columnNames)])
            data[:] = np.nan
            frame = pd.DataFrame(data,columns = columnNames, index = dates)

            for element in rJson['BEAAPI']['Results']['Data']:
                date = convertDate(element['TimePeriod'],'A')
                frame.loc[date,element['LineDescription']] = float(element['DataValue'].replace(',',''))
            
            frame = frame.sort_index()
            note = rJson['BEAAPI']['Results']['Notes'][0]['NoteText']
            
            return {'note':note,'data':frame}

        except:

            print('Error: invalid input.')

    # 3.5

    # def getMne(self,DirectionOfInvestment=None,OwnershipLevel=None,NonbankAffiliatesOnly=None,Classification=None,Country='all',Industry='all',Year='all',State='all',SeriesID=0):

    # 3.6 Gross domestic product by industry

    def getGdpByIndustry(self,TableID =None, Industry='ALL',Frequency='A',Year = 'ALL'):

        uri = 'http://bea.gov/api/data/?UserID='+self.apiKey+'&method=GetData&datasetname=GDPbyIndustry&TableID='+str(TableID)+'&Industry='+str(Industry)+'&Frequency='+str(Frequency)+'&Year='+str(Year)+'&ResultFormat=JSON&'
        r = requests.get(uri)
        rJson = r.json()

        columnNames = []
        dates = []

        try:
            for element in rJson['BEAAPI']['Results']['Data']:
                if element['IndustrYDescription'] not in columnNames:
                    columnNames.append(element['IndustrYDescription'])

                date = convertDate(element['Year'],Frequency)
                if date not in dates:
                    dates.append(date)

            data = np.zeros([len(dates),len(columnNames)])
            data[:] = np.nan
            frame = pd.DataFrame(data,columns = columnNames, index = dates)

            for element in rJson['BEAAPI']['Results']['Data']:
                date = convertDate(element['Year'],Frequency)
                frame.loc[date,element['IndustrYDescription']] = float(element['DataValue'].replace(',',''))
            
            frame = frame.sort_index()
            note = rJson['BEAAPI']['Results']['Notes'][0]['NoteText']

            return {'note':note,'data':frame}

        except:

            print('Error: invalid input.')



    # 3.7 ITA: International transactions

    def getIta(self,Indicator=None,AreaOrCountry='ALL',Frequency='A',Year='ALL'):

        if Indicator=='ALL' and 'ALL' in AreaOrCountry:
            print('Warning: You may not select \'ALL\' for both Indicator and AreaOrCountry')

        else:

            uri = 'http://bea.gov/api/data/?UserID='+self.apiKey+'&method=GetData&datasetname=ita&Indicator='+str(Indicator)+'&AreaOrCountry='+str(AreaOrCountry)+'&Year='+str(Year)+'&ResultFormat=JSON&'
            r = requests.get(uri)
            rJson = r.json()

            columnNames = []
            dates = [] 

            try:

                if AreaOrCountry.lower()  == 'all':

                    columnNames = []
                    dates = [] 

                    for element in rJson['BEAAPI']['Results']['Data']:
                        if element['AreaOrCountry'] not in columnNames:
                            columnNames.append(element['AreaOrCountry'])

                            date = convertDate(element['Year'],Frequency)
                            if date not in dates:
                                dates.append(date)

                    data = np.zeros([len(dates),len(columnNames)])
                    data[:] = np.nan
                    frame = pd.DataFrame(data,columns = columnNames, index = dates)

                    for element in rJson['BEAAPI']['Results']['Data']:
                        date = convertDate(element['Year'],Frequency)
                        if len(element['DataValue'].replace(',',''))>0:
                            frame.loc[date,element['AreaOrCountry']] = float(element['DataValue'].replace(',',''))
                        else:
                            frame.loc[date,element['AreaOrCountry']] = np.nan
                            
                else:

                    columnNames = []
                    dates = [] 

                    for element in rJson['BEAAPI']['Results']['Data']:
                        if element['Indicator'] not in columnNames:
                            columnNames.append(element['Indicator'])

                            date = convertDate(element['Year'],Frequency)
                            if date not in dates:
                                dates.append(date)

                    data = np.zeros([len(dates),len(columnNames)])
                    data[:] = np.nan
                    frame = pd.DataFrame(data,columns = columnNames, index = dates)





                    for element in rJson['BEAAPI']['Results']['Data']:
                        date = convertDate(element['Year'],Frequency)
                        if len(element['DataValue'].replace(',',''))>0:
                            frame.loc[date,element['Indicator']] = float(element['DataValue'].replace(',',''))
                        else:
                            frame.loc[date,element['Indicator']] = np.nan


                frame = frame.sort_index()
                units  = rJson['BEAAPI']['Results']['Data'][0]['CL_UNIT']
                mult = rJson['BEAAPI']['Results']['Data'][0]['UNIT_MULT']
                if int(mult) == 3:
                    units = 'Thousands of '+units
                elif int(mult) == 6:
                    units = 'Millions of '+units
                elif int(mult) == 9:
                    units = 'Billions of '+units
                if Frequency.lower() == 'q':
                    Notes = rJson['BEAAPI']['Results']['Notes']
                    for note in Notes:
                        if note['NoteRef'] == 'Q':
                            noteQ = note['NoteText']

                    units = units + ', '+ noteQ
                
                return {'note':units,'data':frame}

            except:
                print(rJson['BEAAPI']['Error']['ErrorDetail']['Description'])



    # 3.8 IIP: International investment position

    def getIip(self,TypeOfInvestment=None,Component=None,Frequency='A',Year='ALL'):

        uri = 'http://bea.gov/api/data/?UserID='+self.apiKey+'&method=GetData&datasetname=IIP&TypeOfInvestment='+str(TypeOfInvestment)+'&Component='+str(Component)+'&Year='+str(Year)+'&Frequency='+str(Frequency)+'&ResultFormat=JSON&'
        r = requests.get(uri)
        rJson = r.json()

        columnNames = []
        dates = []
        try:
            for element in rJson['BEAAPI']['Data']:
                if element['TimeSeriesDescription'] not in columnNames:
                    columnNames.append(element['TimeSeriesDescription'])

                date = convertDate(element['TimePeriod'],Frequency)
                if date not in dates:
                    dates.append(date)

            data = np.zeros([len(dates),len(columnNames)])
            data[:] = np.nan
            frame = pd.DataFrame(data,columns = columnNames, index = dates)

            for element in rJson['BEAAPI']['Data']:
                date = convertDate(element['TimePeriod'],Frequency)
                if len(element['DataValue'].replace(',','')) ==0:
                    frame.loc[date,element['TimeSeriesDescription']] = np.nan
                else:
                    frame.loc[date,element['TimeSeriesDescription']] = float(element['DataValue'].replace(',',''))
            
            frame = frame.sort_index()
            units  = rJson['BEAAPI']['Data'][0]['CL_UNIT']
            mult = rJson['BEAAPI']['Data'][0]['UNIT_MULT']
            if int(mult) == 3:
                units = 'Thousands of '+units
            elif int(mult) == 6:
                units = 'Millions of '+units
            elif int(mult) == 9:
                units = 'Billions of '+units

            return {'note':units,'date':frame}

        except:
            print('Error: invalid input.')



    # 3.9 Regional Income: detailed regional income and employment data sets.

    def getRegionalIncome(self,TableName=None,LineCode=None,GeoFips=None,Year ='ALL'):

        '''GeoFips can equal STATE
COUNTY
MSA
MIC
PORT
DIV
CSA'''

        uri = 'http://bea.gov/api/data/?UserID='+self.apiKey+'&method=GetData&datasetname=RegionalIncome&TableName='+str(TableName)+'&LineCode='+str(LineCode)+'&Year='+str(Year)+'&GeoFips='+str(GeoFips)+'&ResultFormat=JSON&'
        r = requests.get(uri)
        rJson = r.json()

        columnNames = []
        dates = []
        Frequency = 'A'
        try:
            for element in rJson['BEAAPI']['Results']['Data']:
                if element['GeoName'] not in columnNames:
                    columnNames.append(element['GeoName'])

                date = convertDate(element['TimePeriod'],Frequency)
                if date not in dates:
                    dates.append(date)

            data = np.zeros([len(dates),len(columnNames)])
            data[:] = np.nan
            frame = pd.DataFrame(data,columns = columnNames, index = dates)

            for element in rJson['BEAAPI']['Results']['Data']:
                date = convertDate(element['TimePeriod'],Frequency)
                if len(element['DataValue'].replace(',','')) ==0:
                    frame.loc[date,element['GeoName']] = np.nan
                else:
                    frame.loc[date,element['GeoName']] = float(element['DataValue'].replace(',',''))
            frame = frame.sort_index()

            units = rJson['BEAAPI']['Results']['UnitOfMeasure']

            return {'notes':units,'data':frame}

        except:

                print('Error: invalid input.')


    # 3.10 Regional product: detailed state and MSA product data sets

    def getRegionalProduct(self,Component=None,IndustryId=1,GeoFips='State',Year ='ALL'):

        '''GeoFips can equal either STATE or MSA'''

        uri = 'http://bea.gov/api/data/?UserID='+self.apiKey+'&method=GetData&datasetname=regionalProduct&Component='+str(Component)+'&IndustryId='+str(IndustryId)+'&Year='+str(Year)+'&GeoFips='+str(GeoFips)+'&ResultFormat=JSON&'
        r = requests.get(uri)
        rJson = r.json()

        columnNames = []
        dates = []
        Frequency = 'A'
        try:
            for element in rJson['BEAAPI']['Results']['Data']:
                if element['GeoName'] not in columnNames:
                    columnNames.append(element['GeoName'])

                date = convertDate(element['TimePeriod'],Frequency)
                if date not in dates:
                    dates.append(date)

            data = np.zeros([len(dates),len(columnNames)])
            data[:] = np.nan
            frame = pd.DataFrame(data,columns = columnNames, index = dates)

            for element in rJson['BEAAPI']['Results']['Data']:
                date = convertDate(element['TimePeriod'],Frequency)
                if len(element['DataValue'].replace(',','')) ==0:
                    frame.loc[date,element['GeoName']] = np.nan
                else:
                    frame.loc[date,element['GeoName']] = float(element['DataValue'].replace(',',''))
            
            frame = frame.sort_index()
            note = rJson['BEAAPI']['Results']['Data'][0]['CL_UNIT']

            return {'note':note,'date':frame}

        except:

                print('Error: invalid input.')


# Auxiliary function.

        
def convertDate(dateString,Frequency):

    '''Function for converting the date strings from BEA with quarter indicators into datetime format'''

    if Frequency=='A':
        month='01'
    elif Frequency=='Q':
        if dateString[-1]=='1':
            month='01'
        elif dateString[-1]=='2':
            month='04'
        elif dateString[-1]=='3':
            month='07'
        else:
            month='10'
    return datetime.datetime.strptime(dateString[0:4]+'-'+month+'-01','%Y-%m-%d')