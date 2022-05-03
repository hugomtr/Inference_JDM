# InferenceJDM
InferenceJDM is a system to make inferences through textual data of the serious game "JeuxDeMots".
The data of JDM has been fed by games of thousands of people over a long period of time.

This tool aims to make inferences of different kind from terms of the knowledge base of Jeux de mots. <br>
To use the script, just run ``` python3 jdm_inferences.py ``` and you will be ask to enter a in this order a first term, a relation between this term and the second one, and this last term. Finally, you are asked to enter a number between 1 and 3 to decide which type of inference you want to make. <br> <br>
Three kind of inferences has been taken into account: 

* **Deductive inference (1)** (we searched for the generics of our first input term to infer) <br> e.g 
*Une tortue peut-elle marcher ? oui car tortue est un reptile et un reptile peut marcher*

* **Inductive inference (2)** (we searched for the specifics of our second input term to infer) <br> e.g 
*Un chat peut-il griffer ? oui car un chat est un sacré de birmanie et un sacré de birmanie peut griffer*

* **Transitive inference (3)** (xRy and yRz => xRz, where R is any relationship between the terms, can be r_has_part, r_lieu, etc) <br> e.g 
*La Tour Eiffel est-elle en France? Oui car la Tour Eiffel est à Paris, et Paris et en France*

-------------------------------------

## Our approach
The code has been divided in 3 functions, without taking into account the main one.

1. ___getPreprocessedKB___ : <br>As its name indicates, this function preprocess the data retrieved in JDM with the help of the library BeautifulSoup. Many regular expressions are used to get rid of the irrelevant parts of the data such as some comments, description and so on. At the end, we use this preprocessed data to get a dataframe. <br> We have divided the relations and the entries into 2 different dataframes. In this function we also check wether a term exists in the Jeux de mots knowledge base or not. If it does not, we save it in an empty file text. Thus, we can make a check later and it will avoid us request one more time the server.
2. ___getPolysemicTerm___ : <br>Returns the name of the polysemic term by taking the id next to the '>' symbol, and mapping it to the entries dataframe.
3. ___fileExists___ : <br>Allows us when making inferences to not request again the server if a given term has already been registered, returns true if the file exists, false otherwise.

### More details
We defined a threshold to stop the program at around 5 seconds, code has been improved to search efficiently and quickly, it has been also refactored many times to improve reusability and redability. We have also sorted the weights of the relations in descending order to get more consistent results, more quickly.

### Relations used in the program

* r_syn
* r_isa
* r_anto
* r_hypo
* r_has_part
* r_carac
* r_holo
* r_agent-1
* r_instr-1
* r_patient-1
* r_lieu-1

More details about what these relations can do [there](http://www.jeuxdemots.org/jdm-about-detail-relations.php).

### Contributors
* Adrien Linares
* Hugo Maître
