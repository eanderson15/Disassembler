import subprocess as sp
import sys
import string
import pathlib

# get the date time and directory
when = sp.check_output(['date', "+%H:%M:%S   %d/%m/%y"])
when = str(when, 'utf-8')
where = sp.check_output(['pwd'])
where = str(where, 'utf-8')

# get the executable name from command line
obj_filename = sys.argv[1]

# get the directory name from command line
dir_name = sys.argv[2]

# scan the directory for any .c or .h files
fs = list(pathlib.Path('./' + dir_name).glob('*.c'))
fs = fs + list(pathlib.Path('./' + dir_name).glob('*.h'))

# get the assembly instructions from objump
ass = sp.check_output(['objdump', '-d', dir_name + '/' + obj_filename])
ass = str(ass, 'utf-8')
ass = ass.splitlines()

# get the debug info from llvm-dwarfdump
deb = sp.check_output(['llvm-dwarfdump', '--debug-line', dir_name + '/' + obj_filename])
deb = str(deb, 'utf-8')
deb = deb.splitlines()

# more global variables
funs = []

used_src_sets = []

current_file = ''

main_address = ''

# this function takes in the output from llvm-dwarfdump and converts to list of tuples of dictionaries
# each tuple corresponds to an indivdual entry in the output
# each tuple has a file dictionary and a debug info dictionary
def deb_process(deb):
    deb_files = []
    i = 0
    deb_len = len(deb)
    # iterate through lines
    while (i < deb_len):
        # recognize demarcation of file information
        if ((deb[i])[0:11] == 'file_names['):
            files = []
            addresses = []
            # add all file lines to array
            # depends on empty line after according to generic output
            while (deb[i] != ''):
                files.append(deb[i])
                i = i + 1
            i = i + 1
            # check to account for case where files happen but not debug infor
            if (i < deb_len):
                # skip two lines of non-info
                i = i + 2
                # add all debug info to array
                while (deb[i] != ''):
                    addresses.append(deb[i])
                    i = i + 1
            # append collected information as a tuple
            deb_files.append([files, addresses])
        i = i + 1
    deb_dicts = []
    # iterate through tuples of collected 
    for i in deb_files:
        # utilize functions to convert the information above to dictionaries
        file_dict = convert_debug_files_to_dict(i[0])
        # initialze the list of sets that will collect information on previously used lines
        # for graying out
        for jk in range(len(file_dict)):
            used_src_sets.append(set())
        deb_dict = convert_deb_to_dict(i[1])
        # append dictionarys as tuple
        deb_dicts.append([file_dict, deb_dict])
    return deb_dicts

# function to convert the file info from llvm-dwarfdump to a dictionary
# dictionary {string file #: string filename}
def convert_debug_files_to_dict(s):
    dict = {}
    # iterate through provided lines
    for i in range(len(s)):
        # if the line starts with file
        if(s[i][0:4] == 'file'):
            j = ""
            # iterate through characters and collect the numbers (file number)
            for c in s[i]:
                if c.isdigit():
                    j = j + c
            j = int(j)
            # update the dictionary with the file number and the filename
            dict.update({j:s[i+1].split('"')[1]})
    return dict

# function to convert the debug info from llvm-dwarfdump to a dictionary
# dictionary {string address: list of corresponding strings of debug info}
def convert_deb_to_dict(s):
    dict = {}
    # removes duplicates
    list(dict.fromkeys(s))
    # iterate through lines
    for i in s:
        # if line is an end_sequence that indicates duplicate line so skip
        # if line is not an is_stmt indicates some sort of optimization that doesn't need to be printed
        if ((i.find('end_sequence') == -1) and (i.find('is_stmt') != -1)):
            isplit = i.split()
            # if the address has already been added then append the debug info to that entry's list
            if (dict.get(isplit[0], False)):
                dict.get(i.split()[0]).append(i.split()[1:])
            # else add the address and debug info tuple to dictionary
            else:
                dict.update({i.split()[0]: [i.split()[1:]]})
    return dict

# function to convert the source files to a dictionary
# dictionary {string filename : tuple(list of string lines of source code, array containg bool value if line is visited by assembly)}
def convert_file_to_dict(fs):
    dict = {}
    # iterate through source file names
    for f in fs:
        # open the contents of the file
        sf = str(f)
        fo = open(sf, 'r')
        contents = fo.readlines()
        strlist = []
        # iterate through the source lines and append
        for line in contents:
            if (line == '\n'):
                line = ''
            strlist.append(line)
        fo.close()
        # initialize the visited array
        visited = [False] * len(strlist)
        # update the dictionary {filename, (source array, visited array)}
        dict.update({sf.split('/')[1]: [strlist, visited]})
    return dict

# function to use the addresses in assembly to mark if the src line is visited by it
def mark_visited_src(deb, src):
    # iterate through tuples in deb
    for block in deb:
        # iterate through the lists of debug info
        for diL in block[1].values():
            # iterate through the list
            for di in diL:
                # get the filename using the file number from the debug info
                filename = block[0].get(int(di[2]))
                # get the code
                cv = src.get(filename)
                if (cv != None):
                    # mark the visited array True if here and update the dictionary
                    cv[1][int(di[0]) - 1] = True
                    src.update({filename: cv})
    return src

# function to combine lines that were not visited by assembly into lines that were visited by assembly
def combine_lines(src):
    # iterate through source files
    for key in src.keys():
        cv = src.get(key)
        c = cv[0]
        v = cv[1]
        len_c = len(c)
        i = 0
        # iterate through lines of code
        while(i < len_c):
            # if the line was not visited
            if (not v[i]):
                # if the line is empty or just a bracket
                if (c[i] != '' and (c[i].split()[0] == '}' or c[i].split()[0] == '{')):
                    j = 1
                    # this chunk of code pushes the line up to the closest visited line that's non empty
                    while (c[i - j] == ''):
                        j = j + 1
                    c[i - j] = c[i - j] + c[i]
                    c[i] = ''
                # if still lines in the code to go
                elif (i + 1 < len(c)):
                    # this code pushes the line down
                    c[i + 1] = c[i] + c[i + 1]
                    c[i] = ''
                else:
                    # push the line up to closest visited line that's non empty
                    j = 1
                    while (c[i - j] == ''):
                        j = j + 1
                    c[i - j] = c[i - j] + c[i]
                    c[i] = ''
            i = i + 1
        i = i - 1
        # check for non visited lines at the end of the file and push up
        if (not v[i]):
            j = 1
            while (c[i - j] == '' and (i - j != -1)):
                j = j + 1
            c[i - j] = c[i - j] + c[i]
            c[i] = ''
        # update the src
        cv = [c, v]
        src.update({key: cv})
    return src

# iterate through the source code given an address returns the corresponding source line
def assembly_address_iter(deb, src, address):
    global current_file
    global main_address
    line = ''
    accessed = False
    # iterate through the tuples
    for i in range(len(deb)):
        block = deb[i]
        # check if the address is in the dictionary
        diL = block[1].get(address, False)
        if(diL == False):
            continue
        else:
            # iterate through the debug info
            for di in diL:
                # get the code using file number to file name to src
                name = block[0].get(int(di[2]))
                cv = src.get(name)
                if (cv != None):
                    # if the file number line number tuple is in the set then set accessed to true
                    if ((di[0], di[2]) in used_src_sets[i]):
                        accessed = True
                    # otherwise add the tuple to the set
                    else:
                        used_src_sets[i].add((di[0], di[2]))
                    # if the file name just changed then add tag indicating that file changed to be parsed later
                    if (name != current_file):
                        current_file = name
                        line += '!!!s!!!' + current_file + ' '
                    # add all lines together corresponding to single address
                    line += cv[0][int(di[0]) - 1]
    # if the line has been accessed before then add tag to gray out later
    if (accessed):
        line = '!!!g!!!' + line
    # if the line has main in it and its the first occurence then save address
    if (line.find('main') != -1 and main_address == ''):
        main_address = address
    return line

# iterate through the source code given an address returns the bool if it returns a line
# same as above but not tagging or anything
# simple access iteration
def assembly_address_iter_bool(deb, src, address):
    line = ''
    for block in deb:
        diL = block[1].get(address, False)
        if(diL == False):
            continue
        else:
            for di in diL:
                name = block[0].get(int(di[2]))
                cv = src.get(name)
                if (cv != None):
                    line += cv[0][int(di[0]) - 1]
    if (line != ''):
        return True
    return False

# function to write two files with lined up assembly and source for easy conversion to html
def assembly_iter(deb, src):
    ass_file = open('ass_output.txt', 'w')
    src_file = open('src_output.txt', 'w')
    # iterate through assembly lines
    for line in ass:
        # check if empty
        if (line != ""):
            # get the address
            split_line = line.split()
            split_line = split_line[0].replace(':', '')
            # check if is legit address
            if (all(c in string.hexdigits for c in split_line)):
                hex_len = len(split_line)
                # if this line indicates a function
                if (hex_len == 16):
                    if (assembly_address_iter_bool(deb, src, "0x" + split_line)):
                        # append the address to array
                        funs.append(split_line)
                    continue
                # make the address into len 16 format
                while(hex_len != 16):
                    split_line = '0' + split_line
                    hex_len = hex_len + 1
                # get the source line
                src_line = assembly_address_iter(deb, src, "0x" + split_line)
                # if empty
                if (src_line == ''):
                    # check if assembly has comment
                    if (line.find('#') != -1):
                        # move comment to new line and add new line to source
                        line = line.replace('#', '\n\t#')
                        src_line = src_line + '\n'
                    # write to files with needed new lines
                    src_file.write('\n' + src_line)
                    ass_file.write(line + '\n')
                else:
                    # add f tag to all lines
                    src_line = '!!!f!!!' + split_line + ' ' + src_line
                    # if src line does not have ending endline then add it
                    if (not src_line.endswith('\n')):
                        src_line = src_line + '\n'
                    # count how many endls in src line and add them to assembly line
                    endl_count = src_line.count('\n')
                    while (endl_count > 1):
                        line = '\n' + line
                        endl_count = endl_count - 1
                    # now correct for comment
                    if (line.find('#') != -1):
                        line = line.replace('#', '\n\t#')
                        src_line = src_line + '\n'
                    # now if file changes note will be another line so add endl to assembly
                    if (src_line.find('!!!s!!!') != -1):
                        line = '\n' + line
                    # write lines
                    src_file.write(src_line)
                    ass_file.write(line + '\n')
    ass_file.close()
    src_file.close()

# function to take in lined up output files and converting to html
def generate_html():
    global main_address
    ass_file = open('ass_output.txt', 'r')
    src_file = open('src_output.txt', 'r')
    ass_lines = ass_file.readlines()
    src_lines = src_file.readlines()
    # gets the main address
    main_address = main_address[2:]
    # html starting code
    html_str = '''
    <!doctype html
    <html>
        <head>
            <meta charset="utf-8">
            <title> Bombass Project 4 </title>
        </head>
        <body>'''
    # add when and where and link it to first occurence of main
    html_str = html_str + '<a href="#' + main_address + '">' + '<h3>' + when + ' and ' + where + '</h3>' + '</a>' + '''
            <div style="float: left; width: 50%">
            <p style="white-space: nowrap; font-family: monospace">
    '''
    # iterate through assembly lines
    for ass_line in ass_lines:
        jump = False
        # check if the first character of the instruction is j
        if (len(ass_line) > 32):
            if (ass_line[32] == 'j'):
                jump = True
        # get the address of the jump or the call
        if (len(ass_line) > 44):
            jump_address = ass_line[39:45]
            while (len(jump_address) < 16):
                jump_address = '0' + jump_address
        # replace all special characters with html characters
        ass_line = ass_line.replace('\t', '&nbsp&nbsp&nbsp&nbsp')
        ass_line = ass_line.replace(' ', '&nbsp')
        ass_line = ass_line.replace('<', '&lt')
        ass_line = ass_line.replace('>', '&gt')
        ass_line = ass_line.replace('\n', '<br>')
        # if it is a call
        if (ass_line.find('callq') != -1):
            # check if address is in list of addresses corresponding to functions in source code
            if (jump_address in funs):
                # make linke
                ass_line = '<a href="#' + jump_address + '">' + ass_line + '</a>'
        # if it is a jump
        if (jump):
            plus_index = ass_line.find('+')
            gte_index = ass_line.find('&gt')
            # get the number that is being added to the base address
            if (plus_index != -1 and gte_index != -1):
                add_address = ass_line[(plus_index + 3):gte_index]
                # check if the original address is in the list of addresses corresponding to functions in source code
                if (('0000000000' + hex(int(jump_address, 16) - int(add_address, 16))[2:]) in funs):
                    # make link
                    ass_line = '<a href="#' + jump_address + '">' + ass_line + '</a>'
        # add the line to the html code
        html_str = html_str + ass_line
    # code between assembly and source divs
    html_str = html_str + '''
            </p>
            </div>
            <div style="float: left; width: 50%">
            <p style="white-space: nowrap; font-family: monospace">
    '''
    g = False
    # iterate through source line
    for src_line in src_lines:
        # replace all the special characters with html characters
        src_line = src_line.replace('\t', '&nbsp&nbsp&nbsp&nbsp')
        src_line = src_line.replace(' ', '&nbsp')
        src_line = src_line.replace('<', '&lt')
        src_line = src_line.replace('>', '&gt')
        src_line = src_line.replace('\n', '<br>')
        # get the indices of all tags
        f_tag_index = src_line.find('!!!f!!!')
        g_tag_index = src_line.find('!!!g!!!')
        s_tag_index = src_line.find('!!!s!!!')
        # if there is a file switch tag
        if (s_tag_index != -1):
            # remove it
            src_line = src_line.replace('!!!s!!!', '')
            index = s_tag_index
            # get the index of the last character in file name appended to tag
            while (src_line[index] != '&'):
                index = index + 1
            # get filename and create link
            filename = src_line[s_tag_index:index]
            html_str = html_str + '<a href="./' + dir_name + '/' + filename + '">' + filename + '</a><br>'
            # remove the filename from the source line
            src_line = src_line[:s_tag_index] + src_line[index:]
        html_str = html_str + '<a '
        # if there is an f tag
        if (f_tag_index != -1):
            # reset greying value
            g = False
            # remove the tag
            src_line = src_line.replace('!!!f!!!', '')
            # add the link id
            html_str = html_str + 'id="' + src_line.split('&nbsp')[0] + '"'
        # if there is a g tag set to true
        if (g_tag_index != -1):
            g = True
        # if should be greyed out
        if (g):
            # remove the tag
            src_line = src_line.replace('!!!g!!!', '')
            # make line gray
            html_str = html_str + ' style="color: gray"'
        html_str = html_str + '>'
        if (f_tag_index != -1):
            # remove the tag and add everything else to the line
            src_line = '&nbsp'.join(src_line.split('&nbsp')[1:])
        html_str = html_str + src_line + '</a>'
    html_str = html_str + '''
            </p>
            </div>
        </body>
    </html>
    '''
    html_file = open(dir_name + '/' + obj_filename + '.html', 'w')
    html_file.write(html_str)
    html_file.close()

# process the debug info
deb = deb_process(deb)
# get the source file dictionary
src = convert_file_to_dict(fs)
# mark the corresponding lines
src = mark_visited_src(deb, src)
# combine the lines
src = combine_lines(src)
# iterate over the assembly code
assembly_iter(deb, src)
# generate the html code
generate_html()