# Restaurant Library

## Description
Welcome to Restaurant Library! This project is designed to help users find the best, most tailored restaurants near them using a combination of Google's API, web scraping techniques, and AI. Whether you're looking for a cozy café, a fine dining experience, or a quick bite, Restaurant Library has you covered.

## Disclaimer
This project was created for educational purposes only. The code is not intended for commercial use.

## Files 
- 'getSimilarRestaurants.py' - This file contains the code to get similar restaurants based on the user's location and restaurants entered by the user.
- 'getBestFitRestaurant.py' - This file contains the code to get the best fit restaurant based on the restaurants entered by the user.

## Installation
To run this project, you will need to install the following libraries:
    pip install requests 
    pip install selenium
    pip install beautifulsoup4
    pip install python-dotenv

You will also need to have a Google API key. You can get one by following the instructions here: https://developers.google.com/maps/documentation/javascript/get-api-key

## Usage
To use this project, you will need to run the following command in your terminal:
    python getSimilarRestaurants.py
    python getBestFitRestaurant.py
In each of the files you can enter the restaurants you are interested in and your dedicated location in the 'userLocation' and 'restaurantName' variables.

