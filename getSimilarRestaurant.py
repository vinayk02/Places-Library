import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from dotenv import dotenv_values
env_values = dotenv_values(".env")
google_places_api_key = env_values['GOOGLE_API_KEY']


#function to get the user's current location
def getUserCoordinates(usersLocation):
    url = "https://maps.googleapis.com/maps/api/geocode/json?address=" + usersLocation + "&key=" + google_places_api_key
    response = requests.get(url)
    data = response.json()
    userLat = data['results'][0]['geometry']['location']['lat']
    userLng = data['results'][0]['geometry']['location']['lng']
    return userLat, userLng
    
browser = webdriver.Chrome()
#function to get the details of a restaurant
def getRestaurantDetails(restaurantName, knownPlaceId, placeId = None):
    restaurantPriceLevel = 2
    restaurantRating = 0
    if(knownPlaceId == False):
        url ="https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input=" + restaurantName + "&inputtype=textquery&fields=place_id&key=" + google_places_api_key
        responseForPlaceId = requests.get(url)
        dataForPlaceId = responseForPlaceId.json()
        
        placeId = dataForPlaceId['candidates'][0]['place_id']
        url = "https://maps.googleapis.com/maps/api/place/details/json?place_id=" + placeId + "&fields=name,rating,formatted_phone_number,website,price_level,opening_hours,types,geometry&key=" + google_places_api_key
        responseGoogleDetails = requests.get(url)
        dataGoogleDetails = responseGoogleDetails.json()
        #get the restaurant's name, priceLevel, rating,
        restaurantName = dataGoogleDetails['result']['name'] 
        if('priceLevel' in dataGoogleDetails['result']):
            restaurantPriceLevel = dataGoogleDetails['result']['price_level']
        restaurantRating = dataGoogleDetails['result']['rating']
   
   #scrape google maps for the restaurant's details
    browser.get("https://www.google.com/maps/search/?api=1&query=Google&query_place_id=" + placeId)
    cuisineButton = browser.find_element(By.CLASS_NAME, "DkEaL")
    cuisine = cuisineButton.text
    #use the data-tab-index to find the button
    xpath = f"//button[@data-tab-index='2']"
    buttonElementFound =  browser.find_element(By.XPATH, xpath)
   #click the button to get the restaurant's details
    buttonElementFound.click()
    time.sleep(0.5)
 
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    allSections= soup.find_all("div", {"class": "iP2t7d fontBodyMedium"})
    requiredSections = []
    #setup the arrays for the restaurant's details
    highlights = []
    offerings = []
    atmosphere = []
    crowd = []
    #get the h2 element and make sure it is either "Highlights", "Offerings", "Atmosphere", or "Crowd"
    for section in allSections:
        #get the h2 element and make sure it is either "Highlights", "Offerings", "Atmosphere", or "Crowd"
        sectionSoup = BeautifulSoup(str(section), 'html.parser')
        h2 = sectionSoup.find_all("h2", {"class": "iL3Qke fontTitleSmall"})
        h2 = h2[0].text
        if(h2 == "Highlights" or h2 == "Offerings" or h2 == "Atmosphere" or h2 == "Crowd"):
            requiredSections.append(section)

    #get the text of the spans in the required sections
    for section in requiredSections:
        sectionSoup = BeautifulSoup(str(section), 'html.parser')
        if(sectionSoup.find_all("h2", {"class": "iL3Qke fontTitleSmall"})[0].text == "Highlights"):
            highlightsFound = sectionSoup.find_all("span")
            for highlight in highlightsFound:
                highlights.append(highlight.text)
        elif(sectionSoup.find_all("h2", {"class": "iL3Qke fontTitleSmall"})[0].text == "Offerings"):
            offeringsFound = sectionSoup.find_all("span")
            for offering in offeringsFound:
                offerings.append(offering.text)
        elif(sectionSoup.find_all("h2", {"class": "iL3Qke fontTitleSmall"})[0].text == "Atmosphere"):
            atmosphereFound = sectionSoup.find_all("span")
            for atmos in atmosphereFound:
                atmosphere.append(atmos.text)
        elif(sectionSoup.find_all("h2", {"class": "iL3Qke fontTitleSmall"})[0].text == "Crowd"):
            crowdFound = sectionSoup.find_all("span")
            for c in crowdFound:
                crowd.append(c.text)
    return {"cuisine": cuisine, "highlights": highlights, "offerings": offerings, "atmosphere": atmosphere, "crowd": crowd, "rating": restaurantRating, "priceLevel": restaurantPriceLevel}
   
 
#function to gather all restaurants details and create weights for each attribute
def combineRestaurantDetails(restaurantsAttributes):
    #setup the objects for the user's weights
    atmosphere = {}
    crowd = {}
    offerings = {}
    cuisine = {}
    highlights = {}
    total_rating = 0
    total_price = 0
    for restaurant in restaurantsAttributes:
        for atmos in restaurant['atmosphere']:
            if atmos in atmosphere:
                atmosphere[atmos] += 1
            else:
                atmosphere[atmos] = 1

        for c in restaurant['crowd']:
            if c in crowd:
                crowd[c] += 1
            else:
                crowd[c] = 1

        for offering in restaurant['offerings']:
            if offering in offerings:
                offerings[offering] += 1
            else:
                offerings[offering] = 1

        if restaurant['cuisine'] in cuisine:
            cuisine[restaurant['cuisine']] += 1
        else:
            cuisine[restaurant['cuisine']] = 1

        for highlight in restaurant['highlights']:
            if highlight in highlights:
                highlights[highlight] += 1
            else:
                highlights[highlight] = 1
        total_rating += restaurant['rating']
        total_price += restaurant['priceLevel']
    
    #setup the weights for the user's attributes
    totalRestaurants = len(restaurantsAttributes)
    averagePrice = total_price/totalRestaurants
    averageRating = total_rating/totalRestaurants
    for atmos in atmosphere:
        atmosphere[atmos] = atmosphere[atmos]/totalRestaurants
    for c in crowd:
        crowd[c] = crowd[c]/totalRestaurants
    for offering in offerings:
        offerings[offering] = offerings[offering]/totalRestaurants
    for c in cuisine:
        cuisine[c] = cuisine[c]/totalRestaurants
    for highlight in highlights:
        highlights[highlight] = highlights[highlight]/totalRestaurants

    return {"cuisine": cuisine, "highlights": highlights, "offerings": offerings, "atmosphere": atmosphere, "crowd": crowd, "rating": averageRating, "price": averagePrice}


#function to get nearby restuarants that  are similar to the user's selected restaurants
def getNearbyRestaurants(userLat, userLng, userWeights):
    preferredCuisines = []
    restaurantsFound = []
    filteredRestaurants = []
    if(userWeights != None):
        for cuisine in userWeights['cuisine']:
            if(userWeights['cuisine'][cuisine] >= 0.3):
                preferredCuisines.append(cuisine)

    url = ""
    if(len(preferredCuisines) == 0):
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=" + str(userLat) + "," + str(userLng) + "&radius=1500&type=restaurant&key=" + google_places_api_key
        response = requests.get(url)
        data = response.json()
        #get all the restaurants found
        for restaurant in data['results']:
            priceLevel = 2
            if('price_level' in restaurant):
                priceLevel = restaurant['price_level']            
            restaurantsFound.append({'placeId': restaurant['place_id'], 'name': restaurant['name'], 'rating': restaurant['rating'], 'priceLevel': priceLevel})
    else:
        for cuisine in preferredCuisines:
            url += "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=" + str(userLat) + "," + str(userLng) + "&radius=1500&type=restaurant&keyword=" + cuisine + "&key=" + google_places_api_key
            response = requests.get(url)
            data = response.json()
            #get all the restaurants found
            for restaurant in data['results']:
                priceLevel = 2
                if('price_level' in restaurant):
                    priceLevel = restaurant['price_level']
                restaurantsFound.append({'placeId': restaurant['place_id'], 'name': restaurant['name'], 'rating': restaurant['rating'], 'priceLevel': priceLevel})

    tempRestaurants =  restaurantsFound
    for restaurant in tempRestaurants:
        #remove the restaurants that are more expensive than the user's weights

        if(restaurant['priceLevel'] > userWeights['price'] ):
            restaurantsFound.remove(restaurant)
    tempRestaurants = restaurantsFound
    #check if the restuarant have the same offerings, atmosphere, cuisine, crowd, and highlights as the user's weights
    for restaurant in tempRestaurants:
        restaurantName = restaurant['name']
        restaurantPlaceId = restaurant['placeId']
        restaurantRating = restaurant['rating']
        restaurantPrice = restaurant['priceLevel']
        #get the rest of the details using the detail fetch function
        restaurantAttributes = getRestaurantDetails(restaurantName, True, restaurantPlaceId)
        restaurantCuisine = restaurantAttributes['cuisine']
        restaurantHighlights = restaurantAttributes['highlights']
        restaurant_offerings = restaurantAttributes['offerings']
        restaurantAtmosphere = restaurantAttributes['atmosphere']
        restaurantCrowd = restaurantAttributes['crowd']        
        #compare the results to the user's weights
        for atmos in userWeights['atmosphere']:
            #if a certain atmosphere in the user weights is > .5, make sure the restaurant has that atmosphere
             if(userWeights['atmosphere'][atmos] >= 0.7):
                if(atmos not in restaurantAtmosphere):
                    restaurantsFound.remove(restaurant)
                    break
        for c in userWeights['crowd']:
            if( userWeights['crowd'][c]>= 0.7):
                if(c not in restaurantCrowd):
                    if(restaurant in restaurantsFound):                     
                        restaurantsFound.remove(restaurant)
                        break
        for offering in userWeights['offerings']:
            if(userWeights['offerings'][offering] >= 0.7):
                if(offering not in restaurant_offerings):
                    if(restaurant in restaurantsFound):                    
                        restaurantsFound.remove(restaurant)
                        break
        if(restaurantCuisine not in userWeights['cuisine']):
            if(restaurant in restaurantsFound):
                restaurantsFound.remove(restaurant)
                break
        for highlight in userWeights['highlights']:
            if(userWeights['highlights'][highlight] >= 0.7):
                if(highlight not in restaurantHighlights):
                    if(restaurant in restaurantsFound): 
                        restaurantsFound.remove(restaurant)
                        break
        similarityPercentage = calculateSimilarityScore(userWeights, restaurantAttributes)
        filteredRestaurants.append({'name': restaurantName, 'placeId': restaurantPlaceId, 'rating': restaurantRating, 'priceLevel': restaurantPrice, 'similarity': similarityPercentage})
    
    filteredRestaurants.sort(key=lambda x: x['similarity'], reverse=True)
    return filteredRestaurants

#function to calculate the similarity score of the user's selected restaurants and the nearby restaurants
def calculateSimilarityScore(userWeights, suggestedRestaurant):
    similarityPercentage = 0
    #setup the variables for the similarity score
    atmosphereTotalScore = 0
    crowdTotalScore = 0
    offeringsTotalScore = 0
    cuisineTotalScore = 0
    highlightsTotalScore = 0
    atmosphereWeight = 0
    crowdWeight = 0
    offeringsWeight = 0
    cuisineWeight = 0
    highlightsWeight = 0
    
    #calculate the total score and weight for each attribute
    for atmos in userWeights['atmosphere']:
        atmosphereWeight += userWeights['atmosphere'][atmos]
        if(atmos in suggestedRestaurant['atmosphere']):
            atmosphereTotalScore += userWeights['atmosphere'][atmos]
    for c in userWeights['crowd']:
        crowdWeight += userWeights['crowd'][c]
        if(c in suggestedRestaurant['crowd']):
            crowdTotalScore += userWeights['crowd'][c]
    for offering in userWeights['offerings']:
        offeringsWeight += userWeights['offerings'][offering]
        if(offering in suggestedRestaurant['offerings']):
            offeringsTotalScore += userWeights['offerings'][offering]
    for c in userWeights['cuisine']:
        cuisineWeight += userWeights['cuisine'][c]
        if(c in suggestedRestaurant['cuisine']):
            cuisineTotalScore += userWeights['cuisine'][c]
    for highlight in userWeights['highlights']:
        highlightsWeight += userWeights['highlights'][highlight]
        if(highlight in suggestedRestaurant['highlights']):
            highlightsTotalScore += userWeights['highlights'][highlight]

    #calculate the similarity percentage
    similarityPercentage = (((atmosphereTotalScore/atmosphereWeight) + (crowdTotalScore/crowdWeight) + (offeringsTotalScore/offeringsWeight) + (cuisineTotalScore/cuisineWeight) + (highlightsTotalScore/highlightsWeight)) / 5) * 100
    return similarityPercentage


        
        
    


 
#main function
def getSimilarRestaurant():
    #enter the user's location
    userLocation = "1 World Trade Center, New York, NY 10007, USA"
    userLat, userLng = getUserCoordinates(userLocation)
    userWeights = None
    #Enter the names of the restaurants that the user is interested in
    restaurantName = ["Efes Mediterranean Grill","Sahara Restaurant","Laila Restaurant And Lounge"]
    restaurantsAttributes = []
    index = 0
    for restaurant in restaurantName:
        restaurantAttributes = getRestaurantDetails(restaurantName[index], False, restaurant)
        restaurantsAttributes.append(restaurantAttributes)
        index = index + 1    
    userWeights = {}
    userWeights = combineRestaurantDetails(restaurantsAttributes)
    similarRestaurants = getNearbyRestaurants(userLat, userLng, userWeights)
    print(similarRestaurants)





if __name__ == "__main__":
    getSimilarRestaurant()






