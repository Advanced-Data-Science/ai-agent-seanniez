Project Overview  
  
This project seeks to design an intelligent data collection agent that leverages APIs dealing  
with economic and stock data. In this project, 2 APIs are used (in accordance with the DMP)  
those are the FRED API from the Federal Reserve, as well as the Alpha Vantage API. 
  
The program employs intelligent and respectful data fetching practices. During the data requ-  
esting stage, the program keeps track of the success rate, that being the rate at which series'  
are satisfactorily collected. If the success rate is too low, delays are increased to reduce the  
chances of hitting rate limits. If the success rate is high, delays are reduced and the data is  
collected more quickly.
  
The config file houses user-defined information that is crucial to the agent's functionality. At   
the top, the user may input the series' they wish to pull data for. It will be necessary to provide  
the name of the API that will be providing this data.  
  
Below this, there are lines defining a dummy keys for each API. While the program is running,  
the actual keys are pulled from a .env file that the user will need to create and then declare in  
.gitignore. Further, the config file requires that the user input the starting date for which the data  
is to be pulled, as well as the end date. Finally, the base delay is defined to have a delay between  
each API request.  
  
The program will then process the raw data by normalizing values and data types, storing the data  
at each processing stage in respective directories. At the end of data collection and processing, reports  
are generated, describing the overall quality of the data, as well as the performance of each API.