"""
GG_Parser.py: Generates a json of Girl Genius comics, along with current chapter name and links to next/previous comics.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from bs4 import BeautifulSoup as bs
from time import sleep
from random import randint
import json

def myReq() -> requests.session:
    sessionObj = requests.session()
    retries = Retry(total=5, backoff_factor=60, status_forcelist=[502,503,504])
    sessionObj.mount('http://', HTTPAdapter(max_retries=retries))
    sessionObj.mount('https://', HTTPAdapter(max_retries=retries))
    return sessionObj

# Define a special selector. Use this to find the chapter name of the current comic. 
def selectedDropdownOption(tag):
    return tag.name == "option" and tag.has_attr("selected")

# Our core mechanic. Returns all the necessary parts of a comic page.
def getGGPageElements(targetUrl) -> dict:
    print(targetUrl)
    try:
        targetPage = myReq().get(targetUrl)
        targetPage.raise_for_status()
    except requests.exceptions.HTTPError as err: 
        print(err)
        return 0

    bsParsedPage = bs(targetPage.content, 'html.parser')
    
    #! TO DO: Keep writing, look for ways to parse pages that have multiple comics. Use 
    # https://www.girlgeniusonline.com/comic.php?date=20041001 as an example case.
    # More studying! OK so we know that all main panel images are gonna have alt='Comic' as the tag.
    # We use a .findAll(alt='Comic') to return a list of bs4.element.Tag objects, then we use a len() 
    # to determine if we need a for-loop to return a list of 'href' attributes for each object.
    findComicImages = bsParsedPage.findAll(alt='Comic')

    comicImgList = []
    if len(findComicImages) > 1:
        # We engage some multi-mode processing here.
        for i in findComicImages:
            comicImgList.append(i['src'])  #! uh, does this need to be "src" instead?
    elif len(findComicImages) == 1:
        # We just need the one thing.
        comicImgList.append(['src'])
    else:
        comicImgList.append('No Comics Found!')

    # Lets get the chapter name!
    dropdownOptions = bsParsedPage.find_all(selectedDropdownOption)
    chapterName = (dropdownOptions[0]).get_text()
    
    # Find our current location, next, and previous comics.
    currentComicDate = targetUrl.split('=')[-1]
    findNextComic = bsParsedPage.find(id='topnext')
    findPreviousComic = bsParsedPage.find(id='topprev')
    if not findNextComic:
        returnNextUrl = ''
    else:
        returnNextUrl = findNextComic['href']
    if not findPreviousComic:
        returnPrevUrl = ''
    else:
        returnPrevUrl = findPreviousComic['href']

    # Return results.
    composedDict = {
        'currentComicDate' : currentComicDate, 
        'chapterName' : chapterName, 
        'nextComicUrl' : returnNextUrl, 
        'prevComicUrl' : returnPrevUrl, 
        'comicImgList' : (comicImgList).sort()
            }
    return composedDict

def buildComicDataStructure():
    # Comic begins here
    nextPage = "https://www.girlgeniusonline.com/comic.php?date=20021104"
    completeComicIndex = []
    while nextPage:
        try:
            targetPage = getGGPageElements(nextPage)
        except Exception:
            print("Unable to retrieve page. Check connection and try again.")
            break
        sleep(randint(15,30))
        completeComicIndex.append(targetPage)
        if targetPage['nextComicUrl']:
            nextPage = targetPage['nextComicUrl']
        else:
            nextPage = False
    return completeComicIndex
        
def main():
    # do the thing.
    outputJsonStructure = buildComicDataStructure()
    with open('ggStructure.json', 'w') as outputFile:
            json.dump(outputJsonStructure, outputFile)

if __name__ == "__main__":
    main()