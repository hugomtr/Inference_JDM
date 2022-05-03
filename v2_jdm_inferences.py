import requests
from bs4 import BeautifulSoup
import re, csv
import numpy as np
import os.path, sys
import pandas as pd
import time

# Relations that will be used in our system
dicoRelations = {"r_syn": '5', "r_isa": '6', "r_anto": '7', "r_hypo": '8', "r_has_part": '9', "r_carac": '17', "r_holo": '10', 
                "r_agent-1": '24', "r_instr-1": '25', "r_patient-1": '26', "r_lieu-1": '28'}


def getPreprocessedKB(iA, iR,Sortant = True):

    inputTermA = iA
    inputRelation = iR

    filenameEntry = f"{inputTermA}_KBE.csv"
    filenameRelation = f"{inputTermA}_KBR.csv"

    # Avoid querying one more time the server a term that does not exist
    if os.path.isfile(f"{inputTermA}_Empty.txt"):
        sys.exit(f"En consultant le système de fichiers, il a déjà été acté que le terme {inputTermA} n'existait pas")  

    if not iR:
        vgm_url = f'http://www.jeuxdemots.org/rezo-dump.php?gotermsubmit=Chercher&gotermrel={inputTermA}&rel='

    # Parsing of the JDM lexical network DUMP on a given input Term
    vgm_url = f'http://www.jeuxdemots.org/rezo-dump.php?gotermsubmit=Chercher&gotermrel={inputTermA}&rel={inputRelation}'
    if Sortant:
       vgm_url = f'http://www.jeuxdemots.org/rezo-dump.php?gotermsubmit=Chercher&gotermrel={inputTermA}&rel={inputRelation}&relin=norelin'

    html_text = requests.get(vgm_url).text
    soup = BeautifulSoup(html_text, 'html.parser')

    # Taking everything starting from the code balise
    try:
        page = soup.find('code').getText()
    except:
        open(f"{inputTermA}_Empty.txt", "x")
        sys.exit(f"Le terme {inputTermA} n'existe pas.") 

    # RegEx patterns for preprocessing 
    commentsPattern = "^\/\/ *.*"
    behindNodePattern = "(?s)^.*?(?=e;eid)"
    behindNodePatternRelations = "(?s)^.*?(?=r;rid)"
    blankLinesPattern = "^\s*$"
    deleteSingleQuotes = r"(?!\b'\b)'"

    # ENTRIES PREPROCESSING
    prepro1 = re.sub(behindNodePattern, '', page) # Delete all what's behind the first nodes e;[...]
    prepro2 = re.sub(commentsPattern, '', prepro1, flags=re.MULTILINE) # Delete all the comments (whitespace can be seen as \s in regex.) 
    prepro3 = re.sub("((r;.*)|(rt;.*))", '', prepro2) # Delete relations, relations types, blank lines
    prepro4 = re.sub(blankLinesPattern, '', prepro3, flags=re.MULTILINE) 
    entries = re.sub(deleteSingleQuotes, '', prepro4)

    # RELATIONS PREPROCESSING
    pp1 = re.sub(behindNodePatternRelations, '', page)
    relations = re.sub(commentsPattern, '', pp1, flags=re.MULTILINE)

    # Make this as a list
    textEntry = entries.split("\n")
    textRelation = relations.split("\n")

    # Convert raw data into semi-structured data (in this case csv format file) and save it.
    np.savetxt(filenameEntry, textEntry, delimiter =",", fmt ='%s')
    np.savetxt(filenameRelation, textRelation, delimiter =",", fmt ='%s')

    dfEntry = pd.read_csv(filenameEntry, on_bad_lines='skip', delimiter=';')
    dfRelation = pd.read_csv(filenameRelation, on_bad_lines='skip', delimiter=';')
 
    return dfRelation, dfEntry


def getPolysemicTerm(dfEntries, nodeNames):
    polysemicPattern = "(?<=>)[0-9]*"
    prepro = re.search(polysemicPattern, nodeNames[0]) 
    polysemicId = prepro.group()
    rowDFpolys = dfEntries.loc[dfEntries['eid'] == int(polysemicId)]
    polysemicName = "("+ rowDFpolys['name'].values[0] + ")"
    return polysemicName

def fileExists(nameTerm): 
    fileNameR = f"{nameTerm}_KBR.csv"
    fileNameE = f"{nameTerm}_KBE.csv"
    file_existsR = os.path.exists(fileNameR)
    file_existsE = os.path.exists(fileNameE)
    if (file_existsR == True & file_existsE == True):
        return True
    else:
        return False

def main():

    inputTermA = input("Entrez un premier terme: \n")
    relationType = input("Entrez une relation sémantique entre le premier terme et celui d'après: \n")

    # Relation type must be a valid jdm one and that is in the dictionnary (à corriger)
    while(relationType not in dicoRelations):
        relationType = input("Erreur, veuillez rentrer un nom de relation valide: \n")

    inputTermB = input("Entrez un second terme: \n")

    # To get the num of the relation based on the name
    inputRelation = int(dicoRelations[relationType])


    print("\n##################################################################\n\
     |  Tapez (1) pour une inférence déductive          |\n \
    |  Tapez (2) pour une inférence inductive          |\n \
    |  Tapez (3) pour une inférence transitive         |\n\
##################################################################\n\n")

    inferenceType = input("Quel type d'inférence souhaitez vous faire ? \n")

    while (inferenceType not in ['1','2','3']):
        inferenceType = input("Erreur, veuillez rentrer un numéro d'inférence valide: \n")

    polyTerm = ""
    count = 0
    
    #####################################################
    ############# DEDUCTION & INDUCTION #################
    #####################################################

    if (inferenceType == '1'):

        dfRelation, dfEntry = getPreprocessedKB(inputTermA, '6')      
        dfRelation = dfRelation.sort_values(by='w ', ascending=False)
        nodeIds = np.array(dfRelation.node2.values)
        node2names = dfEntry.set_index("eid").loc[nodeIds,['name']].values.flatten()
                
        for name in node2names:

            exists = fileExists(name)

            start = time.time()
            print("\nSearching generics ... - Found: ",name)
                
            if name == inputTermB:
                print("\n->Question : ",inputTermA ,relationType, inputTermB, "\n->Answer => Oui c'est possible car ", inputTermA ,inputRelation, name,  " et ",name , inputRelation, inputTermB)
                return

            try:
                if (exists == True):
                    print("Term exists, processing...")
                    dfNewEntry = pd.read_csv(fileNameE, on_bad_lines='skip', delimiter=';')
                    dfNewRelation = pd.read_csv(fileNameR, on_bad_lines='skip', delimiter=';')
                else:
                    print("Term doesn't exist, querying...")
                    dfNewRelation, dfNewEntry = getPreprocessedKB(name, relationType)

                dfNewRelation = dfNewRelation.sort_values(by='w ', ascending=False)
                nodeIds_bis = np.array(dfNewRelation.node2.values)
                node2names_bis = dfNewEntry.set_index("eid").loc[nodeIds_bis,['name']].values.flatten()

                end = time.time()
                timer = end-start
                count += timer
                if(count >= 5):
                    print("\n[Threshold reached. Program has stopped]")
                    break
                
                if inputTermB in node2names_bis:
                    # Inversed relation
                    if relationType in [9]:        
                        inputTermA,inputTermB = inputTermB,inputTermA   
                    # Taking into account polysemic terms
                    if '>' in name:
                        polyTerm = getPolysemicTerm(dfEntry, node2names)
                        name = re.sub("[0-9].*", polyTerm, name)      
                    print("\n->Question : ",inputTermA ,relationType, inputTermB, "\n->Answer => Oui c'est possible car ", inputTermA , "r_isa" , name, " et ",name, relationType, inputTermB)
                    return              
            except:
                pass
        print("\n->Question : ",inputTermA, relationType, inputTermB, "\n->Answer => Non, à priori il n'y a pas d'explication pour cela")
        return


    if (inferenceType == '2'):     
        dfRelation, dfEntry = getPreprocessedKB(inputTermA, '8')
        dfRelation = dfRelation.sort_values(by='w ', ascending=False)
        nodeIds = np.array(dfRelation.node2.values)
        node2names = dfEntry.set_index("eid").loc[nodeIds,['name']].values.flatten()

        for name in node2names:

            exists = fileExists(name)
            start = time.time()
            print("\nSearching specifics ... - Found: ",name)
            if name == inputTermB:
                print("\n->Question : ",inputTermA ,relationType, inputTermB, "\n->Answer => Oui c'est possible car ", inputTermA ,relationType, name, " et ",name , relationType, inputTermB)
                return

            try:
                if (exists == True):
                    print("->Term already exists, processing...")
                    dfNewEntry = pd.read_csv(fileNameE, on_bad_lines='skip', delimiter=';')
                    dfNewRelation = pd.read_csv(fileNameR, on_bad_lines='skip', delimiter=';')
                else:
                    dfNewRelation, dfNewEntry = getPreprocessedKB(name, relationType)
                    print("->Term doesn't exist, querying...")

                dfNewRelation = dfNewRelation.sort_values(by='w ', ascending=False)
                nodeIds_bis = np.array(dfNewRelation.node2.values)
                node2names_bis = dfNewEntry.set_index("eid").loc[nodeIds_bis,['name']].values.flatten()

                # Stop the program if nothing has been found until a certain threshold
                end = time.time()
                timer = end-start
                count += timer
                if(count >= 5):
                    print("\n[Threshold reached. Program has stopped]")
                    break
                    
                if inputTermB in node2names_bis:
                    # relation inversée
                    if relationType in [9]:        
                        inputTermA,inputTermB = inputTermB,inputTermA
                    if '>' in name:
                        polyTerm = getPolysemicTerm(dfEntry, node2names)
                        name = re.sub("[0-9].*", polyTerm, name)      
                    print("\n->Question : ",inputTermA ,relationType, inputTermB, "\n->Answer => Oui c'est possible car ", inputTermA , "r_isa" , name, " et ",name, relationType, inputTermB)
                    return             
            except:
                pass
        print("\n->Question : ",inputTermA, relationType, inputTermB, "\n->Answer => Non, à priori il n'y a pas d'explication pour cela")
        return

    #####################################################
    ##################### TRANSITIVITÉ ##################
    #####################################################

    if (inferenceType == '3'):

        if relationType in [9]:
            inputTermA,inputTermB = inputTermB,inputTermA

        dfRelation, dfEntry = getPreprocessedKB(inputTermA, relationType)
        dfRelation = dfRelation.sort_values(by='w ', ascending=False)
        nodeIds = np.array(dfRelation.node2.values)
        node2names = dfEntry.set_index("eid").loc[nodeIds,['name']].values.flatten()

        for name in node2names:
            exists = fileExists(name)
            start = time.time()
            print("\nSearching ... -",name,"\n")
            if name == inputTermB:
                print("\n->Question: ",inputTermA , inputRelation, inputTermB, "\n->Answer => Oui c'est possible car ", inputTermA ,relationType, name, " et ",name , relationType, inputTermB)
                return

            try:
                if (exists == True):
                    print("Term exists, processing...")
                    dfNewEntry = pd.read_csv(fileNameE, on_bad_lines='skip', delimiter=';')
                    dfNewRelation = pd.read_csv(fileNameR, on_bad_lines='skip', delimiter=';')
                else:
                    print("Term doesn't exist, querying...")
                    dfNewRelation, dfNewEntry = getPreprocessedKB(name, relationType)
                dfNewRelation = dfNewRelation.sort_values(by='w ', ascending=False)
                nodeIds_bis = np.array(dfNewRelation.node2.values)
                node2names_bis = dfNewEntry.set_index("eid").loc[nodeIds_bis,['name']].values.flatten()

                end = time.time()
                timer = end-start
                count += timer
                if(count >= 5):
                    print("\n[Threshold reached. Program has stopped]")
                    break

                if inputTermB in node2names_bis:
                    if relationType in [9]:        
                        inputTermA,inputTermB = inputTermB,inputTermA
                    print(inputTermA , relationType, inputTermB, "\n->Answer => Oui c'est possible car ", inputTermA ,relationType, name, " et ",name , relationType, inputTermB)
                    return                
            except:
                pass

        print("\n->Question: ", inputTermA, relationType, inputTermB, " => Non à priori aucune relation à distance 2 trouvée")

if __name__ == "__main__":
    main()