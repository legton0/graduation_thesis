import io
import unicodedata

def readCsvToDict(fileName):
    with io.open(fileName+'.csv', mode='r', encoding='utf8') as f:
        lines = f.readlines()
    csvDict = {}
    for line in lines:
        splitLine = line.replace('\n', '').split(':')
        csvDict[splitLine[0]] = splitLine[1].split(',')
        csvDict[splitLine[0]] = [value for value in csvDict[splitLine[0]] if value != '']
    return csvDict

def writeDictToCsv(fileName, outputDict):
    with io.open(fileName+'.csv', mode='w', encoding='utf8') as f:
        for key,values in outputDict.items():
            f.write(key)
            f.write(':')
            f.write(',')
            for value in values:
                f.write(str(value))
                f.write(',')
            f.write('\n')

# le o vocabulario de palavras do dataset aeiouadô
def readWordsDict():
    with io.open('dataset.csv', mode='r', encoding='utf8') as f:
        lines = f.readlines()
    wordsDict = {}
    for line in lines:
        splitLine = line.replace('\n', '').split(',')
        wordsDict[splitLine[0].lower()] = splitLine[1]
    return wordsDict

def readCsvArray(fileName):
    with io.open(fileName+'.csv', mode='r', encoding='utf8') as f:
        lines = f.readlines()
    csvArray = []
    for line in lines:
        csvArray += line.replace('\n', '').split(',')
    return csvArray

# substitui acentos por letras sem acento para normalizar as palavras
def replaceAccentedCharacters(word):
    newWord = ''
    normalizedWord = unicodedata.normalize('NFKD', word).encode('ASCII', 'ignore').decode("utf-8")
    vowels = ['a', 'e', 'i', 'o', 'u']
    i = 0
    if len(word) == len(normalizedWord):
        while i < len(word):
            if normalizedWord[i] in vowels:
                newWord += normalizedWord[i]
            else:
                newWord += word[i]
            i += 1
    else:
        raise ValueError('Invalid Word')
    return newWord

# tenta encontrar um valor fonetico, utilizado para verificar se um valor fonetico existe
def tryFindPhoneticValue(phoneticTranscription, i, phoneticsDictSubset):
    auxI = i
    phoneticIndex = -1
    currentPhoneticValue = ''
    lastFoundPhoneticValue = ''
    while auxI >= 0:
        currentPhoneticValue = phoneticTranscription[auxI] + currentPhoneticValue
        try:
            phoneticIndex = phoneticsDictSubset.index(currentPhoneticValue)
            lastFoundPhoneticValue = currentPhoneticValue
        except:
            pass
        auxI -= 1
    if phoneticIndex >= 0:
        return lastFoundPhoneticValue
    else:
        return ''

# retorna a label do som da silaba na etiquetagem proposta
def getSoundLabel(wordSyllabes, wordSyllabesPhonetics, i, j, newRepresentationKeysDict, newRepresentationValuesDict):
    keyIndex = -1
    valueIndex = -1
    vowels = ['a', 'e', 'i', 'o', 'u']
    label = ''
    foundBoth = False
    if wordSyllabes[i][j] in vowels:
        label = 'V'
    else:
        for rkey,rvalue in newRepresentationKeysDict.items():
            try:
                keyIndex = rvalue.index(wordSyllabes[i][j])
                valueIndex = newRepresentationValuesDict[rkey].index(wordSyllabesPhonetics[i][j])
                if (keyIndex >= 0 and valueIndex >= 0):
                    label = rkey
                    break
            except:
                if (keyIndex >= 0 and label == ''):
                    label = rkey
                pass
    if label != '':
        return label
    else:
        return ' ? '

# retorna a label de posição da silaba na etiquetagem proposta
def getPositionLabel(wordSyllabes, wordSyllabesPhonetics, i, j, newRepresentationKeysDict, newRepresentationValuesDict, previousPositionLabel):
    vowels = ['a', 'e', 'i', 'o', 'u']
    label1 = ''
    label2 = ''
    label3 = ''
    label3Value = 1
    if wordSyllabes[i][j] in vowels:
        label1 = 'S'
        label2 = 'N'
        if len(wordSyllabes[i]) > (j+1) and wordSyllabes[i][j+1] in vowels:
            label1 = 'C'
            label3 = '1'
            label3Value += 1
        if j > 0 and wordSyllabes[i][j-1] in vowels:
            label1 = 'C'
            label3 = '2'
            label3Value += 1
        if label3Value > 2:
            label3 = ' ??? '
    else:
        label1 = 'S'
        label2 = 'A'
        if len(wordSyllabes[i]) > (j+1) and wordSyllabes[i][j+1] not in vowels:
            label1 = 'C'
            label3 = '1'
            label3Value += 1
        if j > 0:
            if wordSyllabes[i][j-1] in vowels:
                label2 = 'C'
            else:
                label1 = 'C'
                label3 = '2'
                label3Value += 1
                if len(previousPositionLabel) > 2 and previousPositionLabel[1] == 'C':
                    label2 = 'C'
        if label3Value > 2:
            label3 = ' ??? '
    label = label1 + label2 + label3
    if label != '':
        return label
    else:
        return ' ?? '


# faz o pre-processamento, transformando as palavras do vocabulário normal + fonético na etiquetagem proposta
# retorna um dicionario contendo todas as representações da palavra
def preprocessing(wordsDict, phoneticsDict, badWords, phoneticCountDict = None):
    newRepresentationKeysDict = readCsvToDict('newRepresentationDictKeys')
    newRepresentationValuesDict = readCsvToDict('newRepresentationDictValues')
    outputDict = {}
    for key,value in wordsDict.items():
        word = replaceAccentedCharacters(key)
        if word in badWords or key in badWords or word[0] == '-':
            continue
        phoneticTranscription = value.replace('[', '').replace(']', '')
        i = len(phoneticTranscription) - 1
        j = len(word) - 1
        newWord = ''
        currentPhoneticValue = ''
        mutedSounds = ['h', '*n', '*m', 'bs', 'sc', 'sç', 'xc', 'xs', 'b-', 'd-', 'r-', 's-', 'x-']
        vowels = ['a', 'e', 'i', 'o', 'u']
        phoneticSyllabes = phoneticTranscription.split('.')
        wordSyllabesPhonetics = []
        wordSyllabes = []
        newRepresentation = ''
        for s in range(len(phoneticSyllabes)):
            wordSyllabesPhonetics.append([])
            wordSyllabes.append([])
        s = len(phoneticSyllabes) - 1
        while j >= 0:
            if (phoneticTranscription[i] == "." or phoneticTranscription[i] == "'"):
                if phoneticTranscription[i] == ".":
                    s -= 1
                newWord = phoneticTranscription[i] + newWord
                i -= 1
                continue
            if (word[j] == "-"):
                j -= 1
                continue
            if (j-1) >= 0 and (word[j-1]+word[j]) in phoneticsDict.keys():
                currentPhoneticValue = tryFindPhoneticValue(phoneticTranscription, i, phoneticsDict[word[j-1]+word[j]])
            if currentPhoneticValue != '':
                newWord = word[j-1]+word[j] + newWord
                wordSyllabesPhonetics[s].insert(0, currentPhoneticValue)
                wordSyllabes[s].insert(0, word[j-1]+word[j])
                j -= 1
            else:
                currentPhoneticValue = tryFindPhoneticValue(phoneticTranscription, i, phoneticsDict[word[j]])
                if currentPhoneticValue != '':
                    newWord = word[j] + newWord
                    wordSyllabesPhonetics[s].insert(0, currentPhoneticValue)
                    wordSyllabes[s].insert(0, word[j])
            if currentPhoneticValue == '':
                isMutedSound = False
                if (j-1) >= 0:
                    if word[j-1] in vowels:
                        possibleMutedSound = '*' + word[j]
                        if possibleMutedSound in mutedSounds:
                            if not isMutedSound:
                                wordSyllabesPhonetics[s].insert(0, '')
                                wordSyllabes[s].insert(0, word[j])
                            isMutedSound = True
                    else:
                        possibleMutedSound = word[j-1] + word[j]
                        if possibleMutedSound in mutedSounds:
                            if not isMutedSound:
                                wordSyllabesPhonetics[s].insert(0, '')
                                wordSyllabes[s].insert(0, word[j])
                            isMutedSound = True
                if (j+1) < len(word):
                    if word[j] in vowels:
                        possibleMutedSound = '*' + word[j+1]
                        if possibleMutedSound in mutedSounds:
                            if not isMutedSound:
                                wordSyllabesPhonetics[s].insert(1, '')
                                wordSyllabes[s].insert(0, word[j])
                            isMutedSound = True
                    else:
                        possibleMutedSound = word[j] + word[j+1]
                        if possibleMutedSound in mutedSounds:
                            if not isMutedSound:
                                wordSyllabesPhonetics[s].insert(1, '')
                                wordSyllabes[s].insert(0, word[j])
                            isMutedSound = True
                possibleMutedSound = word[j]
                if possibleMutedSound in mutedSounds:
                    if not isMutedSound:
                        wordSyllabesPhonetics[s].insert(0, '')
                        wordSyllabes[s].insert(0, word[j])
                    isMutedSound = True
                if isMutedSound:
                    newWord = word[j] + newWord
                else:
                    print(key+',')
            i -= len(currentPhoneticValue)
            j -= 1
            currentPhoneticValue = ''
        if (i == 0):
            newWord = phoneticTranscription[i] + newWord
            i -= 1
        auxNewWord = newWord.replace(".", '').replace("'", '')
        if len(auxNewWord) != len(word.replace("-", "")):
            print(key+',')
        else:
            auxNewWord = ''
            for s in wordSyllabes:
                auxNewWord += ''.join(s)
            if (len(auxNewWord) != len(word.replace("-", ""))):
                print(auxNewWord)
                print(wordSyllabes, wordSyllabesPhonetics)
                print(word)
            else:
                syllabes = newWord.replace("'", "").split('.')
                defaultSyllabeValue = 1
                previousPositionLabel = ''
                for s in range(len(phoneticSyllabes)):
                    syllabeValue = defaultSyllabeValue
                    newRepresentation += '['
                    for l in range(len(phoneticSyllabes[s])):
                        if (phoneticSyllabes[s][l] == "'"):
                            syllabeValue = 3
                            defaultSyllabeValue = 0
                            continue
                    for l in range(len(wordSyllabesPhonetics[s])):
                        newRepresentation += '('
                        soundLabel = getSoundLabel(wordSyllabes, wordSyllabesPhonetics, s, l, newRepresentationKeysDict, newRepresentationValuesDict)
                        positionLabel = getPositionLabel(wordSyllabes, wordSyllabesPhonetics, s, l, newRepresentationKeysDict, newRepresentationValuesDict, previousPositionLabel)
                        newRepresentation += positionLabel
                        newRepresentation += ' '
                        newRepresentation += soundLabel
                        newRepresentation += ')'
                        previousPositionLabel = positionLabel
                    newRepresentation += ']'
                    newRepresentation += str(syllabeValue)
                    if (s < (len(phoneticSyllabes)-1)):
                        newRepresentation += '.'
                if '?' not in newRepresentation:
                    outputDict[word] = [newWord, phoneticTranscription, newRepresentation]
    return outputDict

def main():
    # le dicionário de simbolos fonéticos
    phoneticsDict = readCsvToDict('phoneticsDict')

    # le dataset original contendo vocabulário e representações fonéticas
    wordsDict = readWordsDict()

    # pega lista de palavras que estavam causando problemas
    # ao curso do TCC, foi decidido não tratar todos os casos por questão de tempo
    badWords = readCsvArray('badWords')

    # faz o pre-processamento, transformando as palavras do vocabulario em todas as representações
    # utilizadas, incluindo a etiquetagem
    result = preprocessing(wordsDict, phoneticsDict, badWords)
    
    writeDictToCsv('etiquetas', result)

if __name__ == "__main__":
    main()