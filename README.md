![alt text](https://upload.wikimedia.org/wikipedia/en/thumb/f/f2/Premier_League_Logo.svg/1200px-Premier_League_Logo.svg.png)

# Improving EPL Betting Odds leveraging on social data and statistics
This is the course project for the Unstructured and Streaming Data Engineering (USDE) Course @ Politecnico di Milano.
The purpose of this project is trying to predict the outcome of the English Premier League matches of season 2018/2019, using several sources of information:

- betting odds
- soccer statistics
- social media data

The final model is able to cosiderably improve the accuracy of the betting odds.

The code is organized as follows:

- **dataset**: the dataset folders contains the CSVs extracted from the scraping and data gathering phases together with a few scripts used to transform the dataset in order to be used for creating models.
- **notebooks**: this folder contains the notebooks used to clean, analyze and prepare the data and also the ones with the actual running models.
- **scrapers**: in this folder there are the scrapers or scripts used to gather the data and also the CSVs extracted from the social networks (Twitter and Facebook). Note that the scrapers might not be working since the pages could have been slightly changed since when the data was extracted.

