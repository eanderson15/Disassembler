# Disassembler

Files:
disassem.py 

We would like to mention that if '!!!f!!!', '!!!g!!!',
'!!!s!!!', or '&nbsp' are ever used as strings in the c
source file code the disassem script will not work since
we used those as tags and '&nbsp' to replace spaces and
newline characters to format our html better.

To run the file, we need the
executable file name and the directory it resides in.
All files, executable and source code, need to be
located in a subfolder within the directory where
disassem.py is located.
python disassem.py (executable file) (directory of file)

To run with our test cases:
1) Type "python disassem.py hello test1"
2) Type "python disassem.py opt test2"

Examples:
    On input:
        python disassem.py hello test1
    Our output in html is in the file hello.html with
    llvm-dwarfdump --debug-line and objdump -d used
    internally in the code. Outputed as well are two
    files ass_output.txt and src_output.txt which are
    the lines printed out before html formatting.

    On input:
        python disassem.py opt test2
    Our output in html is in the file opt.html with
    llvm-dwarfdump --debug-line and objdump -d used
    internally in the code. Outputed as well are two
    files ass_output.txt and src_output.txt which are
    the lines printed out before html formatting.

We would like to mention we had 10 functions (3 to
parse the assembly and source to dictionaries, 1 to combine lines
according to description, 1 to process debug information, 4 to 
iterate through assembly lines and source code, and 1 to generate
the html file).

We also used a few global variables funs, main_address, current_file,
and used_src_sets. To process and hold functions, the current file,
and used source lines to make our hyperlinks work. We also added our
main_address global to keep track of our first occurance of main to
give the link for the top of the file.

Limitations, bugs, special features:
It was possible to create the file in a more programatic way in the
sense that we could've used less lines to achieve the same functionality
in a better way. We would also like to
note that some of our code is based on the recurring patterns of data
that we observed from the assembly and debug information. So there could
be potential bugs in the output of the html with other test files. It works
for our two small test cases 
across all optimization levels, but if further patterns come out from 
more complicated test cases we cannot guarantee the best functionality 
of our program, while it will still work to a degree.

We tested our test files extensively, but we believe its possible there
could be more bugs due to the variable nature of all of the data that we 
are taking in. 

We formatted the code to change
the font to make the code line up in a more appropriate way and
set up hyperlinks for every possible subroutine which means for every jump
and callq statement and linked them to the appropriate address number.
When dealing with comments in the assembly code, we added a new line 
and we also added a white space in the source lines to make up for the extra 
line in  assembly. We also did not account for the space of the 
computer's screen, so our lines will overlap if the screen is too narrow or
a line is too long.


Some more potential problems:
During our testing of optimized programs, sometimes our source lines would
not line up with the address lines in the way it normally does. This happens
because the assembly addresses become the same for some lines and our functionality
to combine lines with comments forces the source lines up. We believe this cases
is technically correct as we are supposed to build our program in an 
"assembly" centric way which means that following the assembly addresses, we
end up with source lines that look strange intuitively.

When we gray out the extra contiguous lines of source code, there is a small possibility
of mismatch of access since we only checked that the source lines were grayed out, but
if the source line was close enough to other source lines they would grayed out
unintentionally.


Output:
The example output html files for our test cases are located in their respective folders.
All compiled with -g3 and -O0 flags.
parse.html is in parser
hello.html is in test1
opt.html is in test2

