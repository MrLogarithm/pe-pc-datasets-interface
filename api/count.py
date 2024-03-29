from collections import defaultdict
from itertools import chain, combinations
import json, re

##############################
# SETUP and HELPER FUNCTIONS #

def powerset( iterable ):
    s = list(iterable)
    return chain.from_iterable( combinations(s,r) for r in range(1,len(s)+1) )

def reduce( sign, split=False, merge=False ):

    variantRegex = "(~|@)[^X.+|()&]+"

    # Problem cases to be aware of:
    # |NINDA2X((UDU~A+TAR)~B)|
    # |(SZAXHI@G~A)~B|
    # ERESZ~X(...), ENLIL~X(...), etc

    if sign == "ENLIL~X(|EN~C.NUN~A|)":
        sign = "|EN~C.NUN~A|"
    if sign == "ERESZ~X(|AN.AB~A|)":
        sign = "|AN.AB~A|"
    if sign == "NERGAL~X(KISZ)":
        sign = "KISZ"

    if merge and "~" in sign or "@" in sign:
        sign = re.sub( variantRegex, '', sign )
        sign = re.sub( "^\|\((.*)\)\|$", "|\\1|", sign ) # replace |( and )| with |
        sign = re.sub( "\(\((.*)\)\)", "(\\1)", sign ) # replace (( and )) with ( and )

    # Sometimes 1(...) is omitted around numerals,
    # eg in |LAGAB~bx(HIxN04)|. Remove the extraneous
    # parenthesis that this introduces:
    #if sign.count(")") == 1:
        #sign = sign.replace(")","")

    if split and ("|" in sign):

        # Even if we don't merge sign variants, we need to get rid of
        # things like |( A x B )~b|, because we want to end up with
        # [A, B], not [A, B~b]:
        if ")~" in sign:
            sign = re.sub("\((.*)\)~[^X.+|()@&]", "\\1", sign)

        sign = re.sub("\|", " ", sign)
        sign = re.sub("([^0-9N])\(+", "\\1", sign)
        sign = re.sub("(([^0-9]{2})|([^0-9][0-9])|([0-9][^0-9])|ZATU[0-9]{3})\)+", "\\1", sign)
        sign = re.sub("[\.+&]", " ", sign)
        sign = re.sub("X", " ", sign)
        # sign = re.sub("([^X ])X", "\\1 ", sign) # < IF X should be counted as a sign
        sign = sign.split(" ")
        sign = [ component for component in sign if component != "" ]

    # For consistency, always return a list when split is True
    if split and not isinstance(sign,list):
        sign = [sign]
    return sign

def simplify_line( line, split=False, merge=False ):
    line = list(map(
            lambda sign: reduce( sign, split=split, merge=merge ),
            line
        ))
    if split:
        line = sum( line, [] )
    # Get rid of errors introduced by N(...) notation:
    line = [sign for sign in line if (sign != "N") and (not sign.startswith("N(")) and (not re.match("^N[0-9]",sign))]
    return line

def get_transliterations( text ):
    text = text[ text.index( "Transliteration:" ) : ]
    text = text.upper().split("\n")[1:]
    lines = []
    for line in text:
        line = line.strip()
        if line == "":
            continue

        if any( line.startswith(char) for char in "#@$&>" ):
            continue

        if " " not in line:
            continue

        if "!(" in line:
            index = line.index("!(")
            index_r = index
            while line[index] != " " and index >= 0:
                index -= 1
            while line[index_r] != ")" and index_r <= len(line):
                index_r += 1
            line = line[:index+1]+line[line.index("!(")+2:index_r]+line[index_r+1:]

        if ")A" in line:
            # Subcases are notated as ( ..... )a
            # Always a, never [b-z]
            index = line.index( ")A" )
            depth = 1
            while index >= 0:
                index -= 1
                if line[index] == "(":
                    depth -= 1
                if line[index] == ")":
                    depth += 1
                if depth == 0:
                    break
            line = line[:index] + line[index+1:line.index(")A")] + line[line.index(")A")+2:]

        # Remove annotations:
        line = re.sub("[#?\[\]!<>]", " ", line)
        # Remove line number:
        line = line[line.index(" ") + 1:]
        # Remove count preceding ,
        if ',' in line:
            line = line[line.index(",")+1:].strip()
        # Split signs apart:
        line = line.split(" ")
        # Remove delimiters:
        line = [sign.strip() for sign in line if sign.strip() != "," and sign.strip() != ""]
        # Get rid of errors introduced by N(...) notation:
        line = [sign for sign in line if (sign != "N") and (not sign.startswith("N(")) and (not re.match("^N[0-9]",sign))]

        lines.append( line )
    lines = {
            "normal":lines,
            "merge":list(map(lambda line:simplify_line( line, merge=True , split=False),lines)),
            "split":list(map(lambda line:simplify_line( line, merge=False, split=True ),lines)),
            "merge_split":list(map(lambda line:simplify_line( line, merge=True , split=True ),lines)),
        }
    return lines



###############
# LOAD CORPUS #

pc_file = open( "./cdli_result_20200519.txt" )
pc_text = pc_file.read()
pc_file.close()

delim = "Primary publication"
pc_text = [
        delim+text
        for text in pc_text.split( delim )[1:]
    ]

corpus = []
for text in pc_text:
    text_info = dict()
    for line in text.split("\n"):
        if ":" in line and not line.startswith("#"):
            key, value = line[ : line.index(":") ], line[line.index(":") + 1 : ]
            key = key.lower().strip()
            value = value.lower().strip()
            if key == "transliteration":
                transliterations = get_transliterations( text )
                text_info[ "transliteration" ] = transliterations
            else:
                text_info[ key ] = value
    corpus.append( text_info )

################
# NGRAM COUNTS #

def get_counts( format_, query, order, numeric, lines, periods, genre, provenience ):
    counts = defaultdict(int)

    for text in corpus:
        
        # Filter texts:
        if not any(p in text['period'] for p in periods):
            continue
            
        if not any(p == text['provenience'] for p in provenience):
            continue
            
        if not any(g in text['genre'] for g in genre):
            continue
            
        for line in text["transliteration"][format_]:
            line_counts = defaultdict(int)
            if order:
                for length in range(1,len(line)+1):
                    for start in range(len(line)-length+1):
                        ngram = tuple(line[start:start+length])
                        if "..." in ngram or "X" in ngram:
                            continue
                        if not numeric and any( re.match("^[0-9]+\(", sign) for sign in ngram ):
                            continue
                        #counts[ngram] += 1
                        line_counts[ngram] += 1
            else:
                for ngram in powerset( line ):
                    ngram = tuple(sorted(ngram))
                    if "..." in ngram or "X" in ngram:
                        continue
                    if not numeric and any( re.match("^[0-9]+\(", sign) for sign in ngram ):
                        continue
                    line_counts[ngram] += 1
            for ngram, count in line_counts.items():
                if lines:
                    counts[ngram] += 1
                else:
                    counts[ngram] += count
    query = query.upper().strip()
    counts = { " ".join(key): counts[key] for key in counts } # if query in key }
    if order:
        counts = { k:v for k,v in counts.items() if query in k }
    else:
        counts = { k:v for k,v in counts.items() 
                   if all(
                       any(word in k_ for k_ in k.split(" ")) 
                       for word in query.split(" ")) }
    return defaultdict(int,counts)
