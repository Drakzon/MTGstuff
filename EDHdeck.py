import bs4 as bs
import urllib.request
import xml.dom.minidom
import re
import numpy as np
import pickle
import csv
import os
import unicodedata

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
        
def GrabEDHREC():   
    'Function goes through and grabs the average deck for each commander on EDHrec'
    
    savefilename = 'EDHrec'

    sauce = urllib.request.urlopen('https://edhrec.com/commanders').read()
    soup = bs.BeautifulSoup(sauce,'lxml')
    nav=soup.nav
    commanderColoursLinkListRaw = nav.find_all('a', href=re.compile('/commanders/'))
    commanderColoursLinkList = []

    for a in range(len(commanderColoursLinkListRaw)):
        commanderColoursLinkList.append(commanderColoursLinkListRaw[a].attrs['href'])
#        print(commanderLinkList[a].split('/')[2])
    
    Decks = {}    


 
    for b in range(len(commanderColoursLinkList)):
        sauce = urllib.request.urlopen('https://edhrec.com/commanders/' + commanderColoursLinkList[b].split('/')[2]).read()
        soup = bs.BeautifulSoup(sauce,'lxml')
        
        CommanderLinks = GrabCommanders(soup)
        
        for c in range(len(CommanderLinks)):
            sauce = urllib.request.urlopen('https://edhrec.com/decks/' + CommanderLinks[c]).read()
            soup = bs.BeautifulSoup(sauce,'lxml')
                
            General = soup.h3.text
            print(General)
            Deck = GrabDecklist(soup)
            Decks[General] = Deck

    np.save(savefilename + '.npy', Decks)
    return(Decks)
    
def GrabCommanders(soup):
    CommanderlistXML = soup.find_all('div',class_="nw")
    CommanderList = []
    for c in range(len(CommanderlistXML)):
        if CommanderlistXML[c].find('a',href=re.compile('/commanders/')):
            CommanderList.append(CommanderlistXML[c].find('a',href=re.compile('/commanders/')).attrs['href'].split('/')[2])
#            print(CommanderList)
    return(CommanderList)
    
def GrabDecklist(soup):
    "Grab decklist from Beautiful soup object of edhrec page"
    DecklistXML = soup.find('div',class_="container well").text
    temp = '1'
    SplitXML = re.split('1 |2 |3 |4 |5 |6 |7 |8 |9 |0', DecklistXML)
    SplitXML2 =''.join(i for i in SplitXML if not i.isdigit())
#    SplitXML3 = remove_accents(SplitXML2)
    Numbers = re.findall(r'\d+', temp + DecklistXML)
    Decklist = [list(x) for x in zip(Numbers, SplitXML2)]
    return(Decklist)
    
def GetPriceManaleak(card):
    "Gets a price from manaleak"
    
    sauce = urllib.request.urlopen('http://www.manaleak.com/magic-the-gathering/advanced_search_result.php?keywords=' + card.replace(" ", "+")).read()
    soup = bs.BeautifulSoup(sauce,'lxml')

    cardPrices = soup.find('', class_="content t_view")
    priceTemp = cardPrices.find_all('div',class_="product_price_wrapper")
    pricelist = []

    for prices in priceTemp:
        PricewCurr = prices.find('span').text
        PricenoCurr = PricewCurr.split('£')[1]
        pricelist.append(float(PricenoCurr))
    return(min(pricelist))

    
    
#class Deck:
#    "A Class to hold deck info"
#    
#    def __init__(self):
#    self.decklist = []
    
    

# load EDHrec
if not os.path.isfile('EDHrec.pickle'):
    print('Running GrabEDHREC, may take a while')
    decks = GrabEDHREC()
    pickle.dump(Decks, open("EDHrec.pickle", "wb"))
else:
    print('Loading EDHrec.pickle')
    decks = pickle.load(open("EDHrec.pickle", "rb"))

                    
# set up collection
print('Importing inventory...')
collection = []
collectionSupply = []
InventoryFile = 'inventory.csv'
if not os.path.isfile(InventoryFile):
    print('[ERROR] File not found: inventory.csv. Please make sure your'
          + ' inventory.csv file is in the same directory as this script.'
          + '\nIf you do not have an inventory.csv, you can export one'
          + ' from deckbox.org (make sure you rename it to inventory.csv)')
    exit()
invFile = open(InventoryFile)
invReader = csv.reader(invFile)

for row in invReader:
    if len(row) == 0:
        break
    collection.append(row[2])
    collectionSupply.append(row[0])

invFile.close()              
              
GeneralList = []
for key in decks.keys(): 
    if "Commander Analysis" not in key:
#        print(key)
        GeneralList.append(key)

score = {}
score2 = {}
OwnedCards = {}
MissingCards = {}
TotalCards = {}
#
print('Pricing')
    
for EDHDeck in GeneralList: 
    OwnedCards[EDHDeck] = 0
    TotalCards[EDHDeck] = 0
    MissingCards[EDHDeck] = []
    score[EDHDeck] = 0
    pricetocomplete = 0
    print(EDHDeck)
    for card in decks[EDHDeck]:
        card[1] = remove_accents(''.join(i for i in card[1] if not i.isdigit()))
        TotalCards[EDHDeck] += 1
        if card in collection:
#           print('Own ' + card[1])
           OwnedCards[EDHDeck] += 1
        else:
            print('Missing ' + card[1])
            MissingCards[EDHDeck].append(card)
            pricetocomplete += GetPriceManaleak(card[1])
    score[EDHDeck] = OwnedCards[EDHDeck]/TotalCards[EDHDeck]
    score2[EDHDeck] = pricetocomplete
    print('Deck: ' + EDHDeck + 'would cost around £' + str(round(pricetocomplete)) + ' to complete')

    
SortedScores = sorted(score.items(), key=lambda x: x[1], reverse=True)
SortedPrices = sorted(score.items(), key=lambda x: x[1], reverse=True)

#for A in SortedScores:
#    print(A)
    
with open('Scores.csv','w', newline='') as out:
    csv_out=csv.writer(out)
    csv_out.writerow(['Deck','Completion Factor'])
    for row in SortedScores:
        csv_out.writerow(row)
      
with open('Prices.csv','w', newline='') as out:
    csv_out=csv.writer(out)
    csv_out.writerow(['Deck','Cost to complete'])
    for row in SortedPrices:
        csv_out.writerow(row)
        
print('Finished')


#Deck = GeneralList[40]
#EDHDeck = 'Yidris, Maelstrom Wielder'
#
#OwnedCards[EDHDeck] = 0
#TotalCards[EDHDeck] = 0
#MissingCards[EDHDeck] = []
#score[EDHDeck] = 0
#score2[EDHDeck] = 0
#for card in decks[EDHDeck]:
#    TotalCards[EDHDeck] += 1
#    if card[1] in collection:
##       print('Own ' + card[1])
#      OwnedCards[EDHDeck] += 1
#    else:
##        print('Missing ' + card[1])
#        MissingCards[EDHDeck].append(card)
#        score2[EDHDeck] += GetPriceManaleak(card[1])
#        print(card[1])
#score[EDHDeck] = OwnedCards[EDHDeck]/TotalCards[EDHDeck]
#
#
#print(score[EDHDeck])
#print(score2[EDHDeck])


#cardprice = GetPriceManaleak(card)








