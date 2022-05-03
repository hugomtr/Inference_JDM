import requests
from bs4 import BeautifulSoup
import re, csv
import numpy as np
import os.path, sys
import pandas as pd


# User prompt
inputTermA = input("Entrez un premier terme: \n")
inputTermB = input("Entrez un second terme: \n")

print("\n   ##################################################################\n\
 |  Tapez (6) pour une inférence déductive (relation is_a)           |\n \
|  Tapez (9) ou (28) pour une inférence transitive (r_lieu,haspart..)|\n \
|  Tapez (8) pour une inférence inductive (relation r_holo)         |\n\
   ##################################################################\n\n")

inputRelation = input("Entrez une relation sémantique entre les deux précédents termes: \n")

while (inputRelation not in ['6','8','9','28']):
    inputRelation = input("Erreur, veuillez rentrer un numéro d'inférence valide: \n")

correspondance = {'6': "deductive inference", '9': "transitive inference", '28': "transitive inference", '8':"inductive inference", }

print(f"Asking system for a {correspondance[inputRelation]} between \"{inputTermA}\" and \"{inputTermB}\"...")


# Preprocessing
def getPreprocessedKB(iA, iR):

    inputTermA = iA
    inputRelation = iR

    filenameEntry = f"{inputTermA}_KBE.csv"
    filenameRelation = f"{inputTermA}_KBR.csv"

    # Parsing of the JDM lexical network DUMP on a given input Term
    if(inputRelation == '6'):
        vgm_url = f'http://www.jeuxdemots.org/rezo-dump.php?gotermsubmit=Chercher&gotermrel={inputTermA}&rel='
    else:
        vgm_url = f'http://www.jeuxdemots.org/rezo-dump.php?gotermsubmit=Chercher&gotermrel={inputTermA}&rel={inputRelation}'

    html_text = requests.get(vgm_url).text
    soup = BeautifulSoup(html_text, 'html.parser')

    # Taking everything starting from the code balise
    page = soup.find('code').getText()

    # RegEx patterns for preprocessing 
    commentsPattern = "^\/\/ *.*"
    behindNodePattern = "(?s)^.*?(?=e;eid)"
    behindNodePatternRelations = "(?s)^.*?(?=r;rid)"
    blankLinesPattern = "^\s*$"
    getSortant = "(?s)(r;[0-9]).*?(?=\n\n)"

    # ENTRIES PREPROCESSING
    prepro1 = re.sub(behindNodePattern, '', page) # Delete all what's behind the first nodes e;[...]
    prepro2 = re.sub(commentsPattern, '', prepro1, flags=re.MULTILINE) # Delete all the comments (whitespace can be seen as \s in regex.) 
    prepro3 = re.sub("((r;.*)|(rt;.*))", '', prepro2) # Delete relations, relations types, blank lines
    entries = re.sub(blankLinesPattern, '', prepro3, flags=re.MULTILINE) 
    # print(entries) 

    # RELATIONS PREPROCESSING
    pp1 = re.sub(behindNodePatternRelations, '', page)
    pp2 = re.sub(behindNodePatternRelations, '', pp1)
    pp3 = re.sub(commentsPattern, '', pp1, flags=re.MULTILINE)
    reg = re.search(getSortant, pp3)

    relations = ""
    try:
        relations = "r;rid;node1;node2;type;w\n" + reg.group(0)
    except AttributeError:
        pass

    # pp1 = re.sub(behindNodePatternRelations, '', page)
    # relations = re.sub(commentsPattern, '', pp1, flags=re.MULTILINE)

    # Debug to redirect to a log file
    # print(page) 

    # Make this as a list
    textEntry = entries.split("\n")
    textRelation = relations.split("\n")

    # Removing single quote from the list
    for singleQuote in range(0,len(textEntry)):
        textEntry[singleQuote] = textEntry[singleQuote].replace("'","")

    for singleQuote in range(0,len(textRelation)):
        textRelation[singleQuote] = textRelation[singleQuote].replace("'","")


    # Convert raw data into semi-structured data (in this case csv format file) and save it.
    np.savetxt(filenameEntry, textEntry, delimiter =",", fmt ='%s')
    np.savetxt(filenameRelation, textRelation, delimiter =",", fmt ='%s')

    dfEntry = pd.read_csv(filenameEntry, on_bad_lines='skip', delimiter=';')
    dfRelation = pd.read_csv(filenameRelation, on_bad_lines='skip', delimiter=';')

    return dfRelation, dfEntry # not the purpose of the function but need them outside of the function (return a tuple)



dfRelation, dfEntry = getPreprocessedKB(inputTermA, inputRelation)
solutionFound = 0


#####################################################
##################### DEDUCTION #####################
#####################################################


if(inputRelation == '6'):


    # The number of generics for a given inputTermA
    nbGenerics = len(dfRelation.loc[dfRelation['type']==6].node2) 

    # To iterate on the highest weights
    # dfRelation['w'].sort_values(ascending=False)

    # All the "is-a" (type=6) relations of the term given in input (for DEDUCTIVE INFERENCE)
    # For each generic of our input term, we check all their r_agent (type=24) and see if it corresponds to the input termB 
    for i in range(nbGenerics):
        
        # We take all the generics of our inputTerm.
        # We look at each entry of our term whose id is in the relation dataframe of that term and that satisfies the condition bellow
        # i.e correspondance between id in dfE and dfR
        # test for specific here also?
        genericDF = dfEntry[dfEntry['eid'] == dfRelation[(dfRelation['type']==6) & (dfRelation['w']>0)] .node2.iloc[i]]

        # Just retrieve its name from the generic DataFrame
        genericName = genericDF.name.values[0]
        
        print(f"\nTaking into account:\n{genericDF} \n")

        fileNameR = f"{genericName}_KBR.csv"
        fileNameE = f"{genericName}_KBE.csv"
        file_existsR = os.path.exists(fileNameR)
        file_existsE = os.path.exists(fileNameE)


        # Avoid making queries each time we want to use our system
        if (file_existsR == True & file_existsE == True):
            print("File exists, processing...")
            try:
                dfTermE = pd.read_csv(fileNameE, on_bad_lines='skip', delimiter=';')
                dfTermR = pd.read_csv(fileNameR, on_bad_lines='skip', delimiter=';')
            except:
                pass

            # Test if dataset empty, it can indeed be, because sometimes beautifulsoup fails to parse some terms
            if(dfTermR.empty):
                continue

            # We take all the id's of the r_agent relation of the generic
            indexOfInterest = dfTermR.loc[dfTermR['type']==24].node2.values 

            # We search for all the r_agent relations of the first generic (index i)
            for j in range(len(dfTermR.loc[dfTermR['type']==24])):
                # At the first matching with the termB (e.g voler), then it succeeds
                if(dfTermE.loc[dfTermE['eid']==indexOfInterest[j]].name.values[0] == inputTermB):
                    solutionFound += 1
                    print(f"\n\n->Answer : Un(e) {inputTermA} est un(e) {genericName} et un(e) {genericName} peut {inputTermB}. Donc un(e) {inputTermA} PEUT {inputTermB}.")
                    sys.exit("A solution has been encountered, program finished.")                 
                # Otherwise if none of them match then we can infer it's false
                else:
                    print("false for", indexOfInterest[j])





        # If we haven't yet the terms in our knowledge base (files doesn't existb)
        else:
            print("\n--Don't have the term, processing to get the new KB...--\n")
            dfRelation_new = pd.DataFrame() 
            dfEntry_new = pd.DataFrame() 


            try:
                new_df = getPreprocessedKB(genericName, inputRelation)
            except:
                pass

            new_fileNameR = f"{genericName}_KBR.csv"
            new_fileNameE = f"{genericName}_KBE.csv"

            try:
                dfRelation_new = pd.read_csv(new_fileNameR, on_bad_lines='skip', delimiter=';')
                dfEntry_new = pd.read_csv(new_fileNameE, on_bad_lines='skip', delimiter=';')

                if(dfRelation_new.empty | dfEntry_new.empty):
                    continue

                indexOfInterest2 = dfRelation_new.loc[dfRelation_new['type']==24].node2.values 
                print("INDEX OF INTEREST : ", indexOfInterest2)
            except:
                pass



            try:
                for k in range(len(dfRelation_new.loc[dfRelation_new['type']==24])):
                    if(dfEntry_new.loc[dfEntry_new['eid']==indexOfInterest2[k]].name.values[0] == inputTermB):
                        print("solution found")
                        solutionFound += 1
                        print(f"\n\n->Answer : Un(e) {inputTermA} est un(e) {genericName} et un(e) {genericName} peut {inputTermB}. Donc un(e) {inputTermA} PEUT {inputTermB}.")
                        sys.exit("A solution has been encountered, program finished.")     
                    else:
                        print("false for", indexOfInterest2[k])
            except:
                pass

           



    # If we can't deduce something, by default, it takes the last generic of our input term A, and based on it, says it returns no/false.
    try:
        if(solutionFound == 0):
            print(f"\n\n->Answer : Un(e) {inputTermA} est un(e) {genericName} et un(e) {genericName} ne peut pas {inputTermB}. Donc un(e) {inputTermA} NE PEUT PAS {inputTermB}.")
    except:
        print("The term hasn't generics. Program finished")


#####################################################
##################### INDUCTION #####################
#####################################################




if(inputRelation == '8'):


    nbSpecifics = len(dfRelation.loc[dfRelation['type']==8].node2) 
    print(nbSpecifics)

    # To iterate on the highest weights
    dfRelation['w'].sort_values(ascending=False)

    # We iterate on the hyponyms of our input term
    for hypo in range(0, nbSpecifics):

        # Debug        
        # if(hypo ==10):
        #     break

        specificDF = pd.DataFrame() 
        try:
            specificDF = dfEntry[dfEntry['eid'] == dfRelation[(dfRelation['type']==8) & (dfRelation['w']>=0)] .node2.iloc[hypo]]
        except:
            pass

        if not specificDF.empty:
            specificName = specificDF.name.values[0]
        else:
            continue
        
       
        print(f"\nTaking into account:\n{specificDF} \n")

        fileNameR = f"{specificName}_KBR.csv"
        fileNameE = f"{specificName}_KBE.csv"
        file_existsR = os.path.exists(fileNameR)
        file_existsE = os.path.exists(fileNameE)

        if (file_existsR == True & file_existsE == True):
            print("File exists, processing...")
            dfTermE = pd.read_csv(fileNameE, on_bad_lines='skip', delimiter=';')
            dfTermR = pd.read_csv(fileNameR, on_bad_lines='skip', delimiter=';')

            if(dfTermR.empty):
                continue

            
            # on a que le df avec les 8 on veut celui avec tout donc on rappl la fcnt avec les mm param excepté n° de fctn
            dfTermR, dfTermE = getPreprocessedKB(inputTermA, '')
            # We take all the id's of the r_agent relation of the specific
            indexOfInterest = dfTermR.loc[dfTermR['type']==24].node2.values 

            # We search for all the r_agent relations of the first specific (index i)
            for j in range(len(dfTermR.loc[dfTermR['type']==24])):
                # At the first matching with the termB (e.g voler), then it succeeds
                if(dfTermE.loc[dfTermE['eid']==indexOfInterest[j]].name.values[0] == inputTermB):
                    solutionFound += 1
                    print(f"\n\n->Answer : Un(e) {inputTermA} est un(e) {specificName} et un(e) {specificName} peut {inputTermB}. Donc un(e) {inputTermA} PEUT {inputTermB}.")
                    sys.exit("A solution has been encountered, program finished.")                 
                # Otherwise if none of them match then we can infer it's false
                else:
                    print("false for", indexOfInterest[j])


        # If we haven't yet the terms in our knowledge base (files doesn't existb)
        else:
            print("\n--Don't have the term, processing to get the new KB...--\n")
            
            # Initializing empty dataframe
            dfRelation_new = pd.DataFrame() 

            try:
                new_df = getPreprocessedKB(specificName, inputRelation)
            

                new_fileNameR = f"{specificName}_KBR.csv"
                new_fileNameE = f"{specificName}_KBE.csv"
                
                dfRelation_new = pd.read_csv(new_fileNameR, on_bad_lines='skip', delimiter=';')
                dfEntry_new = pd.read_csv(new_fileNameE, on_bad_lines='skip', delimiter=';')

            except:
                pass

            if(dfRelation_new.empty):
                continue

            indexOfInterest2 = dfRelation_new.loc[dfRelation_new['type']==24].node2.values 
            print("INDEX OF INTEREST : ", indexOfInterest2)

            print("CHECK", dfRelation_new)
            for k in range(len(dfRelation_new.loc[dfRelation_new['type']==24])):
                print("hello")
                if(dfEntry_new.loc[dfEntry_new['eid']==indexOfInterest2[k]].name.values[0] == inputTermB):
                    solutionFound += 1
                    print(f"\n\n->Answer : Un(e) {inputTermA} est un(e) {specificName} et un(e) {specificName} peut {inputTermB}. Donc un(e) {inputTermA} PEUT {inputTermB}.")
                    sys.exit("A solution has been encountered, program finished.")     
                else:
                    print("false for", indexOfInterest2[k])

    if(solutionFound == 0):
        print(f"\n\n->Answer : Un(e) {inputTermA} est un(e) {specificName} et un(e) {specificName} ne peut pas {inputTermB}. Donc un(e) {inputTermA} NE PEUT PAS {inputTermB}.")





#####################################################
##################### TRANSITIVITÉ ##################
#####################################################

if (inputRelation in ['9','28']):

    if inputRelation in [9]:
        inputTermA,inputTermB = inputTermB,inputTermA

    dfRelation, dfEntry = getPreprocessedKB(inputTermA, inputRelation)
    dfRelation = dfRelation.sort_values(by='w', ascending=False)
    node2ids = np.array(dfRelation.node2.values)
    node2names = dfEntry.set_index("eid").loc[node2ids,['name']].values.flatten()

    for name in node2names:
        print(name)

    try:
        dfNewRelation, dfNewEntry = getPreprocessedKB(name, inputRelation)
        dfNewRelation = dfNewRelation.sort_values(by='w', ascending=False)
        node2ids_bis = np.array(dfNewRelation.node2.values)
        node2names_bis = dfNewEntry.set_index("eid").loc[node2ids_bis,['name']].values.flatten()
        
        if inputTermB in node2names_bis:
            if inputRelation in [9]:        
                inputTermA,inputTermB = inputTermB,inputTermA

        print(inputTermA ," relation n°", inputRelation, inputTermB, " => oui car ", inputTermA ," relation n° ",inputRelation, name, " et ",name ," relation n° ", inputRelation, inputTermB)

    except:
        pass

        print(inputTermA, inputRelation, inputTermB, " => non à priori aucune relation à distance 2 trouvée")



""" Note perso:
Certains termes ne sont pas requétables, exemple "entreprise" , "homme" il a donc fallu traiter ces exceptions
"""
