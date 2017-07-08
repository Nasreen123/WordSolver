import requests, re


# GET POTENTIAL MATCHES
def get_matches(target):
    length = len(target)
    matches = []

    word_list = open('wordsolver/word_list.txt', 'r')
    len_word_list = 0

    for word in word_list:
        word = word.strip()
        len_word_list += 1

        if len(word) == length:
            matching = True

            for i, letter in enumerate(word):
                if letter != "_" and target[i] == "_" or \
                   target[i] != "?" and letter != target[i]:
                    matching = False

            if matching == True:
                matches.append(word)

    word_list.close()
    return matches


# GET WORD MEANINGS
def get_meanings(matches):
    matches_and_meanings = {}

    for word in matches:
        meaning = get_meaning(word)
        matches_and_meanings[word] = meaning

    return matches_and_meanings

def get_meaning(word):
    extract = get_wikipedia_extract(word)
    disambiguation = get_wikipedia_disambiguation_page(word)
    #definition = get_wiktionary_meaning(word) # won't use this for now
    extract = clean(extract)
    #disambiguation = clean(disambiguation) # unnecessary

    if 'may refer to:' in extract:
        meaning = extract.split(' . ')
        meaning = meaning[1:]
    else:
        meaning = [extract]
    return meaning

def clean(text):
    text = re.sub('\n\n\n', '', text)
    text = re.sub('\n\n', '', text)
    text = re.sub('\n', '', text)
    text = re.sub('<li>.+?,', ' . ', text)
    text = re.sub('<.+?>', '', text)
    text = re.sub(r'\[(edit)\]', '', text) #<-- this line breaks it
    return text


def get_wikipedia_extract(word):
    try:
        query = 'https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=&redirects=1&format=json&titles=' + word
        r = requests.get(query)
        result_object = r.json()
        key = list(result_object['query']['pages'].keys())[0]
        if key != None:
            extract = result_object['query']['pages'][key]['extract']
            if word + ' may refer to:' not in extract:
                return extract
        return ''
    except:
        return ''


def get_wikipedia_disambiguation_page(word):
    try:
        query = 'https://en.wikipedia.org/wiki/' + word
        #try here?
        result = requests.get(query)
        text = result.text

        start = re.search(' may refer to:</p>', text)
        end = re.search('<span class="mw-headline" id="See_also">', text)

        text = text[start.end():end.start()]

        return text
    except:
        return ''


def get_wiktionary_meaning(word):
    query = 'https://en.wiktionary.org/wiki/' + word
    result = requests.get(query) #urllib.request.urlopen(query).read()
    text = result.text
    #print('\n\n', word, ' wiktionary: ', text)
    try:
        start = re.search('id="Translations', text) #(.+?)style="text-align:left;">
        text = text[start.end():]
        start = re.search('style="text-align:left;">', text)
        text = text[start.end():]
        end = re.search("</div>", text)
        text = text[:end.start()]
        return meaning
    except:
        return ''


# RATE MEANINGS BASED ON CLUES TO FIND THE BEST MATCHES
def get_score(meaning, clues):
    score = 0
    for clue_word in clues:
        for item in meaning:
            if clue_word in item:
                score = score + 1
    return score


def sort_matches(matches_meanings_dict, clues):
    scores_dict = {} # might use this later to give better suggestions

    for word, meaning in matches_meanings_dict.items():
        score = get_score(meaning, clues)
        if score > 0:
            scores_dict[word] = score

    matches = scores_dict.keys()
    ordered_matches = sorted(matches, reverse=True, key=lambda word: scores_dict[word])

    return ordered_matches



# TERMINAL TOOL

def print_match_and_meaning(match, meaning=None, full_meaning=False):
    print("\n", match)
    if len(meaning) == 1 and full_meaning == False:
        print(meaning[0][:200])
    elif len(meaning) == 1 and full_meaning == True:
        print(meaning[0])
    else:
        print("; ".join(meaning))
    print('\n')

if __name__ == "__main__":

    with open('wordsolver/stopwords.txt') as stopwordsfile:
        stopwords = [word.strip() for word in stopwordsfile]

    print("\nWelcome to wordsolver!")
    target = input("\nPlease type the pattern of the target word, using '?' for unknown letters, eg. '?y?'\n>>")
    clue = input("\nPlease type the clue\n>>")

    print("\n Please wait while matches are found\n")

    matches = get_matches(target)
    meanings_dict = get_meanings(matches)

    print("-----------------------------------------")

    for match, meaning in meanings_dict.items():
        print_match_and_meaning(match, meaning)

    print("-----------------------------------------")

    print("To sort the list and see the most likely matches, type 'sort'")
    print("To get the full meaning of a word, type the word")
    print("To quit, type 'q'")

    running = True

    while running:

        user_input = input(">>")

        if user_input == "q":
            running = False

        elif user_input == "sort":
            clues = [word for word in clue.split(" ") if word not in stopwords]
            sorted_matches = sort_matches(meanings_dict, clues)
            for match in sorted_matches:
                meaning = meanings_dict.get(match, None)
                print_match_and_meaning(match, meaning)

        else:
            meaning = meanings_dict.get(user_input, None)
            print_match_and_meaning(user_input, meaning, full_meaning=True)
