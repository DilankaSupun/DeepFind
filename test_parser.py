import re

def parse_query_test(original_query: str):
    q = original_query.lower().strip()

    # Normalize UI/UX
    q = re.sub(r'ui[/-_]ux', 'ui ux', q)
    q = re.sub(r'\.(\w+)', r'\1', q)

    # We want to extract location phrases.
    # Words: in, inside, from, under
    # Drive indicators: drive
    # Folder indicators: folder
    
    # To handle 'C:', we should probably preserve : and \ just for drive detection.
    # Let's tokenize by space first, preserving punctuation attached to words.
    raw_tokens = q.split()
    
    drive_filters = set()
    folder_filters = set()
    location_words_used = set() # To exclude from normal metadata
    
    i = 0
    while i < len(raw_tokens):
        w = raw_tokens[i]
        clean_w = re.sub(r'[^\w:]', '', w) # keep letters, numbers, and colon
        
        if clean_w in ("in", "inside", "from", "under"):
            # Start parsing location
            loc_tokens = []
            j = i + 1
            is_drive_explicit = False
            is_folder_explicit = False
            
            # Lookahead to see if 'folder' or 'drive' is next
            if j < len(raw_tokens):
                cw = re.sub(r'[^\w]', '', raw_tokens[j])
                if cw == "drive":
                    is_drive_explicit = True
                    location_words_used.add(raw_tokens[j])
                    j += 1
                elif cw == "folder":
                    is_folder_explicit = True
                    location_words_used.add(raw_tokens[j])
                    j += 1
            
            # Now collect the X terms. X can be multiple words if at the end, 
            # or bounded by 'folder' / 'drive' at the end of X.
            # For simplicity, let's just collect all remaining words in the query 
            # OR until we hit another instruction word?
            # Actually, "assignment pdf in UCSC Year2" -> UCSC, Year2 are all folder filters.
            # "fixlanka php inside Projects folder" -> Projects is folder.
            
            while j < len(raw_tokens):
                cw = re.sub(r'[^\w:]', '', raw_tokens[j])
                if cw == "folder" or cw == "drive":
                    location_words_used.add(raw_tokens[j])
                    if cw == "drive": is_drive_explicit = True
                    if cw == "folder": is_folder_explicit = True
                    j += 1
                    break # end of phrase
                
                # if we hit another instruction word that isn't part of location?
                # For safety, let's just assume all trailing words are part of location unless they are known instructions.
                # Actually, "in Downloads cv pdf" is possible? People usually put location at the end.
                
                loc_tokens.append(raw_tokens[j])
                location_words_used.add(raw_tokens[j])
                j += 1
                
            location_words_used.add(w) # the preposition
            
            # Process loc_tokens
            for lt in loc_tokens:
                cl = re.sub(r'[^\w:]', '', lt)
                # check if it's a drive
                if len(cl) == 1 and cl.isalpha():
                    # 'e'
                    drive_filters.add(cl.upper() + ":")
                elif len(cl) == 2 and cl[0].isalpha() and cl[1] == ':':
                    # 'e:'
                    drive_filters.add(cl[0].upper() + ":")
                elif is_drive_explicit and len(cl) > 0:
                    # 'drive c' -> C:
                    if len(cl) == 1 and cl.isalpha():
                        drive_filters.add(cl.upper() + ":")
                    else:
                        folder_filters.add(cl) # fallback
                else:
                    if cl:
                        folder_filters.add(cl)
            i = j
        else:
            i += 1

    print(f"Query: {original_query}")
    print(f"Drive: {drive_filters}")
    print(f"Folder: {folder_filters}")
    print(f"Location words: {location_words_used}")
    print("-" * 40)

parse_query_test("password = document.getElementById('password').value in folder E")
parse_query_test("cv pdf in Downloads")
parse_query_test("fixlanka php inside Projects folder")
parse_query_test("hello world in drive D")
parse_query_test("hello world in D:")
parse_query_test("assignment pdf in UCSC Year2")
